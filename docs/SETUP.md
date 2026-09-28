# One-time setup: GitHub + Render (~15 min)

## 1. Push to GitHub

Create an **empty public** repository on GitHub, then:

```bash
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

The first run does stages 1–3 and pushes the Docker image to GitHub Container Registry. **Stage 4 (deploy) fails on this run because Render isn't set up yet. That's expected.**

## 2. Make the image public

Render needs to pull the image without a password:

1. Open your GitHub profile → **Packages** → `churn-guard`.
2. **Package settings** (bottom right) → **Change visibility** → **Public**.

## 3. Create the Render service

1. Sign up at [render.com](https://render.com) (you can use your GitHub account).
2. **New → Web Service → Existing image.**
3. **Image URL:** `ghcr.io/<you>/churn-guard:latest` (lowercase).
4. **Name:** `churn-guard`, **Region:** closest to you, **Instance type:** Free.
5. Click **Deploy**. After a minute or two you get a URL like `https://churn-guard-xxxx.onrender.com`.

   The free tier sleeps after 15 minutes without traffic, so the first request after a pause takes about 50 seconds.

## 4. Connect GitHub Actions to Render

1. In the Render service: **Settings → Deploy Hook**, then copy the URL.
2. On GitHub: **Settings → Secrets and variables → Actions**.
   - **Secrets** tab → **New repository secret**: name `RENDER_DEPLOY_HOOK_URL`, value: the deploy hook URL.
   - **Variables** tab → **New repository variable**: name `PRODUCTION_URL`, value: your Render URL (e.g. `https://churn-guard-xxxx.onrender.com`, no trailing slash).
3. **Actions → CI/CD Pipeline → Run workflow.** All 5 stages should now go green.

## 5. Recommended

- **Protect `main`:** require pull requests and the **✅ All checks passed** status check.
- **Approval gate:** Settings → Environments → `production` → Required reviewers.
- **Turn off Render's auto-deploy** (Settings → Auto-Deploy → No), so only the pipeline deploys, and only after the gate passes.
