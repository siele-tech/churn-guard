"""Model definition and per-prediction explanations."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from churn.config import CATEGORICAL_FEATURES, NUMERIC_FEATURES

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Plain-English phrasing for the factors that push churn risk UP.
REASONS = {
    "tenure_months": "short time as a customer",
    "monthly_charges": "high monthly bill",
    "support_tickets": "many support tickets",
    "logins_last_30d": "low recent activity",
    "late_payments": "late payments",
    "contract_month-to-month": "month-to-month contract",
    "contract_one-year": "one-year contract",
    "contract_two-year": "two-year contract",
    "payment_method_invoice": "pays by invoice",
    "payment_method_card": "pays by card",
    "payment_method_bank_transfer": "pays by bank transfer",
    "plan_basic": "basic plan",
    "plan_standard": "standard plan",
    "plan_premium": "premium plan",
}


def build_model() -> Pipeline:
    """Logistic regression: accurate enough and fully explainable."""
    prep = ColumnTransformer(
        [
            ("num", StandardScaler(), NUMERIC_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
        ],
        verbose_feature_names_out=False,
    )
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    return Pipeline([("prep", prep), ("clf", clf)])


def top_factors(model: Pipeline, customer: pd.DataFrame, n: int = 3) -> list[str]:
    """The features that increase this customer's churn risk the most."""
    prep, clf = model.named_steps["prep"], model.named_steps["clf"]
    values = prep.transform(customer[FEATURES])
    values = values.toarray() if hasattr(values, "toarray") else np.asarray(values)
    contributions = values[0] * clf.coef_[0]
    names = prep.get_feature_names_out()
    ranked = sorted(zip(contributions, names, strict=True), reverse=True)
    return [REASONS.get(name, name) for c, name in ranked[:n] if c > 0]
