"""
evaluate.py
-----------
Evaluation script for the "AI-Powered Visual Defect Detection" project.

Loads the trained ResNet18 model (saved by train.py) and evaluates it on
the held-out test dataset. Produces:
    - Accuracy, precision, recall, F1-score
    - A confusion matrix (saved as an image)
    - A full classification report (printed to console + saved as text)
    - A grid of sample correctly/incorrectly classified images with
      predicted labels and confidence scores (saved as an image)

Expected dataset layout (relative to project root):
    dataset/test/good/
    dataset/test/defective/

Expected trained weights:
    models/defect_model.pth

This script does NOT modify train.py and does NOT create any backend or
frontend code. It only reads the existing model + test data and writes
evaluation artifacts (images/text) into a "results" folder.

Run this file from the project root:
    python ml/evaluate.py
"""

import os
import random

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    ConfusionMatrixDisplay,
    classification_report,
)


# ----------------------------------------------------------------------------
# 1. REPRODUCIBILITY
# ----------------------------------------------------------------------------
# Same seed as train.py so image sampling / shuffling behaves consistently.
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)


# ----------------------------------------------------------------------------
# 2. PATH SETUP
# ----------------------------------------------------------------------------
# This script lives in <project_root>/ml/evaluate.py, so the project root is
# one directory up. This makes the script work regardless of the current
# working directory it's launched from.
THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_FILE_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "dataset")
TEST_DIR = os.path.join(DATA_DIR, "test")

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "defect_model.pth")

# Folder where evaluation outputs (plots, reports) will be saved.
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

CONFUSION_MATRIX_PATH = os.path.join(RESULTS_DIR, "confusion_matrix.png")
CLASSIFICATION_REPORT_PATH = os.path.join(RESULTS_DIR, "classification_report.txt")
SAMPLE_PREDICTIONS_PATH = os.path.join(RESULTS_DIR, "sample_predictions.png")


# ----------------------------------------------------------------------------
# 3. CONFIG
# ----------------------------------------------------------------------------
IMAGE_SIZE = 224
BATCH_SIZE = 32
NUM_WORKERS = 2
NUM_SAMPLE_IMAGES = 8  # How many correct + incorrect predictions to visualize.

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


# ----------------------------------------------------------------------------
# 4. DEVICE SETUP
# ----------------------------------------------------------------------------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")


# ----------------------------------------------------------------------------
# 5. DATA TRANSFORMS
# ----------------------------------------------------------------------------
# No augmentation for evaluation -- we want a deterministic, fair measure
# of real model performance. Only resize + normalize (same as validation
# in train.py).
test_transforms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])


# ----------------------------------------------------------------------------
# 6. DATASET & DATALOADER
# ----------------------------------------------------------------------------
def build_test_loader():
    """
    Builds the test DataLoader using ImageFolder, which expects the
    good/ and defective/ subfolder structure.
    """
    if not os.path.isdir(TEST_DIR):
        raise FileNotFoundError(
            f"Test data not found at: {TEST_DIR}\n"
            "Expected structure: dataset/test/good/, dataset/test/defective/"
        )

    test_dataset = datasets.ImageFolder(TEST_DIR, transform=test_transforms)

    test_loader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
    )

    return test_loader, test_dataset


# ----------------------------------------------------------------------------
# 7. MODEL LOADING
# ----------------------------------------------------------------------------
def load_model():
    """
    Rebuilds the ResNet18 architecture (must match train.py exactly) and
    loads the saved trained weights into it.
    """
    if not os.path.isfile(MODEL_PATH):
        raise FileNotFoundError(
            f"Trained model not found at: {MODEL_PATH}\n"
            "Run ml/train.py first to produce models/defect_model.pth"
        )

    # Build the same architecture used in train.py: ResNet18 with the
    # final fully-connected layer replaced for 2 output classes.
    # We don't need ImageNet pretrained weights here since we are about
    # to overwrite them with our own trained weights.
    model = models.resnet18(weights=None)
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, 2)

    state_dict = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(state_dict)

    model = model.to(device)
    model.eval()  # Set to evaluation mode (disables dropout/batchnorm updates).

    return model


# ----------------------------------------------------------------------------
# 8. RUN INFERENCE ON THE TEST SET
# ----------------------------------------------------------------------------
def run_inference(model, test_loader):
    """
    Runs the model on the entire test set and collects:
        - true labels
        - predicted labels
        - predicted confidence (softmax probability of the predicted class)
        - the raw image tensors (for later visualization)
    """
    all_labels = []
    all_preds = []
    all_confidences = []
    all_images = []

    softmax = nn.Softmax(dim=1)

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.to(device)

            outputs = model(inputs)
            probs = softmax(outputs)

            confidences, preds = torch.max(probs, dim=1)

            all_labels.extend(labels.numpy())
            all_preds.extend(preds.cpu().numpy())
            all_confidences.extend(confidences.cpu().numpy())

            # Keep images on CPU for plotting later.
            all_images.extend(inputs.cpu())

    return all_labels, all_preds, all_confidences, all_images


# ----------------------------------------------------------------------------
# 9. METRICS
# ----------------------------------------------------------------------------
def compute_and_print_metrics(all_labels, all_preds, class_names):
    """
    Computes accuracy, precision, recall, F1-score and prints/saves a full
    classification report. 'defective' is treated as the positive class
    (index 0, since ImageFolder sorts class names alphabetically:
    defective=0, good=1).
    """
    accuracy = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average="binary", pos_label=0, zero_division=0
    )

    print("\n" + "=" * 60)
    print("TEST SET METRICS")
    print("=" * 60)
    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}  (positive class = 'defective')")
    print(f"Recall   : {recall:.4f}  (positive class = 'defective')")
    print(f"F1-score : {f1:.4f}  (positive class = 'defective')")

    # Full per-class classification report from scikit-learn.
    report = classification_report(all_labels, all_preds, target_names=class_names)
    print("\nClassification Report:")
    print(report)

    # Save the report to a text file for later reference.
    with open(CLASSIFICATION_REPORT_PATH, "w") as f:
        f.write("TEST SET METRICS\n")
        f.write("=" * 60 + "\n")
        f.write(f"Accuracy : {accuracy:.4f}\n")
        f.write(f"Precision: {precision:.4f}\n")
        f.write(f"Recall   : {recall:.4f}\n")
        f.write(f"F1-score : {f1:.4f}\n\n")
        f.write("Classification Report:\n")
        f.write(report)

    print(f"\nSaved classification report to: {CLASSIFICATION_REPORT_PATH}")

    return accuracy, precision, recall, f1


# ----------------------------------------------------------------------------
# 10. CONFUSION MATRIX
# ----------------------------------------------------------------------------
def plot_confusion_matrix(all_labels, all_preds, class_names):
    """
    Computes and saves a confusion matrix image.
    Class indices come from ImageFolder's alphabetical ordering:
        0 = defective, 1 = good
    """
    cm = confusion_matrix(all_labels, all_preds, labels=[0, 1])

    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    fig, ax = plt.subplots(figsize=(6, 6))
    disp.plot(cmap="Blues", ax=ax, colorbar=True)
    ax.set_title("Confusion Matrix - Test Set")

    fig.tight_layout()
    fig.savefig(CONFUSION_MATRIX_PATH)
    plt.close(fig)

    print(f"Saved confusion matrix to: {CONFUSION_MATRIX_PATH}")


# ----------------------------------------------------------------------------
# 11. VISUALIZE SAMPLE PREDICTIONS (correct + incorrect)
# ----------------------------------------------------------------------------
def unnormalize_image(tensor_image):
    """
    Reverses ImageNet normalization so images display with natural colors
    instead of the shifted/scaled values used for model input.
    """
    mean = torch.tensor(IMAGENET_MEAN).view(3, 1, 1)
    std = torch.tensor(IMAGENET_STD).view(3, 1, 1)
    image = tensor_image * std + mean
    image = torch.clamp(image, 0, 1)
    # Convert from (C, H, W) to (H, W, C) for matplotlib.
    return image.permute(1, 2, 0).numpy()


def plot_sample_predictions(all_images, all_labels, all_preds, all_confidences, class_names):
    """
    Displays a grid of sample predictions: some correctly classified and
    some incorrectly classified, each labeled with the true class,
    predicted class, and the model's confidence score.
    """
    correct_indices = [i for i in range(len(all_preds)) if all_preds[i] == all_labels[i]]
    incorrect_indices = [i for i in range(len(all_preds)) if all_preds[i] != all_labels[i]]

    random.shuffle(correct_indices)
    random.shuffle(incorrect_indices)

    num_correct_to_show = min(NUM_SAMPLE_IMAGES // 2, len(correct_indices))
    num_incorrect_to_show = min(NUM_SAMPLE_IMAGES // 2, len(incorrect_indices))

    selected_indices = (
        correct_indices[:num_correct_to_show] + incorrect_indices[:num_incorrect_to_show]
    )

    if len(selected_indices) == 0:
        print("No images available to visualize predictions.")
        return

    num_images = len(selected_indices)
    cols = 4
    rows = (num_images + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 4 * rows))
    axes = np.array(axes).reshape(-1)  # Flatten in case of a single row.

    for ax_idx, sample_idx in enumerate(selected_indices):
        ax = axes[ax_idx]
        image = unnormalize_image(all_images[sample_idx])

        true_label = class_names[all_labels[sample_idx]]
        pred_label = class_names[all_preds[sample_idx]]
        confidence = all_confidences[sample_idx]
        is_correct = all_preds[sample_idx] == all_labels[sample_idx]

        ax.imshow(image)
        ax.axis("off")

        title_color = "green" if is_correct else "red"
        status = "CORRECT" if is_correct else "WRONG"
        ax.set_title(
            f"{status}\nTrue: {true_label} | Pred: {pred_label}\nConfidence: {confidence:.2%}",
            color=title_color,
            fontsize=10,
        )

    # Hide any unused subplot axes.
    for ax_idx in range(len(selected_indices), len(axes)):
        axes[ax_idx].axis("off")

    fig.suptitle("Sample Predictions (Correct and Incorrect)", fontsize=14)
    fig.tight_layout()
    fig.savefig(SAMPLE_PREDICTIONS_PATH)
    plt.close(fig)

    print(f"Saved sample predictions to: {SAMPLE_PREDICTIONS_PATH}")


# ----------------------------------------------------------------------------
# 12. MAIN EVALUATION ROUTINE
# ----------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("AI-Powered Visual Defect Detection - Evaluation")
    print("=" * 70)

    # --- Load test data ---
    test_loader, test_dataset = build_test_loader()

    # Class-index mapping is derived directly from the test dataset's
    # ImageFolder object, so it always matches what the model was trained
    # on IF the train/val/test folders use the same class names
    # ('defective', 'good'). ImageFolder sorts class names alphabetically,
    # so this will be {'defective': 0, 'good': 1} as long as folder names
    # match between train and test sets.
    class_to_idx = test_dataset.class_to_idx
    idx_to_class = {idx: name for name, idx in class_to_idx.items()}
    class_names = [idx_to_class[i] for i in range(len(idx_to_class))]

    print(f"Test samples: {len(test_dataset)}")
    print(f"Class mapping: {class_to_idx}\n")

    # --- Load trained model ---
    model = load_model()
    print(f"Loaded trained model from: {MODEL_PATH}\n")

    # --- Run inference ---
    all_labels, all_preds, all_confidences, all_images = run_inference(model, test_loader)

    # --- Metrics ---
    compute_and_print_metrics(all_labels, all_preds, class_names)

    # --- Confusion matrix ---
    plot_confusion_matrix(all_labels, all_preds, class_names)

    # --- Sample predictions ---
    plot_sample_predictions(all_images, all_labels, all_preds, all_confidences, class_names)

    print("\n" + "=" * 70)
    print("Evaluation complete. All results saved in the 'results/' folder.")
    print("=" * 70)


if __name__ == "__main__":
    main()
