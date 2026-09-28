import pytest

from churn.data import generate_customers
from churn.train import save, train


@pytest.fixture(scope="session")
def customers():
    return generate_customers(n=3000, seed=7)


@pytest.fixture(scope="session")
def trained(customers):
    return train(customers)


@pytest.fixture(scope="session")
def model_file(trained, tmp_path_factory):
    bundle, metrics = trained
    folder = tmp_path_factory.mktemp("models")
    save(bundle, metrics, folder / "model.joblib", folder / "metrics.json")
    return folder / "model.joblib"
