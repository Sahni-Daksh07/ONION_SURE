"""
Reproducible Defect Classifier Training Pipeline

Trains a calibrated classifier on data/splits/train.txt and evaluates on val.txt:
- Employs class-weighted loss to counter the 2.26:1 Bulb imbalance
- Saves versioned model weights and JSON provenance metadata
- Avoids fabricating labels: trains on ground-truth Healthy vs Unhealthy baseline
"""

import os
import sys
import json
import joblib
from pathlib import Path
from typing import List, Tuple, Dict, Any
from datetime import datetime, timezone
import numpy as np
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score

from .classifier import FeatureExtractor


def load_dataset_from_split(split_file: Path, max_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """Loads images from split text file and extracts optical feature vectors."""
    if not split_file.exists():
        raise FileNotFoundError(f"Split file '{split_file}' not found.")

    with open(split_file, "r", encoding="utf-8") as f:
        paths = [line.strip() for line in f if line.strip()]

    # Stratified subsample if max_samples is given
    healthy_paths = [p for p in paths if "Healthy" in p]
    unhealthy_paths = [p for p in paths if "Unhealthy" in p]

    n_per_class = max_samples // 2
    selected = healthy_paths[:n_per_class] + unhealthy_paths[:n_per_class]

    X_list = []
    y_list = []
    valid_paths = []

    for p in selected:
        img_path = Path(p)
        if not img_path.exists():
            continue
        try:
            with Image.open(img_path) as img:
                feats = FeatureExtractor.extract_features(img)
                X_list.append(feats)
                # Binary ground truth
                label = "HEALTHY" if "Healthy" in p else "UNHEALTHY"
                y_list.append(label)
                valid_paths.append(p)
        except Exception:
            continue

    return np.array(X_list, dtype=np.float32), np.array(y_list), valid_paths


def train_classifier(
    train_split: Path = Path("data/splits/train.txt"),
    val_split: Path = Path("data/splits/val.txt"),
    output_dir: Path = Path("ml/weights"),
    model_version: str = "classifier-v1.0.0",
    max_train_samples: int = 800,
    max_val_samples: int = 200,
) -> Dict[str, Any]:
    print("=" * 60)
    print("ONION_SURE — Defect Classifier Training Pipeline")
    print(f"Model Version: {model_version}")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    print(f"Loading training data from {train_split}...")
    X_train, y_train, train_paths = load_dataset_from_split(train_split, max_samples=max_train_samples)
    print(f"Loaded {len(X_train)} training feature vectors.")

    print(f"Loading validation data from {val_split}...")
    X_val, y_val, val_paths = load_dataset_from_split(val_split, max_samples=max_val_samples)
    print(f"Loaded {len(X_val)} validation feature vectors.")

    print("\nTraining class-weighted LogisticRegression classifier...")
    # LogisticRegression with balanced class weights provides well-calibrated probabilities
    clf = LogisticRegression(class_weight="balanced", max_iter=500, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate on validation set
    y_pred = clf.predict(X_val)
    acc = round(float(accuracy_score(y_val, y_pred)), 4)
    macro_f1 = round(float(f1_score(y_val, y_pred, average="macro")), 4)

    print(f"Validation Accuracy: {acc * 100:.2f}% | Macro F1: {macro_f1:.4f}")
    report_dict = classification_report(y_val, y_pred, output_dict=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    weights_path = output_dir / f"{model_version}.joblib"
    metadata_path = output_dir / f"{model_version}_metadata.json"

    # Save model weights
    joblib.dump(clf, weights_path)

    metadata = {
        "model_version": model_version,
        "model_type": "LogisticRegression (balanced class weights)",
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "training_samples": len(X_train),
        "validation_samples": len(X_val),
        "feature_dim": X_train.shape[1] if len(X_train) else 0,
        "classes": list(clf.classes_),
        "metrics": {
            "validation_accuracy": acc,
            "macro_f1": macro_f1,
            "detailed_report": report_dict,
        },
        "weights_file": str(weights_path.as_posix()),
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Model saved to: {weights_path}")
    print(f"Metadata saved to: {metadata_path}")
    return metadata


if __name__ == "__main__":
    train_classifier()
