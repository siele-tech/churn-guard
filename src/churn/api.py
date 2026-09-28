"""HTTP API serving churn predictions.

uvicorn churn.api:app --reload
"""

import os
from contextlib import asynccontextmanager
from importlib import resources
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from churn.config import MODEL_PATH
from churn.features import top_factors

GIT_SHA = os.getenv("GIT_SHA", "local")[:7]
state: dict = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    path = os.getenv("MODEL_PATH", str(MODEL_PATH))
    state["bundle"] = joblib.load(path) if os.path.exists(path) else None
    yield
    state.clear()


app = FastAPI(
    title="Churn Guard",
    description="Predicts how likely a customer is to cancel, and why.",
    version="1.0.0",
    lifespan=lifespan,
)


class Customer(BaseModel):
    tenure_months: int = Field(ge=0, le=120, examples=[4])
    monthly_charges: float = Field(gt=0, le=1000, examples=[89.0])
    support_tickets: int = Field(ge=0, le=100, examples=[3])
    logins_last_30d: int = Field(ge=0, le=1000, examples=[2])
    late_payments: int = Field(ge=0, le=100, examples=[1])
    contract: Literal["month-to-month", "one-year", "two-year"]
    payment_method: Literal["card", "bank_transfer", "invoice"]
    plan: Literal["basic", "standard", "premium"]


class Prediction(BaseModel):
    churn_probability: float
    risk: Literal["low", "medium", "high"]
    top_factors: list[str]
    model_version: str


def risk_band(probability: float) -> Literal["low", "medium", "high"]:
    if probability < 0.3:
        return "low"
    if probability < 0.6:
        return "medium"
    return "high"


def _bundle() -> dict:
    bundle = state.get("bundle")
    if bundle is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return bundle


@app.get("/health")
def health() -> dict:
    bundle = state.get("bundle")
    return {
        "status": "ok" if bundle else "model_missing",
        "git_sha": GIT_SHA,
        "model_version": bundle["version"] if bundle else None,
        "model_auc": bundle["metrics"]["auc"] if bundle else None,
        "trained_at": bundle["trained_at"] if bundle else None,
    }


@app.post("/predict", response_model=Prediction)
def predict(customer: Customer) -> Prediction:
    bundle = _bundle()
    row = pd.DataFrame([customer.model_dump()])
    probability = float(bundle["model"].predict_proba(row)[0, 1])
    return Prediction(
        churn_probability=round(probability, 3),
        risk=risk_band(probability),
        top_factors=top_factors(bundle["model"], row),
        model_version=bundle["version"],
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> str:
    return resources.files("churn").joinpath("static/index.html").read_text(encoding="utf-8")
