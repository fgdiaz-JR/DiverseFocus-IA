"""
Model training script for DiverseFocus-IA text simplification.

Fine-tunes a T5 model on the processed paired data using Hugging Face Transformers
and logs all parameters, metrics, and the trained model artifact to MLflow.
"""

import logging
import os

import mlflow
import mlflow.transformers
import pandas as pd
import torch
from datasets import Dataset, DatasetDict
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models", "checkpoint")

# Hyperparameters (can be overridden via environment variables)
BASE_MODEL = os.getenv("TRAIN_BASE_MODEL", "t5-small")
NUM_EPOCHS = int(os.getenv("TRAIN_NUM_EPOCHS", "3"))
BATCH_SIZE = int(os.getenv("TRAIN_BATCH_SIZE", "8"))
LEARNING_RATE = float(os.getenv("TRAIN_LEARNING_RATE", "5e-5"))
MAX_SOURCE_LENGTH = int(os.getenv("TRAIN_MAX_SOURCE_LENGTH", "512"))
MAX_TARGET_LENGTH = int(os.getenv("TRAIN_MAX_TARGET_LENGTH", "128"))
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT", "diversefocus-simplification")


def load_datasets() -> DatasetDict:
    train_df = pd.read_csv(os.path.join(PROCESSED_DIR, "train.csv"))
    val_df = pd.read_csv(os.path.join(PROCESSED_DIR, "val.csv"))
    return DatasetDict(
        {
            "train": Dataset.from_pandas(train_df),
            "validation": Dataset.from_pandas(val_df),
        }
    )


def preprocess_function(examples: dict, tokenizer: AutoTokenizer) -> dict:
    prefix = "simplify: "
    inputs = [prefix + text for text in examples["complex_text"]]
    model_inputs = tokenizer(
        inputs, max_length=MAX_SOURCE_LENGTH, truncation=True, padding=False
    )
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(
            examples["simple_text"],
            max_length=MAX_TARGET_LENGTH,
            truncation=True,
            padding=False,
        )
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


def main() -> None:
    os.makedirs(MODEL_DIR, exist_ok=True)

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT)

    logger.info("Loading base model: %s", BASE_MODEL)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)

    datasets = load_datasets()
    logger.info(
        "Dataset sizes → train: %d, val: %d",
        len(datasets["train"]),
        len(datasets["validation"]),
    )

    tokenized = datasets.map(
        lambda ex: preprocess_function(ex, tokenizer),
        batched=True,
        remove_columns=datasets["train"].column_names,
    )

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, padding=True)

    training_args = Seq2SeqTrainingArguments(
        output_dir=MODEL_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        weight_decay=0.01,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        predict_with_generate=True,
        logging_dir=os.path.join(MODEL_DIR, "logs"),
        logging_steps=10,
        fp16=torch.cuda.is_available(),
        report_to="none",  # We log to MLflow manually
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    with mlflow.start_run(run_name="train"):
        mlflow.log_params(
            {
                "base_model": BASE_MODEL,
                "num_epochs": NUM_EPOCHS,
                "batch_size": BATCH_SIZE,
                "learning_rate": LEARNING_RATE,
                "max_source_length": MAX_SOURCE_LENGTH,
                "max_target_length": MAX_TARGET_LENGTH,
                "train_samples": len(datasets["train"]),
                "val_samples": len(datasets["validation"]),
            }
        )

        logger.info("Starting training…")
        train_result = trainer.train()

        mlflow.log_metrics(
            {
                "train_loss": train_result.training_loss,
                "train_runtime_sec": train_result.metrics.get("train_runtime", 0),
            }
        )

        trainer.save_model(MODEL_DIR)
        tokenizer.save_pretrained(MODEL_DIR)

        mlflow.transformers.log_model(
            transformers_model={"model": model, "tokenizer": tokenizer},
            artifact_path="model",
            task="text2text-generation",
            registered_model_name="diversefocus-simplification",
        )

        logger.info("Model saved to %s and registered in MLflow.", MODEL_DIR)
        mlflow.log_artifact(os.path.join(MODEL_DIR, "config.json"), "model_artifacts")


if __name__ == "__main__":
    main()
