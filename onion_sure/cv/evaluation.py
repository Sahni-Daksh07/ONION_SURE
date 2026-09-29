"""
Model Evaluation Pipeline on Frozen Test Set

Evaluates model on data/splits/test.txt and computes:
- Accuracy, Precision, Recall, F1-score (macro and weighted)
- Confusion Matrix
- Per-class performance breakdown
- Writes evaluation artifact to data/reports/model_evaluation_test_v1.0.0.json
"""

import sys
import json
import joblib
from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

from .training import load_dataset_from_split


def evaluate_model(
    model_path: Path = Path("ml/weights/classifier-v1.0.0.joblib"),
    test_split: Path = Path("data/splits/test.txt"),
    output_dir: Path = Path("data/reports"),
    max_test_samples: int = 400,
) -> Dict[str, Any]:
    print("=" * 60)
    print("ONION_SURE — Model Evaluation Pipeline (FROZEN TEST SET)")
    print(f"Model Path: {model_path}")
    print(f"Test Split: {test_split}")
    print(f"Timestamp:  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    if not model_path.exists():
        raise FileNotFoundError(f"Model file '{model_path}' not found. Run training.py first.")

    model = joblib.load(model_path)

    print(f"Loading test samples from {test_split}...")
    X_test, y_test, test_paths = load_dataset_from_split(test_split, max_samples=max_test_samples)
    print(f"Loaded {len(X_test)} test feature vectors.")

    y_pred = model.predict(X_test)

    acc = round(float(accuracy_score(y_test, y_pred)), 4)
    prec_macro = round(float(precision_score(y_test, y_pred, average="macro")), 4)
    rec_macro = round(float(recall_score(y_test, y_pred, average="macro")), 4)
    f1_mac = round(float(f1_score(y_test, y_pred, average="macro")), 4)

    classes = list(model.classes_)
    cm = confusion_matrix(y_test, y_pred, labels=classes).tolist()
    class_report = classification_report(y_test, y_pred, output_dict=True)

    print("\n" + "=" * 60)
    print("EVALUATION RESULTS:")
    print(f"Accuracy:     {acc * 100:.2f}%")
    print(f"Precision:    {prec_macro * 100:.2f}% (macro)")
    print(f"Recall:       {rec_macro * 100:.2f}% (macro)")
    print(f"Macro F1:     {f1_mac:.4f}")
    print(f"Classes:      {classes}")
    print(f"Confusion Matrix:\n{np.array(cm)}")
    print("=" * 60)

    evaluation_report = {
        "evaluation_name": "Test Set Model Evaluation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_file": str(model_path.as_posix()),
        "test_split_file": str(test_split.as_posix()),
        "total_test_samples_evaluated": len(X_test),
        "overall_metrics": {
            "accuracy": acc,
            "precision_macro": prec_macro,
            "recall_macro": rec_macro,
            "f1_macro": f1_mac,
        },
        "classes": classes,
        "confusion_matrix": cm,
        "per_class_breakdown": class_report,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "model_evaluation_test_v1.0.0.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(evaluation_report, f, indent=2)

    print(f"Report written to: {report_file}")
    return evaluation_report


if __name__ == "__main__":
    evaluate_model()
