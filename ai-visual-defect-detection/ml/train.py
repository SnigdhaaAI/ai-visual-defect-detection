"""
train.py
--------
Training script for the "AI-Powered Visual Defect Detection" project.

Task:
    Binary image classification: "good" vs "defective" manufacturing parts.

Approach:
    Transfer learning using a pretrained ResNet18 (ImageNet weights), with the
    final fully-connected layer replaced to output 2 classes.

Expected dataset layout (relative to project root):
    dataset/train/good/
    dataset/train/defective/
    dataset/val/good/
    dataset/val/defective/

Output:
    models/defect_model.pth   -> best model (highest validation F1-score)

Run this file from the project root:
    python ml/train.py
"""

import os
import copy
import random
import time

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

from sklearn.metrics import precision_recall_fscore_support, accuracy_score


# ----------------------------------------------------------------------------
# 1. REPRODUCIBILITY
# ----------------------------------------------------------------------------
# Setting fixed seeds makes results (roughly) reproducible across runs.
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
torch.cuda.manual_seed_all(SEED)


# ----------------------------------------------------------------------------
# 2. PATH SETUP
# ----------------------------------------------------------------------------
# We resolve all paths relative to the project root, which is one directory
# above this script (this script lives in <project_root>/ml/train.py).
# This way the script works no matter what directory it's launched from,
# as long as it's run as "python ml/train.py" from the project root,
# or even "python train.py" from inside the ml/ folder.
THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_FILE_DIR)

DATA_DIR = os.path.join(PROJECT_ROOT, "dataset")
TRAIN_DIR = os.path.join(DATA_DIR, "train")
VAL_DIR = os.path.join(DATA_DIR, "val")

MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_SAVE_PATH = os.path.join(MODELS_DIR, "defect_model.pth")

# Make sure the models/ directory exists so torch.save() doesn't fail.
os.makedirs(MODELS_DIR, exist_ok=True)


# ----------------------------------------------------------------------------
# 3. HYPERPARAMETERS / CONFIG
# ----------------------------------------------------------------------------
IMAGE_SIZE = 224          # ResNet18 expects 224x224 input images.
BATCH_SIZE = 32
NUM_EPOCHS = 30
LEARNING_RATE = 1e-4
NUM_WORKERS = 2           # Set to 0 if you run into DataLoader issues on Windows.
EARLY_STOPPING_PATIENCE = 5  # Stop if val F1 doesn't improve for this many epochs.

# ImageNet normalization stats (required because we use ImageNet-pretrained weights).
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
# Training transforms include realistic augmentations for manufacturing/
# industrial images:
#   - Small rotations & flips: parts can be photographed at slightly
#     different orientations on a production line.
#   - Slight brightness/contrast jitter: lighting conditions vary between
#     inspection stations / cameras.
#   - Small translation/scale jitter: parts aren't always perfectly centered.
# We avoid overly aggressive augmentation (e.g. heavy color distortion)
# since defects can be subtle and we don't want to wash them out or
# fabricate fake ones.
train_transforms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomVerticalFlip(p=0.2),
    transforms.RandomRotation(degrees=10),
    transforms.RandomAffine(degrees=0, translate=(0.05, 0.05), scale=(0.95, 1.05)),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])

# Validation transforms should be deterministic (no random augmentation)
# so we get a stable, fair measure of model performance.
val_transforms = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])


# ----------------------------------------------------------------------------
# 6. DATASETS & DATALOADERS
# ----------------------------------------------------------------------------
def build_dataloaders():
    """
    Builds train/val datasets using ImageFolder (expects the
    good/ and defective/ subfolder structure) and wraps them in DataLoaders.
    """
    if not os.path.isdir(TRAIN_DIR):
        raise FileNotFoundError(
            f"Training data not found at: {TRAIN_DIR}\n"
            "Expected structure: dataset/train/good/, dataset/train/defective/"
        )
    if not os.path.isdir(VAL_DIR):
        raise FileNotFoundError(
            f"Validation data not found at: {VAL_DIR}\n"
            "Expected structure: dataset/val/good/, dataset/val/defective/"
        )

    train_dataset = datasets.ImageFolder(TRAIN_DIR, transform=train_transforms)
    val_dataset = datasets.ImageFolder(VAL_DIR, transform=val_transforms)

    # ImageFolder sorts class names alphabetically, so classes will be:
    # {'defective': 0, 'good': 1}
    print(f"Detected classes: {train_dataset.class_to_idx}")

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=NUM_WORKERS,
        pin_memory=torch.cuda.is_available(),
    )

    return train_loader, val_loader, train_dataset.class_to_idx


# ----------------------------------------------------------------------------
# 7. MODEL DEFINITION (Transfer Learning with ResNet18)
# ----------------------------------------------------------------------------
def build_model():
    """
    Loads a pretrained ResNet18 and replaces its final fully-connected
    layer with a new one that outputs 2 classes (good vs defective).
    """
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)

    # Replace the final classification layer.
    # ResNet18's original fc layer maps 512 -> 1000 (ImageNet classes).
    # We map 512 -> 2 (good, defective) instead.
    num_features = model.fc.in_features
    model.fc = nn.Linear(num_features, 2)

    model = model.to(device)
    return model


# ----------------------------------------------------------------------------
# 8. METRICS HELPER
# ----------------------------------------------------------------------------
def compute_metrics(all_labels, all_preds):
    """
    Computes accuracy, precision, recall, and F1-score.
    'defective' is treated as the positive class of interest (index 0,
    since ImageFolder sorts alphabetically: defective=0, good=1), but since
    this is binary classification we use 'binary' averaging on class 0.
    """
    accuracy = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average="binary", pos_label=0, zero_division=0
    )
    return accuracy, precision, recall, f1


# ----------------------------------------------------------------------------
# 9. TRAINING LOOP (single epoch)
# ----------------------------------------------------------------------------
def train_one_epoch(model, loader, criterion, optimizer):
    model.train()
    running_loss = 0.0

    for inputs, labels in loader:
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)

    epoch_loss = running_loss / len(loader.dataset)
    return epoch_loss


# ----------------------------------------------------------------------------
# 10. VALIDATION LOOP (single epoch)
# ----------------------------------------------------------------------------
def validate_one_epoch(model, loader, criterion):
    model.eval()
    running_loss = 0.0
    all_labels = []
    all_preds = []

    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)

            outputs = model(inputs)
            loss = criterion(outputs, labels)
            running_loss += loss.item() * inputs.size(0)

            preds = torch.argmax(outputs, dim=1)
            all_labels.extend(labels.cpu().numpy())
            all_preds.extend(preds.cpu().numpy())

    epoch_loss = running_loss / len(loader.dataset)
    accuracy, precision, recall, f1 = compute_metrics(all_labels, all_preds)

    return epoch_loss, accuracy, precision, recall, f1


# ----------------------------------------------------------------------------
# 11. MAIN TRAINING ROUTINE
# ----------------------------------------------------------------------------
def main():
    print("=" * 70)
    print("AI-Powered Visual Defect Detection - Training")
    print("=" * 70)

    # --- Load data ---
    train_loader, val_loader, class_to_idx = build_dataloaders()

    # --- Build model ---
    model = build_model()

    # --- Loss function & optimizer ---
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # Reduce learning rate when validation loss plateaus.
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=2
    )

    # --- Tracking best model (by validation F1-score) ---
    best_f1 = -1.0
    best_model_weights = copy.deepcopy(model.state_dict())
    epochs_without_improvement = 0

    print(f"\nTraining samples: {len(train_loader.dataset)}")
    print(f"Validation samples: {len(val_loader.dataset)}")
    print(f"Class mapping: {class_to_idx}\n")

    start_time = time.time()

    for epoch in range(1, NUM_EPOCHS + 1):
        epoch_start = time.time()

        train_loss = train_one_epoch(model, train_loader, criterion, optimizer)
        val_loss, val_acc, val_precision, val_recall, val_f1 = validate_one_epoch(
            model, val_loader, criterion
        )

        scheduler.step(val_loss)
        epoch_time = time.time() - epoch_start

        # --- Print clear epoch results ---
        print(
            f"Epoch [{epoch:02d}/{NUM_EPOCHS}] "
            f"({epoch_time:.1f}s) | "
            f"Train Loss: {train_loss:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Val Acc: {val_acc:.4f} | "
            f"Val Precision: {val_precision:.4f} | "
            f"Val Recall: {val_recall:.4f} | "
            f"Val F1: {val_f1:.4f}"
        )

        # --- Save best model & check early stopping ---
        if val_f1 > best_f1:
            best_f1 = val_f1
            best_model_weights = copy.deepcopy(model.state_dict())
            epochs_without_improvement = 0

            torch.save(best_model_weights, MODEL_SAVE_PATH)
            print(f"  -> New best model saved (Val F1: {best_f1:.4f}) to {MODEL_SAVE_PATH}")
        else:
            epochs_without_improvement += 1
            print(
                f"  -> No improvement for {epochs_without_improvement} "
                f"epoch(s) (best Val F1: {best_f1:.4f})"
            )

        if epochs_without_improvement >= EARLY_STOPPING_PATIENCE:
            print(
                f"\nEarly stopping triggered after {epoch} epochs "
                f"(no improvement for {EARLY_STOPPING_PATIENCE} consecutive epochs)."
            )
            break

    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"Training complete in {total_time / 60:.1f} minutes.")
    print(f"Best validation F1-score: {best_f1:.4f}")
    print(f"Best model saved to: {MODEL_SAVE_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    main()
