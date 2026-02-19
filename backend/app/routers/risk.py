from __future__ import annotations

from typing import Any

from app.services.risk_engine import RiskEngine
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


@router.get("/factors")
async def list_risk_factors() -> dict[str, dict[str, Any]]:
    """Return risk factors and weights used by the scoring engine."""
    return RiskEngine.RISK_FACTORS
