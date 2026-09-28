"""Single place for features, file paths and model-quality thresholds."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "customers.csv"
MODELS_DIR = ROOT / "models"
MODEL_PATH = Path(os.getenv("MODEL_PATH", MODELS_DIR / "model.joblib"))
METRICS_PATH = MODELS_DIR / "metrics.json"
BASELINE_PATH = MODELS_DIR / "baseline_metrics.json"

NUMERIC_FEATURES = [
    "tenure_months",
    "monthly_charges",
    "support_tickets",
    "logins_last_30d",
    "late_payments",
]
CATEGORICAL_FEATURES = ["contract", "payment_method", "plan"]
TARGET = "churned"

CONTRACTS = ["month-to-month", "one-year", "two-year"]
PAYMENT_METHODS = ["card", "bank_transfer", "invoice"]
PLANS = ["basic", "standard", "premium"]

# ── Model-quality gate ────────────────────────────────────────────────────────
# A new model is only deployed if it clears the absolute bar AND is not
# meaningfully worse than the model currently in production (the baseline).
MIN_AUC = 0.80  # ranking quality: how well it separates churners from stayers
MIN_RECALL = 0.60  # share of real churners the model catches
MAX_AUC_DROP = 0.01  # allowed regression vs. the production baseline
