"""
Model evaluation script for DiverseFocus-IA text simplification.

Loads the trained model, runs BLEU and ROUGE evaluation on the test set,
and logs all metrics to MLflow.
"""

import json
import logging
import os

import mlflow
import mlflow.transformers
import pandas as pd
import sacrebleu
from datasets import Dataset
from evaluate import load as load_metric
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "checkpoint")
METRICS_DIR = os.path.join(os.path.dirname(__file__), "..", "metrics")

EVAL_BATCH_SIZE = int(os.getenv("EVALUATE_BATCH_SIZE", "8"))
MAX_TARGET_LENGTH = int(os.getenv("TRAIN_MAX_TARGET_LENGTH", "128"))
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT", "diversefocus-simplification")


def generate_predictions(
    pipe: pipeline, texts: list[str], batch_size: int = 8
) -> list[str]:
    """Run generation in batches and return decoded strings."""
    prefixed = [f"simplify: {t}" for t in texts]
    results = pipe(
        prefixed,
        batch_size=batch_size,
        max_length=MAX_TARGET_LENGTH,
        truncation=True,
    )
    return [r[0]["generated_text"] for r in results]


def compute_bleu(predictions: list[str], references: list[str]) -> float:
    """Compute corpus-level BLEU score using sacrebleu."""
    result = sacrebleu.corpus_bleu(predictions, [references])
    return result.score


def compute_rouge(predictions: list[str], references: list[str]) -> dict[str, float]:
    """Compute ROUGE-1, ROUGE-2, ROUGE-L scores."""
    rouge = load_metric("rouge")
    scores = rouge.compute(predictions=predictions, references=references)
    return {k: round(float(v), 4) for k, v in scores.items()}


def main() -> None:
    os.makedirs(METRICS_DIR, exist_ok=True)

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    logger.info("Loading model from %s", MODEL_DIR)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR)

    simplify_pipe = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        device=-1,  # CPU; change to 0 for GPU
    )

    test_df = pd.read_csv(os.path.join(PROCESSED_DIR, "test.csv"))
    logger.info("Evaluating on %d test samples.", len(test_df))

    complex_texts = test_df["complex_text"].tolist()
    reference_texts = test_df["simple_text"].tolist()

    predictions = generate_predictions(simplify_pipe, complex_texts, EVAL_BATCH_SIZE)

    bleu_score = compute_bleu(predictions, reference_texts)
    rouge_scores = compute_rouge(predictions, reference_texts)

    metrics = {
        "bleu": round(bleu_score, 4),
        **rouge_scores,
        "num_test_samples": len(test_df),
    }

    logger.info("Evaluation metrics: %s", metrics)

    metrics_path = os.path.join(METRICS_DIR, "scores.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    with mlflow.start_run(run_name="evaluate"):
        mlflow.log_params(
            {
                "eval_batch_size": EVAL_BATCH_SIZE,
                "num_test_samples": len(test_df),
            }
        )
        mlflow.log_metrics(metrics)
        mlflow.log_artifact(metrics_path, "evaluation")

    logger.info("Metrics saved to %s and logged to MLflow.", metrics_path)


if __name__ == "__main__":
    main()
