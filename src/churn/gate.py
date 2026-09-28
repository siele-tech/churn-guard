"""Model-quality gate: a worse model never reaches production.

python -m churn.gate                    # check models/metrics.json
python -m churn.gate --update-baseline  # accept the new model as the new baseline
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from churn.config import BASELINE_PATH, MAX_AUC_DROP, METRICS_PATH, MIN_AUC, MIN_RECALL


def check(metrics: dict, baseline: dict | None) -> list[str]:
    """Return the reasons the model fails the gate (empty list = pass)."""
    failures = []
    if metrics["auc"] < MIN_AUC:
        failures.append(f"AUC {metrics['auc']:.3f} is below the minimum {MIN_AUC:.2f}")
    if metrics["recall"] < MIN_RECALL:
        failures.append(
            f"Recall {metrics['recall']:.3f} is below the minimum {MIN_RECALL:.2f} "
            "(too many churners would be missed)"
        )
    if baseline and metrics["auc"] < baseline["auc"] - MAX_AUC_DROP:
        failures.append(
            f"AUC dropped from {baseline['auc']:.3f} (production) to {metrics['auc']:.3f}, "
            f"more than the allowed {MAX_AUC_DROP:.2f}"
        )
    return failures


def report(metrics: dict, baseline: dict | None, failures: list[str]) -> str:
    """Markdown table comparing the new model with production."""
    rows = []
    for key in ("auc", "recall", "precision", "f1", "accuracy"):
        new = metrics[key]
        if baseline:
            delta = new - baseline[key]
            arrow = "🟢" if delta > 0.0005 else "🔴" if delta < -0.0005 else "⚪"
            rows.append(f"| {key} | {baseline[key]:.3f} | {new:.3f} | {arrow} {delta:+.3f} |")
        else:
            rows.append(f"| {key} | — | {new:.3f} | — |")
    status = "✅ Model-quality gate passed" if not failures else "❌ Model-quality gate failed"
    lines = [
        f"## {status}",
        "",
        "| Metric | Production | This change | Δ |",
        "|---|---|---|---|",
        *rows,
        "",
        f"Thresholds: AUC ≥ {MIN_AUC}, recall ≥ {MIN_RECALL}, "
        f"max AUC drop vs production {MAX_AUC_DROP}.",
    ]
    if failures:
        lines += ["", *[f"- ❌ {f}" for f in failures], "", "**Deployment blocked.**"]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Model-quality gate")
    parser.add_argument("--metrics", type=Path, default=METRICS_PATH)
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--report", type=Path, help="also write the markdown report here")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")  # emoji in the report on any console

    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    baseline = (
        json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline.exists() else None
    )
    failures = check(metrics, baseline)
    markdown = report(metrics, baseline, failures)
    print(markdown)
    if args.report:
        args.report.write_text(markdown + "\n", encoding="utf-8")

    if summary := os.getenv("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(markdown + "\n")
    for f in failures:
        print(f"::error title=Model-quality gate::{f}")

    if failures:
        return 1
    if args.update_baseline:
        shutil.copyfile(args.metrics, args.baseline)
        print(f"Baseline updated: {args.baseline}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
