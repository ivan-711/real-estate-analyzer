from __future__ import annotations

from app.config import settings
from app.integrations.rentcast import RentCastError
from app.routers import auth, deals, properties, risk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Initialize Sentry only when DSN looks valid.
if settings.sentry_dsn_backend and "://" in settings.sentry_dsn_backend:
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


@app.exception_handler(RentCastError)
async def handle_rentcast_error(request: Request, exc: RentCastError) -> JSONResponse:
    """Return standardized API error shape for RentCast integration failures."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_code": exc.error_code,
        },
    )


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(properties.router)
app.include_router(deals.router)
app.include_router(risk.router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {"message": "MidwestDealAnalyzer API", "version": "0.1.0"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
