"""
main.py
-------
FastAPI backend for the "AI-Powered Visual Defect Detection" project.

This is the API layer that ties together:
    - backend/inference.py  -> predict_image(image), model loaded once
    - backend/history.py    -> save_prediction(...) / get_all_predictions()

Endpoints:
    GET  /health   -> backend + model status
    POST /predict  -> upload an image, get a defect prediction
    GET  /history  -> list previous predictions, newest first

Uploaded images are saved to:
    uploads/
Prediction history is stored (by history.py) in:
    data/predictions.csv

Run with (from the project root):
    uvicorn backend.main:app --reload

See the bottom of this file's accompanying explanation for the exact
command and options.
"""

import os
import uuid
import traceback

from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image, UnidentifiedImageError
import io

# Import our existing, already-built modules.
# NOTE: importing backend.inference triggers the model to load ONCE,
# at import time (see inference.py) -- not on every request.
from inference import predict_image
from history import save_prediction, get_all_predictions


# ----------------------------------------------------------------------------
# 1. PATH SETUP
# ----------------------------------------------------------------------------
# This file lives in <project_root>/backend/main.py, so the project root is
# one directory up. Resolving paths this way means the app works correctly
# no matter what directory it's launched from.
THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_FILE_DIR)

UPLOADS_DIR = os.path.join(PROJECT_ROOT, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


# ----------------------------------------------------------------------------
# 2. CONFIG
# ----------------------------------------------------------------------------
# Only JPEG and PNG images are accepted, as required by the project spec.
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# Maximum upload size (10 MB) -- a sensible guard against huge/broken files.
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Local React development frontend origins allowed to call this API.
# Add/adjust ports here if your frontend runs somewhere else.
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",   # Vite's default dev server port.
    "http://127.0.0.1:5173",
]


# ----------------------------------------------------------------------------
# 3. FASTAPI APP SETUP
# ----------------------------------------------------------------------------
app = FastAPI(
    title="AI-Powered Visual Defect Detection API",
    description="Backend API for classifying manufacturing images as good or defective.",
    version="1.0.0",
)

# Allow the local React dev frontend to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------------
# 4. STARTUP FLAG
# ----------------------------------------------------------------------------
# Since importing backend.inference already loads the model at import time
# (see inference.py), by the time this module finishes importing, the model
# is guaranteed to be ready. We track that here for the /health endpoint.
MODEL_READY = True


# ----------------------------------------------------------------------------
# 5. HELPER FUNCTIONS
# ----------------------------------------------------------------------------
def _get_file_extension(filename: str) -> str:
    """Returns the lowercase file extension, including the leading dot."""
    _, ext = os.path.splitext(filename)
    return ext.lower()


def _build_unique_filename(original_filename: str) -> str:
    """
    Builds a unique filename for a saved upload, preserving the original
    file extension so the saved file can still be opened correctly.
    Example: "part.jpg" -> "3f1b6c2a-....jpg"
    """
    extension = _get_file_extension(original_filename)
    return f"{uuid.uuid4()}{extension}"


# ----------------------------------------------------------------------------
# 6. GET /health
# ----------------------------------------------------------------------------
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """
    Simple health check endpoint. Reports whether the backend is running
    and whether the trained model was loaded successfully.
    """
    return {
        "status": "ok",
        "model_loaded": MODEL_READY,
    }


# ----------------------------------------------------------------------------
# 7. POST /predict
# ----------------------------------------------------------------------------
@app.post("/predict", status_code=status.HTTP_200_OK)
async def predict(file: UploadFile = File(...)):
    """
    Accepts a single image upload, validates it, runs it through the
    defect-detection model, saves the result to history, and returns
    the prediction.
    """
    # --- 1. Validate content type (fast check based on the upload header) ---
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file type: '{file.content_type}'. "
                "Only JPEG and PNG images are accepted."
            ),
        )

    # --- 2. Validate file extension as a second safety check ---
    extension = _get_file_extension(file.filename or "")
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported file extension: '{extension}'. "
                "Only .jpg, .jpeg, and .png files are accepted."
            ),
        )

    # --- 3. Read file bytes and validate size ---
    file_bytes = await file.read()

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file is too large. Maximum allowed size is 10 MB.",
        )

    # --- 4. Validate that the bytes are actually a readable image ---
    # We open from an in-memory buffer first, purely to validate the image
    # content (catches corrupted files, non-image files renamed with a
    # .jpg extension, etc.) before we save anything to disk.
    try:
        image = Image.open(io.BytesIO(file_bytes))
        image.verify()  # Checks the image is not corrupted (does not decode it).
    except (UnidentifiedImageError, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is not a valid image.",
        )

    # --- 5. Save the uploaded image with a unique filename ---
    unique_filename = _build_unique_filename(file.filename or "upload")
    saved_path = os.path.join(UPLOADS_DIR, unique_filename)

    try:
        with open(saved_path, "wb") as f:
            f.write(file_bytes)
    except OSError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {e}",
        )

    # --- 6. Re-open the saved image safely for inference ---
    # image.verify() above invalidates the image object for further use,
    # so we open a fresh copy here specifically for running the model.
    try:
        inference_image = Image.open(saved_path)
        inference_image.load()  # Fully load pixel data now, while we can catch errors.
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image could not be opened for processing.",
        )

    # --- 7. Run the model ---
    try:
        result = predict_image(inference_image)
    except Exception as e:
        # Catch-all for unexpected model/inference errors so the API never
        # crashes and always returns a clean, informative error response.
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model inference failed: {e}",
        )

    # --- 8. Save the prediction to history ---
    try:
        record = save_prediction(
            image_name=unique_filename,
            prediction=result["prediction"],
            confidence=result["confidence"],
            processing_time_ms=result["processing_time_ms"],
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save prediction history: {e}",
        )

    # --- 9. Return the saved record ---
    return {
        "id": record["id"],
        "image_name": record["image_name"],
        "prediction": record["prediction"],
        "confidence": record["confidence"],
        "processing_time_ms": record["processing_time_ms"],
        "timestamp": record["timestamp"],
    }


# ----------------------------------------------------------------------------
# 8. GET /history
# ----------------------------------------------------------------------------
@app.get("/history", status_code=status.HTTP_200_OK)
def history():
    """
    Returns all previous prediction records, newest first.
    """
    try:
        records = get_all_predictions()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read prediction history: {e}",
        )

    return {"count": len(records), "predictions": records}


# ----------------------------------------------------------------------------
# 9. GLOBAL EXCEPTION HANDLER (safety net)
# ----------------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    """
    Catches any exception that wasn't already handled above, so the API
    always returns a clean JSON error response instead of crashing or
    leaking a raw stack trace to the client.
    """
    traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected server error occurred."},
    )
