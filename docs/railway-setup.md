# Railway deployment setup

This document describes how to configure Railway so the **backend** builds and runs correctly. The backend Dockerfile (`backend/Dockerfile`) is written to be built with the **repository root** as the Docker build context (equivalent to `docker build -f backend/Dockerfile .`). If Railway is set to use `backend` as the root directory, the build context is only the `backend/` folder and the build fails with `"/backend": not found` at `COPY backend/ /app/backend`.

## Option A: Repo root as build context (recommended)

Configure Railway so the image is built with the **repository root** as build context and `backend/Dockerfile` as the Dockerfile path. No changes to the Dockerfile are required.

### Where to find the settings

1. Open your [Railway project](https://railway.app/dashboard).
2. Click the **backend service** (the one that runs the FastAPI app).
3. Go to the **Settings** tab (or the deployment/build configuration section for your service).

Exact names may vary slightly by UI; look for **Root Directory**, **Dockerfile path** (or **Dockerfile Path**), and **Start Command**.

### Exact values to set

| Setting | Value | Why |
|--------|--------|-----|
| **Root Directory** | Leave **empty**, or set to **`/`** | So the Docker build context is the whole repo (e.g. `frontend/`, `backend/`, root files). If this is set to `backend`, only the `backend/` folder is used and paths like `COPY backend/ /app/backend` fail. |
| **Dockerfile path** | **`backend/Dockerfile`** | So Railway runs the equivalent of `docker build -f backend/Dockerfile <repo-root>`. Set via the build/Dockerfile path field, or via the **RAILWAY_DOCKERFILE_PATH** variable to `backend/Dockerfile`. |
| **Start command** | Leave as-is (optional) | The Dockerfile `CMD` already runs `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`. Only change this if something else is overriding the Dockerfile CMD and breaking the app. |

### After changing settings

1. **Trigger a new deploy** (e.g. from the Deployments tab or by pushing a commit) so the next build uses the new context and succeeds.
2. Confirm the build completes and the service starts; then check the health endpoint (e.g. `https://<your-railway-url>/api/v1/health`) returns JSON.

### Optional: config as code

A **`railway.toml`** at the repo root encodes:

- **Build:** use Dockerfile at `backend/Dockerfile` (builder `DOCKERFILE`).
- **Watch paths:** `backend/**` and `railway.toml` so only backend (or config) changes trigger a new deploy.

**Root Directory** cannot be set in this file; it must be set in the Railway dashboard (leave empty or `/` so the build context is the repo root). Configuration in code overrides dashboard build/deploy settings for each deployment. See the [Railway config reference](https://docs.railway.app/config-as-code/reference).

## Verify the build locally

From the **repository root**:

```bash
docker build -f backend/Dockerfile .
```

The build should complete with no step failing with `"/backend"` or `"backend/"` not found. If it fails, the Dockerfile or repo layout may not match the assumptions above (e.g. context must be repo root). (Run this from your machine; some CI/sandbox environments restrict Docker.)
