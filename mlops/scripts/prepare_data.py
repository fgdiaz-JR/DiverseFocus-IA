"""
Data preparation script for DiverseFocus-IA text simplification model.

Loads raw paired data (complex/simple text), cleans and splits into
train/validation/test sets, and saves to data/processed/.
"""

import logging
import os
import random

import pandas as pd
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "processed")

VAL_SPLIT = float(os.getenv("PREPARE_VAL_SPLIT", "0.1"))
TEST_SPLIT = float(os.getenv("PREPARE_TEST_SPLIT", "0.1"))
RANDOM_SEED = int(os.getenv("PREPARE_RANDOM_SEED", "42"))

random.seed(RANDOM_SEED)


def load_raw_data() -> pd.DataFrame:
    """Load all CSV files from data/raw/ and concatenate them."""
    frames: list[pd.DataFrame] = []

    csv_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".csv")]
    if not csv_files:
        logger.warning("No CSV files found in %s. Creating synthetic dataset.", RAW_DIR)
        return _create_synthetic_dataset()

    for fname in csv_files:
        path = os.path.join(RAW_DIR, fname)
        logger.info("Loading %s", path)
        df = pd.read_csv(path)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    logger.info("Loaded %d raw samples from %d file(s).", len(combined), len(frames))
    return combined


def _create_synthetic_dataset() -> pd.DataFrame:
    """
    Create a small synthetic paired dataset when no real data is available.
    In production, replace with a proper corpus (e.g., Newsela, ASSET, WikiLarge).
    """
    pairs = [
        (
            "The mitochondria is the organelle responsible for cellular respiration and ATP synthesis.",
            "Mitochondria make energy for cells. They turn food into power the cell can use.",
        ),
        (
            "Photosynthesis is the biological process by which chlorophyll-containing organisms "
            "convert light energy into chemical energy.",
            "Plants use sunlight to make their own food. This is called photosynthesis.",
        ),
        (
            "The legislative branch of government is responsible for enacting statutes and "
            "appropriating the funds necessary to operate the government.",
            "The legislature writes laws and decides how the government spends money.",
        ),
        (
            "Gravitational acceleration near Earth's surface is approximately 9.8 m/s², "
            "causing all objects to accelerate towards the Earth at the same rate in a vacuum.",
            "Gravity pulls everything toward Earth. Without air, all objects fall at the same speed.",
        ),
        (
            "Inflation is the rate at which the general level of prices for goods and services "
            "is rising, and consequently the purchasing power of currency is falling.",
            "Inflation means prices go up over time. When prices rise, money buys less.",
        ),
    ]
    return pd.DataFrame(pairs, columns=["complex_text", "simple_text"])


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and normalise the dataset."""
    required_cols = {"complex_text", "simple_text"}
    if not required_cols.issubset(df.columns):
        raise ValueError(
            f"Dataset must have columns {required_cols}. Got: {list(df.columns)}"
        )

    df = df.dropna(subset=["complex_text", "simple_text"])
    df["complex_text"] = df["complex_text"].str.strip()
    df["simple_text"] = df["simple_text"].str.strip()

    # Remove empty rows
    df = df[(df["complex_text"].str.len() > 10) & (df["simple_text"].str.len() > 10)]

    # Remove duplicates
    df = df.drop_duplicates(subset=["complex_text"])

    logger.info("After cleaning: %d samples.", len(df))
    return df.reset_index(drop=True)


def split_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split into train / validation / test sets."""
    train_val, test = train_test_split(
        df, test_size=TEST_SPLIT, random_state=RANDOM_SEED
    )
    adjusted_val_split = VAL_SPLIT / (1 - TEST_SPLIT)
    train, val = train_test_split(
        train_val, test_size=adjusted_val_split, random_state=RANDOM_SEED
    )
    logger.info(
        "Split → train: %d, val: %d, test: %d", len(train), len(val), len(test)
    )
    return train, val, test


def main() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    df = load_raw_data()
    df = clean_data(df)
    train, val, test = split_data(df)

    train.to_csv(os.path.join(PROCESSED_DIR, "train.csv"), index=False)
    val.to_csv(os.path.join(PROCESSED_DIR, "val.csv"), index=False)
    test.to_csv(os.path.join(PROCESSED_DIR, "test.csv"), index=False)

    logger.info("Processed data saved to %s", PROCESSED_DIR)


if __name__ == "__main__":
    main()
