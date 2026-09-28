import json

import pandas as pd

from churn.config import DATA_PATH, TARGET
from churn.data import generate_customers
from churn.features import FEATURES, top_factors


def test_data_is_deterministic():
    pd.testing.assert_frame_equal(generate_customers(200, seed=1), generate_customers(200, seed=1))


def test_data_has_expected_shape(customers):
    assert set(FEATURES + [TARGET, "customer_id"]) == set(customers.columns)
    assert customers["customer_id"].is_unique
    assert 0.15 < customers[TARGET].mean() < 0.5  # realistic churn rate


def test_committed_dataset_matches_generator():
    """data/customers.csv must be exactly what the generator produces (no manual edits)."""
    committed = pd.read_csv(DATA_PATH)
    pd.testing.assert_frame_equal(committed, generate_customers(), check_dtype=False)


def test_model_learns_the_signal(trained):
    _, metrics = trained
    assert metrics["auc"] > 0.78
    assert set(metrics) >= {"auc", "recall", "precision", "f1", "accuracy", "n_train", "n_test"}


def test_metrics_file_written(model_file):
    metrics = json.loads((model_file.parent / "metrics.json").read_text())
    assert metrics["n_train"] == 2400 and metrics["n_test"] == 600


def test_risky_customer_scores_higher_than_loyal(trained):
    model = trained[0]["model"]
    risky = pd.DataFrame(
        [
            dict(
                tenure_months=3,
                monthly_charges=95,
                support_tickets=4,
                logins_last_30d=1,
                late_payments=2,
                contract="month-to-month",
                payment_method="invoice",
                plan="premium",
            )
        ]
    )
    loyal = pd.DataFrame(
        [
            dict(
                tenure_months=60,
                monthly_charges=40,
                support_tickets=0,
                logins_last_30d=25,
                late_payments=0,
                contract="two-year",
                payment_method="card",
                plan="standard",
            )
        ]
    )
    assert model.predict_proba(risky)[0, 1] > 0.7
    assert model.predict_proba(loyal)[0, 1] < 0.2
    assert "month-to-month contract" in top_factors(model, risky)
