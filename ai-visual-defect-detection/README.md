# AI-Powered Visual Defect Detection

An end-to-end deep learning application that classifies manufacturing part
images as **good** or **defective**, built with a React frontend, a FastAPI
backend, and a PyTorch (ResNet18 transfer learning) model.

---

## Project Overview

Manual visual inspection on a production line is slow and inconsistent.
This project demonstrates how a computer vision model can automate that
first pass: an operator uploads a photo of a part through a web interface,
and the system returns an instant **good / defective** verdict along with
a confidence score, keeping a running inspection history for later review.

This is a portfolio project built to demonstrate practical, end-to-end
machine learning engineering: dataset preparation, model training and
evaluation, a production-style inference service, and a working frontend
— not just a notebook.

---

## Architecture

```
React + Vite + Tailwind CSS  (frontend)
        │  multipart/form-data image upload (HTTP)
        ▼
FastAPI backend (Python)
        │  loads model once at startup
        ▼
PyTorch ResNet18 (transfer learning) inference
        │
        ▼
CSV-based prediction history (data/predictions.csv)
```

No database server is used. Prediction history is stored in a simple CSV
file, which is enough for a single-station inspection demo and keeps the
project easy to run anywhere without extra infrastructure.

---

## Features

- Binary image classification: **good** vs **defective**
- Transfer learning on a pretrained ResNet18 backbone
- Drag-and-drop or browse-to-upload image submission
- Real-time inference through a FastAPI backend
- Live backend/model health indicator in the UI
- Confidence score and processing time shown per prediction
- Automatically-updating inspection history table (newest first)
- Automatic CUDA/CPU fallback — no configuration needed
- No external database — CSV-based history storage

---

## Dataset Information

The model expects images split into three sets, each containing two class
folders:

```
dataset/train/good/       dataset/val/good/       dataset/test/good/
dataset/train/defective/  dataset/val/defective/  dataset/test/defective/
```

`scripts/prepare_dataset.py` will build this structure automatically from a
raw, unsplit dataset laid out as:

```
dataset/raw/good/
dataset/raw/defective/
```

using a reproducible 70% / 15% / 15% train/val/test split (configurable).

> The raw/split dataset itself is not included in this repository/zip —
> only the code needed to prepare and consume it. See **Local Setup** below.

---

## Model Architecture

- **Backbone:** ResNet18, pretrained on ImageNet
- **Head:** final fully-connected layer replaced with `Linear(512, 2)` for
  2-class output (defective, good)
- **Input:** RGB images resized to 224×224
- **Normalization:** standard ImageNet mean/std
- **Class mapping** (fixed by alphabetical folder ordering via
  `torchvision.datasets.ImageFolder`, and mirrored explicitly in the
  inference code):
  - `0` → `defective`
  - `1` → `good`

---

## Training Process

`ml/train.py`:
- Loads `dataset/train/` and `dataset/val/` with `ImageFolder`
- Applies realistic augmentation for manufacturing imagery on the training
  set only (small rotations, flips, translation/scale jitter, mild
  brightness/contrast jitter) — validation data is left un-augmented
- Fine-tunes the pretrained ResNet18 with Adam, a `ReduceLROnPlateau`
  scheduler, and early stopping on validation F1-score
- Tracks loss, accuracy, precision, recall, and F1-score every epoch
- Saves only the **best** validation-F1 checkpoint to
  `models/defect_model.pth`
- Uses a fixed random seed (42) for reproducibility

---

## Test Results

Evaluated on a held-out `dataset/test/` split via `ml/evaluate.py`:

| Metric | Score |
|---|---|
| Accuracy | **99.36%** |
| Precision (defective) | **100%** |
| Recall (defective) | **98.89%** |
| F1-score | **99.44%** |

`ml/evaluate.py` also generates:
- `results/confusion_matrix.png`
- `results/classification_report.txt`
- `results/sample_predictions.png` (correctly and incorrectly classified examples with confidence scores)

---

## Folder Structure

```
ai-visual-defect-detection/
├── backend/
│   ├── inference.py       # Loads model once, exposes predict_image()
│   ├── history.py         # CSV-based prediction history read/write
│   ├── main.py            # FastAPI app: /health, /predict, /history
│   └── requirements.txt
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   ├── public/
│   └── src/
├── ml/
│   ├── train.py           # Model training
│   └── evaluate.py        # Test-set evaluation + reports/plots
├── scripts/
│   └── prepare_dataset.py # Splits raw images into train/val/test
├── models/                # defect_model.pth goes here (see Setup)
├── data/                  # predictions.csv is created here automatically
├── uploads/               # Uploaded inspection images are saved here
├── results/               # Evaluation reports/plots are written here
├── README.md
└── .gitignore
```

---

## Local Setup Instructions

### 1. Clone / unzip the project
Make sure you end up with `ai-visual-defect-detection/` as your project
root, containing `backend/`, `frontend/`, `ml/`, `scripts/`, etc.

### 2. Set up the Python environment
It's recommended to use a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

### 3. Install PyTorch (GPU/CUDA note — read before installing)
**If you already have a working CUDA-enabled PyTorch installation**
(e.g. PyTorch 2.11.0+cu128 on an NVIDIA GPU), **skip this step** — do not
reinstall or downgrade it. The commands below are only for a machine that
doesn't have PyTorch yet.

```bash
# Visit https://pytorch.org/get-started/locally/ and use the command
# generated for your OS + CUDA version, for example:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### 4. Install the remaining backend dependencies
```bash
pip install -r backend/requirements.txt
```
`backend/requirements.txt` does not pin a hard `torch`/`torchvision`
version — it only requires a minimum version, specifically so it won't
try to replace an existing CUDA installation.

### 5. Prepare the dataset (if starting from raw images)
```bash
python scripts/prepare_dataset.py
```

### 6. Train the model
```bash
python ml/train.py
```
This produces `models/defect_model.pth`.

### 7. Evaluate the model
```bash
python ml/evaluate.py
```
This produces the reports/plots in `results/`.

### 8. Install frontend dependencies
```bash
cd frontend
npm install
```

---

## GPU / CUDA Note

This project automatically detects and uses CUDA if available
(`torch.cuda.is_available()`), and falls back to CPU otherwise — in both
training (`ml/train.py`) and inference (`backend/inference.py`). No manual
configuration is required. Training and inference will simply run faster
on a CUDA-enabled GPU such as the RTX 4050 used during development.

---

## Backend Startup Command

From the project root:
```bash
uvicorn backend.main:app --reload
```
Runs at `http://localhost:8000`. Interactive API docs are available at
`http://localhost:8000/docs`.

---

## Frontend Startup Command

From the `frontend/` folder:
```bash
npm run dev
```
Runs at `http://localhost:5173` and expects the backend to be running at
`http://localhost:8000` (CORS is already configured for this origin).

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Returns backend status and whether the model is loaded |
| POST | `/predict` | Accepts one JPEG/PNG image upload, returns a prediction |
| GET | `/history` | Returns all previous predictions, newest first |

**`POST /predict` response shape:**
```json
{
  "id": "uuid",
  "image_name": "example.jpg",
  "prediction": "defective",
  "confidence": 94.8,
  "processing_time_ms": 87,
  "timestamp": "2026-07-10T12:34:56.789+00:00"
}
```

---

## Screenshots / Results

_Add screenshots of the running frontend here, for example:_
- Dashboard with a "good" result
- Dashboard with a "defective" result
- `results/confusion_matrix.png`
- `results/sample_predictions.png`

---

## Limitations

- Trained and evaluated on a specific manufacturing image dataset; may not
  generalize to visually different products or defect types without
  retraining.
- Class mapping (`defective=0`, `good=1`) depends on the training data's
  folder naming (`defective/`, `good/`) matching exactly — this is fixed
  and documented, not dynamically inferred at inference time.
- Prediction history is stored in a single CSV file with no locking, which
  is fine for a single-user local demo but not designed for concurrent
  multi-user production use.
- No authentication/authorization — not intended to be deployed publicly
  as-is.

---

## Future Improvements

- Add authentication for multi-user deployments
- Add defect localization (e.g. Grad-CAM heatmaps or bounding boxes), not
  just a binary verdict
- Support multi-class defect categorization instead of binary good/defective
- Add batch image upload and processing
- Add automated tests (unit tests for backend logic, end-to-end tests for
  the API)
- Containerize the app (Docker) for easier deployment
