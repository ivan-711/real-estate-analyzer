from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# Initialize Sentry if DSN is provided
if settings.sentry_dsn_backend:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn_backend,
        environment=settings.environment,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=1.0 if settings.is_development else 0.1,
    )

# Create FastAPI app
app = FastAPI(
    title="MidwestDealAnalyzer API",
    description="Real estate investment analysis platform for Midwest markets",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router registration will be added here as routers are created
# Example:
# from app.routers import auth, deals, properties
# app.include_router(auth.router)
# app.include_router(deals.router)
# app.include_router(properties.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "MidwestDealAnalyzer API", "version": "0.1.0"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
