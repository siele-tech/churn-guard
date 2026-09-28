import pytest
from fastapi.testclient import TestClient

from churn.api import app, risk_band

RISKY = {
    "tenure_months": 3,
    "monthly_charges": 95,
    "support_tickets": 4,
    "logins_last_30d": 1,
    "late_payments": 2,
    "contract": "month-to-month",
    "payment_method": "invoice",
    "plan": "premium",
}


@pytest.fixture
def client(model_file, monkeypatch):
    monkeypatch.setenv("MODEL_PATH", str(model_file))
    with TestClient(app) as c:
        yield c


def test_health_reports_model(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["model_version"] == "local"
    assert body["model_auc"] > 0.78


def test_predict_risky_customer(client):
    res = client.post("/predict", json=RISKY)
    assert res.status_code == 200
    body = res.json()
    assert body["risk"] == "high"
    assert 0.6 <= body["churn_probability"] <= 1
    assert body["top_factors"]


def test_invalid_input_is_rejected(client):
    assert client.post("/predict", json={**RISKY, "contract": "lifetime"}).status_code == 422
    assert client.post("/predict", json={**RISKY, "tenure_months": -1}).status_code == 422


def test_home_page_is_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Churn <span>Guard</span>" in res.text


def test_missing_model_returns_503(tmp_path, monkeypatch):
    monkeypatch.setenv("MODEL_PATH", str(tmp_path / "nope.joblib"))
    with TestClient(app) as c:
        assert c.get("/health").json()["status"] == "model_missing"
        assert c.post("/predict", json=RISKY).status_code == 503


@pytest.mark.parametrize(
    ("p", "band"), [(0.1, "low"), (0.3, "medium"), (0.59, "medium"), (0.6, "high")]
)
def test_risk_bands(p, band):
    assert risk_band(p) == band
