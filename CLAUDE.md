# CLAUDE.md — Project Briefing for Claude Code

> **Read this file in full before every task.** Then read `ARCHITECTURE.md` for the complete system design, database schema, API endpoints, and directory structure. Then read `PRD.md` for the product specification, user flows, and design specs. These three documents are the single source of truth for this project.

---

## What This Project Is

This is **MidwestDealAnalyzer**, a real estate investment analysis platform focused on the Midwest United States (Wisconsin, Illinois, Michigan, Minnesota, Indiana, Ohio). It helps rental property investors evaluate deals by calculating financial metrics, scoring risk, comparing markets, and tracking portfolios — with a conversational AI assistant that can answer questions about the user's own deals and portfolio using direct context injection (deal data serialized into the LLM prompt, not RAG/pgvector).

The primary use case is analyzing duplexes and small multifamily rental properties in markets like Sheboygan, Milwaukee, Madison, and other Midwest cities. The developer (Ivan) is an active real estate investor evaluating properties in this region, so this is not a hypothetical project — the tool needs to produce financially accurate results that inform real purchase decisions.

**This is a portfolio project and a hiring argument.** It targets backend and full-stack software engineering roles. Code quality, test coverage, clean architecture, CI/CD, monitoring, and documentation matter as much as features. Every design decision should be defensible in a technical interview. A deployed, clickable URL matters more than a perfect codebase — get something live early and iterate.

**The core user journey:** Enter property address + purchase price → auto-fill details from APIs → get full deal analysis with 11-factor risk score → chat with AI about the deal → save to portfolio for comparison. A recruiter should be able to enter "123 Main St, Sheboygan WI" + "$185,000" and see a deal analysis in under 10 seconds.

---

## Tech Stack

**Backend:** Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, PostgreSQL 16, Redis (caching), httpx (async HTTP client for external APIs)

**Frontend:** React 18, Vite, Tailwind CSS, React Bits (reactbits.dev — animated UI components, TS-TW variant), Recharts or Chart.js, Axios

**AI/ML:** Anthropic Claude API (production chatbot via direct context injection), Ollama + Llama (local dev fallback)

**Infrastructure:** Docker Compose (local dev), Railway (backend + PostgreSQL deploy), Vercel (frontend deploy), GitHub Actions (CI/CD), Sentry (error tracking)

**Code Quality:** pre-commit hooks (Black, Prettier, isort, ruff), ESLint, pytest, Bugbot (automated PR review)

**Testing:** pytest, pytest-asyncio, httpx (TestClient), factory_boy (fixtures)

---

## Current Development Phase

> **UPDATE THIS SECTION** as phases are completed.

**Active Phase: Week 0 — PRD + Project Infrastructure**

Week 0 goals (before any application code):
- Write the PRD (product spec, user flows, wireframes, design specs)
- Create GitHub repo with README skeleton
- Run `claude /init` to generate CLAUDE.md, then customize with these conventions
- Set up pre-commit hooks: Black (Python), Prettier (React), isort, ruff
- Set up GitHub Actions: run pytest + frontend tests on push to main
- Set up Sentry accounts (free tier for FastAPI and React)
- Configure `.env.example` with all required environment variables
- Docker Compose for local dev (FastAPI + PostgreSQL + Redis)

Week 0 is complete when: the repo has CI/CD passing (trivially, no tests yet), pre-commit hooks enforcing formatting, Sentry configured, and the PRD is written and reviewed.

**Upcoming phases (do not build yet):**
- Phase 1 (Weeks 1–3): Deal Calculator + Risk Scoring + Minimal Frontend → DEPLOY
- Phase 2 (Weeks 4–6): AI Chatbot (direct context injection, no RAG)
- Phase 3 (Weeks 7–9): Market Comparisons + Dashboard + React Bits Animations
- Phase 4 (Weeks 10–12): Portfolio Tracking + Polish + Full Animation Rollout

---

## Ownership Boundaries

This is critical. The developer is writing certain modules by hand to deeply understand the business logic. Claude Code must not overwrite, rewrite, or replace these files without being explicitly asked.

**DEVELOPER-OWNED FILES (do not generate or overwrite):**
- `backend/app/services/deal_calculator.py` — The developer writes all financial calculation logic
- `backend/app/services/risk_engine.py` — The developer writes risk scoring logic
- `backend/app/services/chatbot.py` — The developer writes LLM prompt engineering and context injection logic
- `backend/app/utils/financial.py` — The developer writes mortgage math, IRR, amortization functions

**What Claude Code CAN do with developer-owned files:**
- Review them and suggest improvements when asked
- Write tests that exercise them (test_deal_calculator.py, test_risk_engine.py, etc.)
- Debug issues when the developer asks for help
- Add docstrings or type hints if the developer requests it

**CLAUDE CODE-OWNED FILES (generate, scaffold, and maintain freely):**
- All SQLAlchemy models in `backend/app/models/`
- All Pydantic schemas in `backend/app/schemas/`
- All FastAPI routers in `backend/app/routers/`
- Database configuration (`database.py`, `config.py`)
- Alembic migrations
- Authentication middleware (`middleware/auth.py`, `middleware/error_handler.py`)
- Docker Compose and Dockerfiles
- All test fixtures (`tests/conftest.py`)
- Frontend code (all of `frontend/`)
- Scripts (`scripts/`)
- CI/CD configuration (`.github/workflows/`, `.pre-commit-config.yaml`)
- `requirements.txt`, `package.json`, `.env.example`

**COLLABORATIVE FILES (Claude Code can scaffold, developer will customize):**
- `backend/app/integrations/rentcast.py` — Claude Code writes the initial client, developer refines error handling and normalization
- `backend/app/integrations/mashvisor.py` — Same pattern
- `backend/app/services/market_comparator.py` — Claude Code scaffolds, developer adds domain-specific comparison logic
- `backend/app/services/portfolio_tracker.py` — Claude Code scaffolds CRUD, developer adds actual-vs-projected analysis

---

## Code Conventions

### Python Style

Use Python 3.11+ features. Type hints on every function signature, every variable where the type is not obvious, and all Pydantic models. Use `from __future__ import annotations` at the top of every file for forward reference support.

```python
# YES — fully typed, clear, documented
from __future__ import annotations

async def calculate_cap_rate(noi: Decimal, purchase_price: Decimal) -> Decimal:
    """Calculate capitalization rate: NOI / Purchase Price."""
    if purchase_price <= 0:
        raise ValueError("Purchase price must be positive")
    return (noi / purchase_price).quantize(Decimal("0.001"))

# NO — untyped, no docstring, no validation
def calc_cap(noi, price):
    return noi / price
```

Use `Decimal` (not `float`) for all financial calculations. Floating point arithmetic produces rounding errors that compound across mortgage amortization schedules and multi-year projections. Import from `decimal` and use `Decimal("0.01")` for quantization.

```python
from decimal import Decimal, ROUND_HALF_UP

# YES
monthly_payment = Decimal("1342.05")
annual = (monthly_payment * 12).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# NO — float will cause rounding drift over 30-year amortization
monthly_payment = 1342.05
annual = monthly_payment * 12
```

Import ordering: standard library, then blank line, then third-party, then blank line, then local imports. Use absolute imports, not relative.

```python
import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.deal import Deal
from app.schemas.deal import DealCreate, DealResponse
from app.services.deal_calculator import DealCalculator
```

Naming conventions: snake_case for everything in Python (variables, functions, files, modules). PascalCase only for classes. Constants in UPPER_SNAKE_CASE. No abbreviations in variable names unless universally understood in real estate (NOI, DSCR, IRR, GRM, LTV, ARV, CoC are all acceptable abbreviations).

### FastAPI Patterns

Every router file follows this structure:

```python
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.deal import DealCreate, DealUpdate, DealResponse, DealListResponse
from app.services.deal_calculator import DealCalculator

router = APIRouter(prefix="/api/v1/deals", tags=["deals"])


@router.post("/", response_model=DealResponse, status_code=status.HTTP_201_CREATED)
async def create_deal(
    deal_data: DealCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DealResponse:
    """Create a new deal analysis for a property. Triggers metric calculation."""
    # ... implementation
```

All endpoints that access user data must depend on `get_current_user`. Every query must filter by `user_id` to enforce data isolation — a user must never see another user's properties, deals, or portfolio data.

Use dependency injection for database sessions and the current user. Never create database sessions manually inside route handlers.

Return appropriate HTTP status codes: 201 for creation, 200 for retrieval and updates, 204 for deletion, 400 for bad input, 401 for auth failures, 403 for forbidden access, 404 for not found, 422 for validation errors (FastAPI default for Pydantic failures).

### Error Handling

Use a consistent error response format across the entire API:

```python
# All error responses follow this shape
{
    "detail": "Human-readable error message",
    "error_code": "DEAL_NOT_FOUND",  # machine-readable code for frontend
    "field": "purchase_price"         # optional: which field caused the error
}
```

Create custom exception classes in `middleware/error_handler.py` and register exception handlers in `main.py`. Never let raw SQLAlchemy or Python exceptions leak to the client.

**External API failure handling (critical — this is what senior engineers look for):**
- **RentCast 429 (rate limited):** Log the error with remaining quota info, return cached data if available within TTL, otherwise return a clear error to the user explaining the monthly limit has been reached. Never silently fail.
- **RentCast 404 (property not found):** Return a helpful message suggesting the user check the address format. Pre-validate address format on the frontend before hitting the API.
- **RentCast/Mashvisor 5xx (server error):** Retry once after 2 seconds with exponential backoff, then return cached data or graceful error. Never retry more than once — external APIs might be down for hours.
- **Claude API timeout mid-stream:** Return partial response if available, or a clear "The AI assistant is temporarily unavailable, please try again" message. Log the timeout duration and token count for cost tracking.
- **Network failure (connection refused, DNS error):** Return cached data if available, otherwise return a specific error code (`EXTERNAL_API_UNAVAILABLE`) so the frontend can show appropriate UI (not a generic 500 page).
- **Invalid/unexpected API response shape:** Log the full raw response for debugging, return a generic "We couldn't process the property data" error. Never crash on unexpected JSON structure — use Pydantic's `model_validate` with error handling.

Implement a **circuit breaker pattern** for external APIs: after 3 consecutive failures within 5 minutes, stop making requests and serve only cached data for 10 minutes before retrying. This prevents cascading failures and protects API quotas.

### Pydantic Schema Patterns

Separate schemas for create, update, and response. The response schema includes computed fields. The create schema only includes user-provided inputs. The update schema makes all fields optional.

```python
class DealCreate(BaseModel):
    """Fields the user provides when creating a deal."""
    property_id: uuid.UUID
    deal_name: str | None = None
    purchase_price: Decimal
    gross_monthly_rent: Decimal
    # ... all user inputs, NO computed fields

class DealUpdate(BaseModel):
    """All fields optional for partial updates."""
    deal_name: str | None = None
    purchase_price: Decimal | None = None
    # ... every field from DealCreate but Optional

class DealResponse(BaseModel):
    """Full deal with all computed metrics included."""
    id: uuid.UUID
    property_id: uuid.UUID
    purchase_price: Decimal
    gross_monthly_rent: Decimal
    # ... all user inputs PLUS all computed fields:
    noi: Decimal | None
    cap_rate: Decimal | None
    cash_on_cash: Decimal | None
    monthly_cash_flow: Decimal | None
    risk_score: Decimal | None
    risk_factors: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

### SQLAlchemy Model Patterns

Use SQLAlchemy 2.0 style with `Mapped` and `mapped_column`. Always use async sessions.

```python
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, String, Numeric, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    # ... etc

    # Relationships
    property: Mapped["Property"] = relationship(back_populates="deals")
    user: Mapped["User"] = relationship(back_populates="deals")
```

---

## Database Conventions

All table names are plural snake_case (`users`, `deals`, `market_snapshots`). All column names are snake_case. Primary keys are UUIDs, never auto-incrementing integers (UUIDs are better for distributed systems and don't leak information about record count).

Every table has `created_at` (set once on insert) and `updated_at` (updated on every modification) timestamps. Use `server_default=func.now()` and `onupdate=func.now()` in SQLAlchemy.

Foreign keys always specify `ondelete="CASCADE"` when the child record should be deleted with the parent (e.g., deleting a property deletes its deals). Use `ondelete="SET NULL"` when the child should survive (rare in this project).

Use Alembic for all schema changes. Never modify the database manually. Migration messages should describe the change: `"add risk_score column to deals table"`, not `"update deals"`. Migrations must be clean and reversible — every `upgrade()` needs a working `downgrade()`.

---

## CI/CD and Code Quality Infrastructure

This is set up in Week 0, before any application code is written. These tools enforce quality automatically regardless of whether Claude Code or the developer wrote the code.

### Pre-commit Hooks (`.pre-commit-config.yaml`)

Run automatically on every `git commit`:
- **Black:** Python code formatting (line length 88)
- **isort:** Python import ordering (profile: black)
- **ruff:** Python linting (catches bugs, security issues, style violations)
- **Prettier:** React/TypeScript/CSS formatting
- **ESLint:** React linting

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks: [{id: black}]
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks: [{id: isort, args: [--profile, black]}]
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks: [{id: ruff, args: [--fix]}]
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks: [{id: prettier, types_or: [javascript, jsx, ts, tsx, css, json]}]
```

### GitHub Actions (`.github/workflows/ci.yml`)

Runs on every push to `main` and every PR:
1. Set up Python + Node.js environments
2. Install dependencies
3. Run `ruff check` and `black --check` (lint)
4. Run `pytest` with coverage report (target: 80%+ on business logic)
5. Run frontend build + ESLint
6. Auto-deploy to Vercel (frontend) + Railway (backend) on merge to main

### Automated PR Review

Use **Bugbot** or Claude's GitHub integration for automated review on every PR. This catches security issues, bugs, and anti-patterns that a solo developer will miss when moving fast. Worth the cost as a safety net.

---

## Monitoring and Observability

### Error Tracking (Sentry)

Set up Sentry free tier for both FastAPI and React from Week 0:
- FastAPI: Catches unhandled exceptions, slow transactions, failed external API calls
- React: Catches JavaScript errors, failed API calls, render crashes
- Configure source maps for readable stack traces in production

### Structured Logging

All API requests get structured JSON logs. Never use `print()` for debugging in production code.

```python
import structlog

logger = structlog.get_logger()

# Every API call logs:
logger.info(
    "api_request",
    endpoint="/api/v1/deals",
    method="POST",
    user_id=str(current_user.id),
    response_time_ms=elapsed,
    status_code=201,
)

# External API calls log separately:
logger.info(
    "external_api_call",
    service="rentcast",
    endpoint="/properties",
    response_time_ms=elapsed,
    cache_hit=False,
    calls_remaining=42,  # track quota burn rate
)
```

### Cost Tracking

- **RentCast/Mashvisor:** Log every API call with remaining quota. Alert (log warning) at 80% of monthly limit.
- **Claude API (Phase 2):** Log token usage per chat session (input tokens, output tokens, total cost estimate). Set a per-session token budget (cap at ~4000 tokens per conversation turn).
- **Railway:** Monitor database size and compute usage via Railway dashboard.

---

## Testing Requirements

Every service function and every API endpoint must have tests. The test suite should pass with `pytest` from the project root with zero configuration. Target: 80%+ coverage on business logic (deal calculations, risk scoring), lower bar acceptable on UI components.

**Test file naming:** `test_{module_name}.py` in the `tests/` directory. Mirror the structure of what you're testing.

**Fixtures (`conftest.py`) must provide:**
- An async test database session (use a separate test database, not the dev database)
- A FastAPI TestClient configured with the test database
- A factory for creating test users (with pre-hashed passwords)
- A factory for creating test properties with realistic Midwest data
- A factory for creating test deals with realistic financial inputs
- Mock responses for RentCast API calls (never hit the real API in tests)

**What to test in the deal calculator:**
- Every metric calculation with known inputs and expected outputs
- Edge cases: zero purchase price, negative rent, 100% vacancy, zero down payment, interest-only loans
- Consistency: creating a deal and retrieving it should return identical metrics
- Decimal precision: verify calculations don't lose precision over multi-year projections

**What to test in the risk scoring engine:**
- Each of the 11 risk factors independently
- Boundary conditions at risk thresholds (e.g., DSCR exactly 1.0, exactly 1.5)
- Composite score calculation with known factor scores and weights
- Edge cases: all-cash purchase (no DSCR), new construction (no age risk), single-property portfolio (no concentration risk)

**What to test in API endpoints:**
- Happy path: create, read, update, delete operations succeed with valid input
- Authentication: unauthenticated requests return 401
- Authorization: users cannot access other users' data (create user A and user B, verify A can't see B's deals)
- Validation: missing required fields return 422, invalid values return 400
- Not found: requesting nonexistent resources returns 404

```python
# Example test structure
class TestDealCalculator:
    """Tests for the deal calculator service."""

    def test_calculate_noi(self):
        """NOI = Effective Gross Income - Operating Expenses, annualized."""
        # Known inputs
        gross_rent = Decimal("1800.00")  # monthly
        vacancy_rate = Decimal("5.00")   # percent
        property_tax = Decimal("200.00") # monthly
        insurance = Decimal("100.00")    # monthly
        maintenance_rate = Decimal("5.00")  # percent of rent
        management_rate = Decimal("10.00")  # percent of rent

        result = DealCalculator.calculate_noi(
            gross_monthly_rent=gross_rent,
            vacancy_rate_pct=vacancy_rate,
            property_tax_monthly=property_tax,
            insurance_monthly=insurance,
            maintenance_rate_pct=maintenance_rate,
            management_fee_pct=management_rate,
        )

        # Hand-calculated expected value:
        # Vacancy loss: 1800 * 0.05 = 90
        # EGI: 1800 - 90 = 1710
        # Maintenance: 1800 * 0.05 = 90
        # Management: 1800 * 0.10 = 180
        # Total OpEx: 200 + 100 + 90 + 180 = 570
        # Monthly NOI: 1710 - 570 = 1140
        # Annual NOI: 1140 * 12 = 13680
        assert result == Decimal("13680.00")

    def test_zero_purchase_price_raises(self):
        """Cap rate calculation must reject zero purchase price."""
        with pytest.raises(ValueError, match="positive"):
            DealCalculator.calculate_cap_rate(
                noi=Decimal("13680.00"),
                purchase_price=Decimal("0"),
            )
```

---

## External API Integration Rules

### General Principles

All external API calls go through dedicated client classes in `backend/app/integrations/`. Never call external APIs directly from routers or services. The integration layer is responsible for: making the HTTP request, handling rate limits and retries, normalizing the response into our internal data structures, caching responses, and logging errors.

Use `httpx.AsyncClient` for all external HTTP calls. Create a shared client instance with appropriate timeouts (10 seconds connect, 30 seconds read for property lookups).

### RentCast Integration (Phase 1)

Base URL: `https://api.rentcast.io/v1`
Auth: API key in `X-Api-Key` header
Rate limit: 50 calls/month on free tier — every call is precious

**Endpoints to integrate:**
- `GET /properties` — Look up property by address (returns structural data, tax info)
- `GET /avm/rent/long-term` — Get rent estimate for a property
- `GET /avm/value` — Get property value estimate
- `GET /listings/rental/long-term` — Get nearby rental comps
- `GET /markets` — Get market statistics by zip code

**Caching strategy for RentCast (critical with 50 calls/month):**
- Cache property lookups for 30 days (property attributes rarely change)
- Cache rent estimates for 14 days
- Cache value estimates for 14 days
- Cache market stats for 30 days
- Store raw JSON response in `raw_response` JSONB column for reprocessing without burning API calls
- Before every API call, check the cache first. Log when a cache hit saves an API call.

**Error handling for RentCast:**
- 429 (rate limited): Log the error, return cached data if available, otherwise return a clear error to the user explaining the monthly limit
- 404 (property not found): Return a helpful message suggesting the user check the address format
- 5xx (server error): Retry once after 2 seconds, then return cached data or error

### Mashvisor Integration (Phase 3 — do not build yet)

Will be added in Phase 3 for market comparisons. The integration client should follow the exact same patterns as the RentCast client: separate class, async httpx, caching, error handling, response normalization.

### Zillow Research Datasets (Phase 3 — do not build yet)

These are CSV downloads loaded via a batch script, not a live API. The script in `scripts/seed_market_data.py` will download CSVs from zillow.com/research/data, parse them with pandas, and insert rows into the `market_snapshots` table. This only runs manually or on a monthly cron, not on every request.

---

## Domain Knowledge: Real Estate Financial Formulas

Claude Code needs to understand these formulas to write correct tests, generate meaningful test data, and review the developer's calculator implementation. All formulas use annual figures unless noted.

**Net Operating Income (NOI):**
NOI = Effective Gross Income − Total Operating Expenses
Effective Gross Income = (Gross Rent + Other Income) − Vacancy Loss
Vacancy Loss = Gross Rent × Vacancy Rate
Operating Expenses = Property Tax + Insurance + Maintenance + Management Fee + HOA + Utilities
NOTE: Mortgage payments are NOT part of operating expenses. NOI is calculated before debt service.

**Cap Rate (Capitalization Rate):**
Cap Rate = NOI / Purchase Price (or Current Market Value)
A 7% cap rate in the Midwest is generally considered good. Below 4% is low-return. Above 10% often signals higher risk.

**Cash-on-Cash Return:**
Cash-on-Cash = Annual Cash Flow / Total Cash Invested
Total Cash Invested = Down Payment + Closing Costs + Rehab Costs
Annual Cash Flow = NOI − Annual Debt Service (mortgage payments × 12)
This measures return on the actual cash you put in, not the total property value. A 10%+ CoC is strong.

**Debt Service Coverage Ratio (DSCR):**
DSCR = NOI / Annual Debt Service
Lenders typically require DSCR ≥ 1.25 (meaning income covers 125% of the mortgage). Below 1.0 means the property loses money before any equity benefit. This is a critical metric for loan qualification.

**Gross Rent Multiplier (GRM):**
GRM = Purchase Price / Annual Gross Rent
Lower GRM = better value. In the Midwest, a GRM under 10 is generally favorable.

**Monthly Mortgage Payment (fixed rate):**
M = P × [r(1+r)^n] / [(1+r)^n − 1]
Where: P = loan amount, r = monthly interest rate (annual / 12), n = total payments (years × 12)

**Internal Rate of Return (IRR):**
The discount rate that makes the Net Present Value of all cash flows equal to zero. Cash flows include: initial investment (negative), annual cash flow for each year held, and net sale proceeds at exit (sale price minus selling costs minus remaining loan balance). Use numpy_financial.irr() or implement Newton's method.

**Equity Buildup:**
Each mortgage payment splits into principal and interest. The principal portion reduces the loan balance, building equity. To calculate equity at year N: compute the remaining loan balance after N years of payments and subtract from original loan amount. Add to any appreciation in property value.

**The 1% Rule (quick screening):**
Monthly Rent / Purchase Price ≥ 1%. This is stored as `rent_to_price_ratio` in market_snapshots. It's a rough filter, not a definitive metric.

**Realistic Midwest defaults for test data:**
- Sheboygan duplex: Purchase $185,000–$230,000, monthly rent $1,400–$1,800, property tax $250–$400/month
- Milwaukee duplex: Purchase $150,000–$280,000, monthly rent $1,200–$2,000
- Vacancy rate: 5–8% (Wisconsin average)
- Insurance: $80–$150/month
- Maintenance reserve: 5–10% of gross rent
- Management fee: 8–10% of gross rent (if professional management)
- Interest rate: 6.5–7.5% (2025–2026 market)
- Down payment: 20–25% for investment properties
- Closing costs: 2–4% of purchase price

---

## Security Considerations

**Authentication:** JWT access tokens (short-lived, 30 minutes) + refresh tokens (long-lived, 7 days). Store refresh tokens in the database so they can be revoked. Hash passwords with bcrypt (use `passlib[bcrypt]`). Never log passwords, tokens, or API keys.

**Data isolation:** Every database query touching user data must include a `WHERE user_id = :current_user_id` clause. This is non-negotiable. Write a test that verifies User A cannot access User B's deals.

**Input validation:** Pydantic handles most validation, but add explicit checks for financial inputs: purchase price must be positive, percentages must be 0–100, interest rates must be 0–30 (sanity check), rent must be non-negative. Reject obviously invalid data early with clear error messages.

**API keys:** All external API keys (RentCast, Mashvisor, Anthropic) go in environment variables, never in code. The `.env.example` file shows the required variables with placeholder values. The actual `.env` is in `.gitignore`.

**Rate limiting:** Add per-user rate limiting to the API using FastAPI middleware (e.g., `slowapi`):
- General endpoints: 100 requests/minute per user
- External API proxy endpoints (property lookup): 10 requests/minute per user (protects RentCast quota)
- Chat endpoint: 20 requests/minute per user (protects Claude API costs)
- Token budget per chat session: ~4000 tokens per conversation turn (Phase 2)

**No API keys in client code:** The React frontend never calls external APIs directly. All external data flows through the FastAPI backend, which holds the API keys server-side.

---

## Onboarding UX Requirements

**The 10-second rule:** A recruiter must be able to go from landing page to seeing a deal analysis in under 10 seconds. This is the single most important UX metric.

**Minimum viable input:** Address + purchase price. That's it. Everything else gets auto-filled:
- Property details (bedrooms, bathrooms, sqft, year built, type) → auto-filled from RentCast property lookup
- Rent estimate → auto-filled from RentCast rent AVM
- Property tax → auto-filled from RentCast property records
- Insurance, maintenance, management → pre-filled with Midwest defaults (editable)
- Financing → pre-filled with standard investment loan terms: 20% down, 7% rate, 30-year fixed (editable)
- Vacancy → pre-filled with 5% Wisconsin average (editable)

**Two-tier form design:**
1. **Essential inputs (visible):** Address field with autocomplete + purchase price field + "Analyze Deal" button
2. **Advanced inputs (collapsed accordion):** All the pre-filled values above, expandable for users who want to customize. Each field shows its source ("From RentCast", "Wisconsin average", "Standard investment terms")

**Demo mode:** Consider a "Try with sample data" button on the landing page that auto-fills a Sheboygan duplex example without requiring registration. This lets recruiters see the product immediately, then prompts them to register to save deals.

---

## README Strategy

The README is a resume artifact. It should be written for two audiences: (1) a recruiter who spends 30 seconds scanning, and (2) a senior engineer who spends 5 minutes evaluating.

**Required sections:**
1. **One-liner:** "Full-stack real estate investment analyzer for Wisconsin rental markets"
2. **Screenshot or GIF:** The deal analysis page with real data. Add after Phase 1 deploys.
3. **Live demo link:** The deployed URL. This is the most important line in the README.
4. **Quick Start:** 3 commands to run locally (`git clone`, `docker-compose up`, `open localhost:3000`)
5. **Architecture diagram:** Simple box diagram: React → FastAPI → PostgreSQL, with RentCast/Mashvisor/Claude API as external services
6. **What I built vs. what Claude Code built:** This is your differentiator. Be explicit and honest. Example:
   > "I used Claude Code for scaffolding — route definitions, database models, React component layout, CI/CD configuration. The deal calculation engine (`/src/core/calculations/`), 11-factor risk scoring algorithm (`/src/core/risk_scoring/`), LLM prompt engineering, and all business logic tests are entirely hand-written. I chose the risk scoring weights, I designed the API contracts, and I can walk through every financial formula on a whiteboard."
7. **Tech stack badges:** Python, FastAPI, PostgreSQL, React, Tailwind, Claude API
8. **Architecture Decision Records (brief):** Why PostgreSQL over MongoDB, why FastAPI over Django, why direct context injection over RAG

---

## Git Conventions

**Branch naming:** `feature/{short-description}` for new features, `fix/{short-description}` for bug fixes, `refactor/{short-description}` for refactoring.

**Commit messages:** Use conventional commits format. Start with a type, then a concise description.
- `feat: add deal calculator with NOI and cap rate calculations`
- `fix: correct mortgage payment formula for edge case with zero interest`
- `test: add test coverage for deal CRUD endpoints`
- `refactor: extract financial math into utils/financial.py`
- `docs: update ARCHITECTURE.md with risk scoring weights`
- `chore: add Docker Compose configuration`
- `ci: add GitHub Actions workflow for pytest on push`

**What to commit:** Commit working code. Every commit should leave the test suite passing. Do not commit half-implemented features. If a feature spans multiple sessions, use a feature branch.

---

## Common Pitfalls to Avoid

**Financial math with floats:** Never use Python `float` for money. Use `Decimal` everywhere. A 30-year mortgage amortization table computed with floats will drift by hundreds of dollars. This is the single most common source of bugs in financial software.

**Forgetting to recalculate:** When a deal's inputs are updated (PUT /deals/{id}), all computed metrics must be recalculated before saving. The router should call the deal calculator service on every create and update, not just on create.

**Async SQLAlchemy gotchas:** Use `AsyncSession` and `await` for all database operations. Use `selectinload()` or `joinedload()` for relationships to avoid lazy loading (which doesn't work in async). Never access a relationship attribute without explicitly loading it first.

**Test database pollution:** Use a transaction-per-test pattern. Each test runs inside a transaction that gets rolled back, so tests don't affect each other. The conftest.py fixture handles this.

**Pydantic v2 breaking changes:** Use `model_config = ConfigDict(from_attributes=True)` instead of the old `class Config: orm_mode = True`. Use `model_dump()` instead of `dict()`. Use `model_validate()` instead of `from_orm()`.

**RentCast quota waste:** During development, mock all RentCast calls. Only use real API calls for manual integration testing. The 50/month free tier has zero room for test suite runs hitting the real API.

**Mortgage formula edge cases:** Handle zero interest rate (the formula divides by zero — in that case, monthly payment is simply loan_amount / total_months). Handle zero loan amount (all-cash purchase — monthly mortgage is zero, DSCR is infinity or N/A). Handle zero down payment (100% financing — total_cash_invested is just closing + rehab costs).

**Environment configuration:** Maintain separate configs for local dev, test, and production. Use Pydantic `BaseSettings` to load from environment variables with sensible defaults for dev. Never hardcode any API keys, database URLs, or secrets.

---

## Frontend Animation Guide (React Bits)

This project uses React Bits (reactbits.dev) for polished micro-interactions and entrance animations. React Bits components are copy-pasted into the project via the shadcn CLI — they become local source files in `frontend/src/components/ui/`, not an npm runtime dependency. Always use the **TS-TW** (TypeScript + Tailwind) variant.

**Important:** This is a financial analysis tool, not a creative portfolio. Every animation must serve a purpose. Function over flash — animations enhance data comprehension and provide feedback, they never compete with the data for attention.

### Installation

```bash
# Install a component via shadcn CLI (from the frontend/ directory)
npx shadcn@latest add @react-bits/CountUp-TS-TW
npx shadcn@latest add @react-bits/BlurText-TS-TW
npx shadcn@latest add @react-bits/SpotlightCard-TS-TW

# Or copy code manually from https://reactbits.dev/{category}/{component}
# Select "TS" and "Tailwind" toggles, then copy into frontend/src/components/ui/
```

Some React Bits components depend on Framer Motion (`framer-motion`). Install it once as a project dependency if any component needs it:
```bash
npm install framer-motion
```

### Component-to-Page Map

This is the definitive mapping of which React Bits component goes where in the app. When building a page, reference this table to know which animation to apply.

**Dashboard Page (`/dashboard`):**
- `CountUp` → Every KPI number: total monthly cash flow, portfolio cap rate, total equity, deal count, average cash-on-cash. Animates from 0 to the actual value on page load. Use `prefix="$"` for dollar amounts, `suffix="%"` for percentages, and `decimals={2}` for financial precision.
- `BlurText` → Section headings: "Portfolio Overview", "Your Active Deals", "Recent Activity". Blur-to-focus entrance on load.
- `SpotlightCard` → Wraps each deal summary card in the deal grid. Adds cursor-following light effect on hover. Apply to the card container, keep the inner content (address, metrics, risk score) as normal elements.
- `StarBorder` → Wraps the single best-performing deal card (highest cash-on-cash) with a green animated border, and the highest-risk deal card (highest risk score) with a red animated border. Use `color` prop to set the border color. Apply to at most 2 cards on the dashboard, not all of them.

**Deal Detail Page (`/deals/:id`):**
- `CountUp` → All financial metrics in the metrics summary section: NOI, cap rate, cash-on-cash, DSCR, GRM, monthly cash flow, total cash invested, IRR projections, equity buildup.
- `AnimatedContent` → Wraps each section (metrics summary, financing details, expense breakdown, projections chart) so they fade/slide in sequentially as the page loads. Use `delay` prop to stagger: first section 0ms, second 100ms, third 200ms, etc.
- `GradientText` → Risk score label text. Use green-to-teal gradient for "Low Risk" (score 0-33), yellow-to-orange for "Moderate Risk" (34-66), orange-to-red for "High Risk" (67-100). The `colors` prop controls the gradient stops.

**Chat Interface (`/chat`):**
- `AnimatedList` → Wraps the entire message list. Each new message (user or bot) enters with a smooth slide-up animation. This is the primary animation for the chatbot page.
- `DecryptedText` → Apply selectively to key financial numbers within chatbot responses (e.g., when the bot says "Your total monthly cash flow is $2,847.33", the dollar amount decrypts character by character). Do NOT apply to entire paragraphs — only short numerical values. Falls back to `SplitText` (word-by-word entrance) if DecryptedText feels too "techy" during review.

**Market Comparison Page (`/markets/compare`):**
- `CountUp` → All comparison metrics on both sides: median home value, median rent, avg cap rate, vacancy rate, YoY appreciation, population growth. Both columns animate simultaneously for a dramatic side-by-side reveal.
- `AnimatedContent` → Wraps each comparison panel so they slide in from opposite sides (left panel from left, right panel from right). Use the `direction` prop.

**Deal Card Grid (shared component used on Dashboard, Deals List, Portfolio):**
- `SpotlightCard` → Default card wrapper for all deal cards across the app. The spotlight effect provides consistent interactive feedback everywhere cards appear.
- `TiltedCard` → Alternative to SpotlightCard. Use for a "Featured Deal" or "Deal of the Month" highlight if one is needed. Do NOT use TiltedCard and SpotlightCard on the same page — pick one style per context.

**Auth Pages (`/login`, `/register`):**
- `Aurora` → Animated gradient background on the login and register pages. Creates a premium first impression. Use dark color scheme with subtle blue/purple/teal hues. Apply as a full-screen background behind the auth form card.
- `BlurText` → App name "MidwestDealAnalyzer" entrance animation on the auth pages.
- `GradientText` → Optional: apply to the app name for animated gradient branding.

**Navigation Bar:**
- `Dock` → (OPTIONAL) macOS-style magnifying icon bar as the main navigation. Icons for Dashboard, Deals, Markets, Portfolio, Chat that expand on hover. Only implement if the developer decides to go with it — a standard sidebar or top nav is the safe default.

**Buttons & Micro-interactions (global):**
- `ClickSpark` → Wraps primary action buttons: "Analyze Deal", "Save to Portfolio", "Compare Markets", "Run Scenario". Emits a small spark particle burst on click. Use `sparkColor` matching the button's accent color.
- `Magnet` → (OPTIONAL) Apply to CTA buttons so they drift slightly toward the cursor on approach. Very subtle effect — the pull distance should be small (5-10px max).

### Animation Principles for This Project

**DO NOT use these React Bits components in this project:**
- BlobCursor, SplashCursor — distracting on a data-heavy dashboard
- GlitchText, AsciiText — wrong aesthetic for financial tools
- Ballpit, Hyperspeed — heavy 3D/WebGL, hurts performance, feels unserious
- TextPressure, CircularText — novelty effects with no natural home in a dashboard
- Particles backgrounds — signals "marketing site" not "financial tool"
- Iridescence, Threads — too flashy for functional data pages

**Performance rules:**
- Never put animated backgrounds (Aurora, Beams, GridMotion) on pages with data tables or charts. Reserve them for auth pages and landing pages only.
- CountUp should trigger once per page load, not re-animate on every re-render. Use scroll-triggered animation (`scrollSpyOnce` pattern) for numbers below the fold.
- SpotlightCard's cursor tracking runs on `mousemove` — this is fine for a grid of 10-20 cards but consider disabling it on mobile (no cursor) by checking for touch devices.
- AnimatedList should only animate NEW messages entering the list, not re-animate the entire history when the component re-renders. Track which messages have already been displayed.

### React Bits Rollout Schedule

Animations are layered in after core functionality is deployed and working. They are Phase 3-4 work, not Phase 1.

**Phase 3 Week 7 (highest impact, easiest):** CountUp, BlurText, SpotlightCard — these go on the dashboard
**Phase 3 Week 8 (chat & detail pages):** AnimatedList, AnimatedContent, StarBorder
**Phase 4 Week 10 (polish & micro-interactions):** ClickSpark, DecryptedText/SplitText, GradientText
**Phase 4 Week 11 (optional flourishes):** Aurora/Beams on auth, Dock navigation, Magnet on CTAs

---

## How to Start a New Session

When starting work on a new task:

1. Read this file (CLAUDE.md), ARCHITECTURE.md, and PRD.md
2. Check which phase is currently active (see "Current Development Phase" above)
3. Run `pytest` to confirm the test suite passes before making changes
4. Check if the task involves a developer-owned file (see "Ownership Boundaries")
5. If scaffolding new files, follow the directory structure in ARCHITECTURE.md exactly
6. After making changes, run `pytest` again to verify nothing broke
7. Pre-commit hooks will enforce formatting automatically on commit; if running manually, use `black .` and `ruff check .`
8. For complex tasks, use plan mode first: describe the approach, get approval, then implement
