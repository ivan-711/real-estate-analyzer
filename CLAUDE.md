# MidwestDealAnalyzer — Project Memory

## Stack
- Backend: FastAPI, Python 3.11+, async SQLAlchemy 2.0, PostgreSQL, Alembic
- Frontend: React 18 + TypeScript, Vite, Tailwind CSS
- Auth: Clerk (JWT via FastAPI dependency)
- External: RentCast API (property + market data)
- Deploy: Railway (backend), Vercel (frontend)

## Conventions
- async SQLAlchemy 2.0 with Mapped types (not legacy declarative)
- Pydantic v2 with ConfigDict(from_attributes=True)
- Decimal for ALL financial/market numbers (never float)
- `from __future__ import annotations` at top of every new Python file
- Type hints on every function signature
- Tests: pytest + httpx AsyncClient, mock all external APIs

## Project Structure
backend/
  app/
    main.py, database.py, config.py
    models/ — user.py, property.py, deal.py, chat.py
    schemas/ — user.py, deal.py, property.py, chat.py
    routers/ — auth.py, deals.py, properties.py, chat.py
    services/ — deal_calculator.py, risk_engine.py, chatbot.pgrations/ — rentcast.py (has get_market_stats, get_property_data)
    utils/ — financial.py
  alembic/ — migrations 0001-0003 (users, properties/deals, chat)
  tests/
frontend/src/
  pages/ — Landing, Dashboard, DealCalculator, DealResults, DealsList, Login, Register
  components/ui/ — CountUp, BlurText, SpotlightCard
  lib/ — api.ts

## DO NOT MODIFY (developer-owned)
- backend/app/services/deal_calculator.py
- backend/app/services/risk_engine.py
- backend/app/services/chatbot.py
- backend/app/utils/financial.py
- backend/app/integrations/rentcast.py (use existing methods, don't add/change)

## Key Patterns
- Router: see routers/deals.py for prefix, tags, dependencies, response_model
- Model: see models/deal.py for Base, Mapped, mapped_column, UUID, Numeric
- Schema: see schemas/deal.py for BaseModel, Decimal | None, ConfigDict
- Tests: see tests/test_api_deals.py for async fixtures, assertions
- Route order matters: static paths before parameterized (e.g. /summary before /{id})

## Current Sta-2 complete: 98 tests passing
- Phase 3 in progress: Slices 1-2 deployed (Dashboard, React Bits Wave 1)
- Next: Slice 3 (market data pipeline)
