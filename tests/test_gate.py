import json

import pytest

from churn.gate import check, main, report

GOOD = {"auc": 0.85, "recall": 0.75, "precision": 0.6, "f1": 0.67, "accuracy": 0.78}


def with_(**changes):
    return {**GOOD, **changes}


def test_good_model_passes():
    assert check(GOOD, baseline=GOOD) == []


def test_first_model_without_baseline_passes():
    assert check(GOOD, baseline=None) == []


@pytest.mark.parametrize(
    ("metrics", "expected"),
    [
        (with_(auc=0.70), "below the minimum 0.80"),
        (with_(recall=0.40), "too many churners would be missed"),
    ],
)
def test_absolute_thresholds(metrics, expected):
    assert any(expected in f for f in check(metrics, baseline=None))


def test_regression_against_production_is_blocked():
    failures = check(with_(auc=0.83), baseline=GOOD)  # 0.85 -> 0.83 = -0.02
    assert any("dropped from 0.850" in f for f in failures)


def test_tiny_regression_is_tolerated():
    assert check(with_(auc=0.845), baseline=GOOD) == []


def test_report_shows_deltas_and_blocks():
    md = report(with_(auc=0.83), GOOD, ["AUC dropped"])
    assert "| auc | 0.850 | 0.830 | 🔴 -0.020 |" in md
    assert "Deployment blocked" in md


def _write(tmp_path, metrics, baseline):
    (tmp_path / "m.json").write_text(json.dumps(metrics))
    (tmp_path / "b.json").write_text(json.dumps(baseline))
    return ["--metrics", str(tmp_path / "m.json"), "--baseline", str(tmp_path / "b.json")]


def test_cli_fails_and_writes_summary(tmp_path, monkeypatch, capsys):
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert main(_write(tmp_path, with_(auc=0.70), GOOD)) == 1
    assert "::error" in capsys.readouterr().out
    assert "gate failed" in summary.read_text(encoding="utf-8")


def test_cli_updates_baseline_only_when_passing(tmp_path):
    better = with_(auc=0.90)
    assert main([*_write(tmp_path, better, GOOD), "--update-baseline"]) == 0
    assert json.loads((tmp_path / "b.json").read_text())["auc"] == 0.90


def test_cli_writes_report_file(tmp_path):
    out = tmp_path / "report.md"
    assert main([*_write(tmp_path, GOOD, GOOD), "--report", str(out)]) == 0
    assert "gate passed" in out.read_text(encoding="utf-8")
