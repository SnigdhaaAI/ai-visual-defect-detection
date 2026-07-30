"""
prepare_dataset.py
-------------------
Dataset preparation script for the "AI-Powered Visual Defect Detection"
project.

Splits a raw collection of labeled images into the train/val/test folder
structure expected by ml/train.py and ml/evaluate.py:

    dataset/train/good/
    dataset/train/defective/
    dataset/val/good/
    dataset/val/defective/
    dataset/test/good/
    dataset/test/defective/

Expected RAW input layout (before running this script), by default:

    dataset/raw/good/
    dataset/raw/defective/

(e.g. the two class folders extracted directly from a Kaggle dataset zip)

Usage (from the project root):
    python scripts/prepare_dataset.py

Optional arguments:
    --raw-dir       Path to the raw dataset (default: dataset/raw)
    --output-dir    Path to write the split dataset (default: dataset)
    --train-ratio   Fraction of images used for training (default: 0.70)
    --val-ratio     Fraction of images used for validation (default: 0.15)
    (The remaining fraction is used for testing.)

This script only copies files -- it never deletes or modifies your raw
images, so it's safe to re-run.
"""

import argparse
import os
import random
import shutil

# Uses the same seed as ml/train.py and ml/evaluate.py so the resulting
# split is reproducible and consistent across the whole pipeline.
SEED = 42

CLASS_NAMES = ["good", "defective"]
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png"}


# ----------------------------------------------------------------------------
# PATH SETUP
# ----------------------------------------------------------------------------
# This file lives in <project_root>/scripts/prepare_dataset.py, so the
# project root is one directory up.
THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_FILE_DIR)

DEFAULT_RAW_DIR = os.path.join(PROJECT_ROOT, "dataset", "raw")
DEFAULT_OUTPUT_DIR = os.path.join(PROJECT_ROOT, "dataset")


def parse_args():
    parser = argparse.ArgumentParser(description="Split raw images into train/val/test folders.")
    parser.add_argument("--raw-dir", default=DEFAULT_RAW_DIR, help="Path to the raw dataset.")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Path to write the split dataset.")
    parser.add_argument("--train-ratio", type=float, default=0.70, help="Fraction used for training.")
    parser.add_argument("--val-ratio", type=float, default=0.15, help="Fraction used for validation.")
    return parser.parse_args()


def list_image_files(class_dir):
    """Returns a sorted list of valid image filenames in a class folder."""
    if not os.path.isdir(class_dir):
        return []

    files = [
        f for f in os.listdir(class_dir)
        if os.path.splitext(f)[1].lower() in VALID_EXTENSIONS
    ]
    files.sort()  # Sort first for determinism, before the seeded shuffle.
    return files


def split_files(files, train_ratio, val_ratio):
    """
    Shuffles (with a fixed seed) and splits a list of filenames into
    train/val/test according to the given ratios.
    """
    shuffled = files[:]
    random.Random(SEED).shuffle(shuffled)

    n_total = len(shuffled)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_files = shuffled[:n_train]
    val_files = shuffled[n_train:n_train + n_val]
    test_files = shuffled[n_train + n_val:]

    return train_files, val_files, test_files


def copy_files(files, source_dir, destination_dir):
    """Copies a list of files from source_dir into destination_dir."""
    os.makedirs(destination_dir, exist_ok=True)
    for filename in files:
        shutil.copy2(
            os.path.join(source_dir, filename),
            os.path.join(destination_dir, filename),
        )


def main():
    args = parse_args()

    if not os.path.isdir(args.raw_dir):
        raise FileNotFoundError(
            f"Raw dataset not found at: {args.raw_dir}\n"
            "Expected structure: dataset/raw/good/, dataset/raw/defective/"
        )

    if args.train_ratio + args.val_ratio >= 1.0:
        raise ValueError("train-ratio + val-ratio must be less than 1.0 (some data must remain for testing).")

    print("=" * 60)
    print("Dataset preparation - AI-Powered Visual Defect Detection")
    print("=" * 60)
    print(f"Raw dataset:  {args.raw_dir}")
    print(f"Output:       {args.output_dir}")
    print(f"Split ratios: train={args.train_ratio}, val={args.val_ratio}, "
          f"test={round(1 - args.train_ratio - args.val_ratio, 2)}\n")

    for class_name in CLASS_NAMES:
        class_raw_dir = os.path.join(args.raw_dir, class_name)
        files = list_image_files(class_raw_dir)

        if len(files) == 0:
            print(f"Warning: no images found for class '{class_name}' in {class_raw_dir}. Skipping.")
            continue

        train_files, val_files, test_files = split_files(files, args.train_ratio, args.val_ratio)

        copy_files(train_files, class_raw_dir, os.path.join(args.output_dir, "train", class_name))
        copy_files(val_files, class_raw_dir, os.path.join(args.output_dir, "val", class_name))
        copy_files(test_files, class_raw_dir, os.path.join(args.output_dir, "test", class_name))

        print(
            f"Class '{class_name}': {len(files)} total -> "
            f"{len(train_files)} train / {len(val_files)} val / {len(test_files)} test"
        )

    print("\nDone. Dataset split written to:", args.output_dir)


if __name__ == "__main__":
    main()
