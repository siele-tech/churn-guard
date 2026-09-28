# Showcase script (~15 min)

**Story:** *"Anyone can train a model. The hard part is making sure a worse one never replaces a good one in production. This pipeline enforces that automatically."*

**Screens:** the live app, GitHub **Actions**, your editor/terminal.

---

## 1. The product (2 min)

Open the live URL. Click **At-risk customer**: 97% churn risk, with the reasons "month-to-month contract, many support tickets, short time as a customer". Click **Loyal customer**: low risk.
Point at the footer: **model version, AUC and commit**. Every prediction is traceable to the pipeline run that produced it.

## 2. The pipeline (3 min)

Open the latest run on the **Actions** tab and walk through the graph:
tests → **train & gate** → **Docker build & test** → deploy → **smoke test**.
Open the run summary: the metrics table, the container test result, the pushed image tag, and the smoke test confirmation.

## 3. A bad model change is blocked ⭐ (5 min)

*"A teammate thinks the model is too complex and removes the contract feature."*

```bash
git switch -c simplify-model
```
In `src/churn/config.py`, change:
```python
CATEGORICAL_FEATURES = ["contract", "payment_method", "plan"]
```
to:
```python
CATEGORICAL_FEATURES = ["payment_method", "plan"]
```
```bash
git commit -am "refactor: simplify model features"
git push -u origin simplify-model
gh pr create --fill        # or open the PR on GitHub
```

- **2 · Train & model-quality gate** fails ❌.
- A bot comment appears on the PR:
  `auc | 0.824 | 0.744 | 🔴 -0.080` and **Deployment blocked**.
- Docker build, deploy and smoke test are all **skipped**, so production is untouched. Refresh the live app: same model version.

*"The pipeline caught a 10% accuracy regression that would have looked fine in a code review."*

Close the PR without merging.

## 4. A good change ships (3 min)

Change something harmless, e.g. the subtitle in `src/churn/static/index.html`, and merge it through a PR.
The gate passes (⚪ +0.000), the image is built, tested and pushed, Render deploys it, and the smoke test confirms the new commit is live. Refresh the page and point at the new commit in the footer.

## 5. Rollback (1 min)

Every image is tagged with its commit SHA, so rolling back means redeploying an older tag. Either:
- `git revert <sha> && git push`, and the pipeline redeploys the previous state, or
- in Render: **Deploys → pick an earlier deploy → Rollback**.

## Closing line

*"Code is tested, the model is tested against production, the container is tested before it's pushed, and the live API is tested after it's deployed. Four safety nets, and none of them needs a human to remember."*
