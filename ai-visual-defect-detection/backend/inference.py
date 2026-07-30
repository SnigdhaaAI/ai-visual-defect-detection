"""
inference.py
------------
Reusable inference module for the "AI-Powered Visual Defect Detection"
web application backend.

This module:
    - Loads the trained ResNet18 model ONCE when it is imported
      (not on every prediction request), which is essential for good
      performance in a web backend.
    - Exposes a single reusable function, predict_image(image), that takes
      a PIL image and returns the prediction, confidence, and processing
      time.

This file intentionally does NOT define any FastAPI routes/endpoints.
It is meant to be imported later by a FastAPI app, e.g.:

    from backend.inference import predict_image
    result = predict_image(pil_image)

Expected trained weights location (relative to project root):
    models/defect_model.pth
"""

import os
import time

import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image


# ----------------------------------------------------------------------------
# 1. PATH SETUP
# ----------------------------------------------------------------------------
# This file lives in <project_root>/backend/inference.py, so the project
# root is one directory up. Resolving paths this way means the module works
# correctly no matter what directory the backend server is launched from.
THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_FILE_DIR)

MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "defect_model.pth")


# ----------------------------------------------------------------------------
# 2. CONFIG
# ----------------------------------------------------------------------------
IMAGE_SIZE = 224

# ImageNet normalization stats -- must match training exactly, since the
# model was fine-tuned starting from ImageNet-pretrained weights.
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Class mapping used during training. torchvision's ImageFolder sorts class
# folder names alphabetically, so for folders named "defective" and "good"
# the mapping is: defective -> 0, good -> 1.
# This is defined explicitly here (rather than re-derived at request time)
# so that inference never silently depends on folder contents at runtime.
CLASS_NAMES = {0: "defective", 1: "good"}


# ----------------------------------------------------------------------------
# 3. DEVICE SETUP
# ----------------------------------------------------------------------------
# Automatically use CUDA if available, otherwise fall back to CPU.
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ----------------------------------------------------------------------------
# 4. PREPROCESSING TRANSFORM
# ----------------------------------------------------------------------------
# This must be IDENTICAL to the validation/test-time preprocessing used
# during training (no random augmentation at inference time).
inference_transforms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])


# ----------------------------------------------------------------------------
# 5. MODEL LOADING (runs once, at module import time)
# ----------------------------------------------------------------------------
def _build_model():
    """
    Rebuilds the ResNet18 architecture used during training (pretrained
    ImageNet backbone with the final layer replaced for 2 output classes),
    then loads the trained weights from disk.

    This is a private helper (leading underscore) -- it is only meant to be
    called once, below, when this module is first imported.
    """
    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(
            f"Trained model not found at: {MODEL_PATH}\n"
            "Make sure models/defect_model.pth exists (run ml/train.py first)."
        )

    # We don't need the pretrained ImageNet weights here since they will be
    # immediately overwritten by our own trained state_dict.
    model = models.resnet18(weights=None)
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, 2)

    state_dict = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(state_dict)

    model = model.to(device)
    model.eval()  # Inference mode: disables dropout, freezes batchnorm stats.

    return model


# The model is loaded exactly once, when this module is first imported,
# and then reused for every subsequent call to predict_image().
# This avoids the (expensive) cost of reloading the model from disk on
# every single prediction request.
_model = _build_model()
_softmax = nn.Softmax(dim=1)


# ----------------------------------------------------------------------------
# 6. PUBLIC INFERENCE FUNCTION
# ----------------------------------------------------------------------------
def predict_image(image: Image.Image) -> dict:
    """
    Runs the defect detection model on a single PIL image and returns the
    prediction result.

    Args:
        image (PIL.Image.Image): Input image, in any mode (RGB, RGBA,
            grayscale, etc.) and any size. It will be converted and
            resized internally to match the model's expected input.

    Returns:
        dict: {
            "prediction": str,            # "good" or "defective"
            "confidence": float,          # confidence percentage, e.g. 94.8
            "processing_time_ms": int,    # inference time in milliseconds
        }
    """
    start_time = time.perf_counter()

    # Ensure the image has exactly 3 color channels (RGB). Some uploaded
    # images may be grayscale, RGBA (with alpha channel), or CMYK, and the
    # model expects standard 3-channel RGB input.
    image = image.convert("RGB")

    # Apply the exact same preprocessing used during training's
    # validation/test phase: resize -> tensor -> ImageNet normalize.
    input_tensor = inference_transforms(image)

    # Add a batch dimension: model expects shape (batch_size, C, H, W).
    input_batch = input_tensor.unsqueeze(0).to(device)

    # Run inference without tracking gradients (faster, less memory).
    with torch.no_grad():
        outputs = _model(input_batch)
        probabilities = _softmax(outputs)

        # Get the predicted class index and its associated probability.
        confidence_tensor, predicted_idx_tensor = torch.max(probabilities, dim=1)

        predicted_idx = predicted_idx_tensor.item()
        confidence = confidence_tensor.item()

    # Safely map the predicted index to a human-readable class name.
    # Falls back to a clear "unknown" label rather than crashing if an
    # unexpected index is ever produced (defensive programming).
    prediction_label = CLASS_NAMES.get(predicted_idx, "unknown")

    processing_time_ms = (time.perf_counter() - start_time) * 1000

    return {
        "prediction": prediction_label,
        "confidence": round(confidence * 100, 1),
        "processing_time_ms": round(processing_time_ms),
    }
