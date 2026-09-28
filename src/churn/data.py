"""Realistic synthetic customer data for a subscription business."""

import numpy as np
import pandas as pd

from churn.config import CONTRACTS, DATA_PATH, PAYMENT_METHODS, PLANS

PLAN_PRICE = {"basic": 19.0, "standard": 49.0, "premium": 89.0}


def generate_customers(n: int = 6000, seed: int = 42) -> pd.DataFrame:
    """Customers whose churn depends on contract, tenure, usage and billing issues."""
    rng = np.random.default_rng(seed)

    contract = rng.choice(CONTRACTS, size=n, p=[0.55, 0.25, 0.20])
    max_tenure = np.select(
        [contract == "month-to-month", contract == "one-year"], [36, 60], default=72
    )
    tenure = np.maximum(1, (rng.random(n) * max_tenure).astype(int))
    plan = rng.choice(PLANS, size=n, p=[0.40, 0.40, 0.20])
    monthly = np.array([PLAN_PRICE[p] for p in plan]) + rng.normal(0, 6, n)
    payment = rng.choice(PAYMENT_METHODS, size=n, p=[0.50, 0.30, 0.20])
    tickets = rng.poisson(1.2, n)
    logins = rng.poisson(12, n)
    late = rng.poisson(0.4, n)

    logit = (
        -1.3
        + 1.5 * (contract == "month-to-month")
        - 1.1 * (contract == "two-year")
        - 0.035 * tenure
        + 0.012 * monthly
        + 0.40 * tickets
        - 0.07 * logins
        + 0.55 * late
        + 0.35 * (payment == "invoice")
    )
    churned = rng.random(n) < 1 / (1 + np.exp(-logit))

    return pd.DataFrame(
        {
            "customer_id": [f"CUST-{i:05d}" for i in range(1, n + 1)],
            "tenure_months": tenure,
            "monthly_charges": monthly.round(2),
            "support_tickets": tickets,
            "logins_last_30d": logins,
            "late_payments": late,
            "contract": contract,
            "payment_method": payment,
            "plan": plan,
            "churned": churned.astype(int),
        }
    )


def load_customers() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


if __name__ == "__main__":
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = generate_customers()
    df.to_csv(DATA_PATH, index=False, lineterminator="\n")
    print(f"wrote {len(df)} customers to {DATA_PATH} (churn rate {df['churned'].mean():.1%})")
