"""Train the churn model and record its metrics.

python -m churn.train
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from churn.config import METRICS_PATH, MODEL_PATH, TARGET
from churn.data import load_customers
from churn.features import FEATURES, build_model


def train(df: pd.DataFrame, seed: int = 42) -> tuple[dict, dict]:
    """Return (model bundle, metrics) trained on an 80/20 stratified split."""
    x_train, x_test, y_train, y_test = train_test_split(
        df[FEATURES], df[TARGET], test_size=0.2, random_state=seed, stratify=df[TARGET]
    )
    model = build_model().fit(x_train, y_train)

    proba = model.predict_proba(x_test)[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "auc": round(float(roc_auc_score(y_test, proba)), 4),
        "recall": round(float(recall_score(y_test, pred)), 4),
        "precision": round(float(precision_score(y_test, pred)), 4),
        "f1": round(float(f1_score(y_test, pred)), 4),
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "n_train": int(len(x_train)),
        "n_test": int(len(x_test)),
        "churn_rate": round(float(df[TARGET].mean()), 4),
    }
    bundle = {
        "model": model,
        "version": os.getenv("GITHUB_SHA", "local")[:7],
        "trained_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "metrics": metrics,
    }
    return bundle, metrics


def save(bundle: dict, metrics: dict, model_path: Path, metrics_path: Path) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    bundle, metrics = train(load_customers())
    save(bundle, metrics, MODEL_PATH, METRICS_PATH)
    print(f"Model trained: AUC {metrics['auc']:.3f}, recall {metrics['recall']:.3f}")
    print(f"Saved {MODEL_PATH} and {METRICS_PATH}")


if __name__ == "__main__":
    main()
