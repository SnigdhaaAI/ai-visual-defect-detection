"""
history.py
----------
Reusable prediction-history module for the "AI-Powered Visual Defect
Detection" web application backend.

This project does not use a database. Instead, prediction history is
stored persistently in a simple CSV file:

    data/predictions.csv

This module:
    - Automatically creates the data/ directory if it doesn't exist.
    - Automatically creates predictions.csv (with a header row) if it
      doesn't exist.
    - Exposes save_prediction(...) to append a new prediction record.
    - Exposes get_all_predictions() to read back all stored predictions,
      newest first.

This file intentionally does NOT define any FastAPI routes/endpoints.
It is meant to be imported later by a FastAPI app, e.g.:

    from backend.history import save_prediction, get_all_predictions

    save_prediction(
        image_name="part_042.jpg",
        prediction="defective",
        confidence=94.8,
        processing_time_ms=87,
    )

    history = get_all_predictions()
"""

import os
import csv
import uuid
from datetime import datetime, timezone


# ----------------------------------------------------------------------------
# 1. PATH SETUP
# ----------------------------------------------------------------------------
# This file lives in <project_root>/backend/history.py, so the project root
# is one directory up. Resolving paths this way means the module works
# correctly no matter what directory the backend server is launched from.
THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_FILE_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PREDICTIONS_CSV_PATH = os.path.join(DATA_DIR, "predictions.csv")


# ----------------------------------------------------------------------------
# 2. CSV SCHEMA
# ----------------------------------------------------------------------------
CSV_COLUMNS = [
    "id",
    "image_name",
    "prediction",
    "confidence",
    "processing_time_ms",
    "timestamp",
]


# ----------------------------------------------------------------------------
# 3. INITIALIZATION HELPERS
# ----------------------------------------------------------------------------
def _ensure_storage_ready() -> None:
    """
    Makes sure the data/ directory and predictions.csv file both exist.

    - Creates data/ if missing.
    - Creates predictions.csv with just the header row if missing.

    This is called automatically before every read/write operation, so
    callers never need to worry about first-time setup.
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.isfile(PREDICTIONS_CSV_PATH):
        with open(PREDICTIONS_CSV_PATH, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()


# ----------------------------------------------------------------------------
# 4. SAVE A NEW PREDICTION
# ----------------------------------------------------------------------------
def save_prediction(
    image_name: str,
    prediction: str,
    confidence: float,
    processing_time_ms: float,
) -> dict:
    """
    Appends a new prediction record to predictions.csv.

    Args:
        image_name (str): Name of the image that was classified
            (e.g. "part_042.jpg").
        prediction (str): Predicted class label ("good" or "defective").
        confidence (float): Confidence percentage (e.g. 94.8).
        processing_time_ms (float): Inference time in milliseconds.

    Returns:
        dict: The full record that was saved, including its generated
            "id" and "timestamp".
    """
    _ensure_storage_ready()

    record = {
        "id": str(uuid.uuid4()),
        "image_name": image_name,
        "prediction": prediction,
        "confidence": confidence,
        "processing_time_ms": processing_time_ms,
        # ISO 8601 timestamp in UTC, e.g. "2026-07-10T14:32:05.123456+00:00"
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    with open(PREDICTIONS_CSV_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(record)

    return record


# ----------------------------------------------------------------------------
# 5. READ ALL PREDICTIONS
# ----------------------------------------------------------------------------
def get_all_predictions() -> list:
    """
    Reads all stored predictions from predictions.csv.

    Returns:
        list[dict]: All prediction records, ordered newest first.
            Returns an empty list if the file is missing or empty
            (both are handled safely, not treated as errors).
    """
    _ensure_storage_ready()

    records = []

    with open(PREDICTIONS_CSV_PATH, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)

    # Newest first. Records are appended in chronological order, so
    # reversing the list is enough -- no need to re-parse timestamps.
    records.reverse()

    return records
