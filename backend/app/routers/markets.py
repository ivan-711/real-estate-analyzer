from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.market import MarketHistoryResponse, MarketSnapshotResponse
from app.services import market_comparator

router = APIRouter(prefix="/api/v1/markets", tags=["markets"])


@router.get("/compare", response_model=list[MarketSnapshotResponse])
async def compare_markets(
    zips: str = Query(..., description="Comma-separated zip codes, e.g. 53081,53202"),
    db: AsyncSession = Depends(get_db),
) -> list[MarketSnapshotResponse]:
    """Return the most recent market snapshot for each requested zip code.

    Requires 2–5 zip codes. Zips with no data are omitted from the response.
    """
    zip_list = [z.strip() for z in zips.split(",") if z.strip()]

    if len(zip_list) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 zip codes are required for comparison.",
        )
    if len(zip_list) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At most 5 zip codes are allowed per comparison.",
        )

    snapshots = await market_comparator.get_market_comparison(zip_list, db)
    return [MarketSnapshotResponse.model_validate(s) for s in snapshots]


@router.get("/{zip_code}", response_model=MarketSnapshotResponse)
async def get_market_snapshot(
    zip_code: str,
    db: AsyncSession = Depends(get_db),
) -> MarketSnapshotResponse:
    """Return the current market snapshot for a zip code.

    Performs a live RentCast lookup and persists the result. Falls back to the
    most recent DB row if RentCast is unavailable. Returns 404 when no data exists.
    """
    snapshot = await market_comparator.get_market_snapshot(zip_code, db)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No market data found for zip code {zip_code}",
        )
    return MarketSnapshotResponse.model_validate(snapshot)


@router.get("/{zip_code}/history", response_model=MarketHistoryResponse)
async def get_market_history(
    zip_code: str,
    db: AsyncSession = Depends(get_db),
) -> MarketHistoryResponse:
    """Return all historical market snapshots for a zip code, newest first.

    Returns 200 with an empty snapshots list when no history exists.
    """
    snapshots = await market_comparator.get_market_history(zip_code, db)
    return MarketHistoryResponse(
        zip_code=zip_code,
        snapshots=[MarketSnapshotResponse.model_validate(s) for s in snapshots],
    )
