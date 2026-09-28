## What changed

<!-- One or two sentences. -->

## Type

- [ ] Model (features, algorithm, training data)
- [ ] API
- [ ] CI/CD / Docker

## Checklist

- [ ] Pipeline is green (tests, model-quality gate, container test)
- [ ] Reviewed the model report comment below (metrics vs. production)
- [ ] If the model improved on purpose: ran `python -m churn.gate --update-baseline` and committed `models/baseline_metrics.json`
