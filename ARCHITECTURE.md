# Real Estate Deal Analyzer — System Architecture

## Project Overview

A Midwest-focused real estate investment analysis platform with an AI-powered chatbot. The platform helps investors evaluate rental property deals by calculating ROI metrics, scoring risk with an 11-factor algorithm, comparing market data, and tracking portfolios — with a conversational AI assistant that answers questions about the user's own deals and market conditions.

**Target Region:** Midwest United States (Wisconsin, Illinois, Michigan, Minnesota, Indiana, Ohio)
**Primary Use Case:** Duplex and small multifamily rental property analysis
**Tech Stack:** Python, FastAPI, PostgreSQL, React, Claude API
**Live URL:** midwestdealanalyzer.com (or similar — check availability)

**The 10-second test:** A recruiter enters "123 Main St, Sheboygan WI" + "$185,000" → the app auto-fills property details from RentCast → displays full deal analysis with risk score → all in under 10 seconds. This is the north star UX metric.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  (Dashboard, Deal Input Forms, Chat Interface, Portfolio)│
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP / WebSocket
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Backend                         │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐ │
│  │  Auth    │ │  Deals   │ │ Portfolio │ │  Chatbot  │ │
│  │  Module  │ │  Engine  │ │  Tracker  │ │ (Context) │ │
│  └──────────┘ └──────────┘ └───────────┘ └───────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐               │
│  │  Market  │ │   Risk   │ │  Data     │               │
│  │  Compare │ │  Scoring │ │  Pipeline │               │
│  └──────────┘ └──────────┘ └───────────┘               │
└──────────┬──────────────────────────────────────────────┘
           │
     ┌─────▼────────┐     ┌──────────────┐
     │  PostgreSQL   │     │  External    │
     │  (Core Data)  │     │  APIs        │
     └──────────────┘     └──────┬───────┘
                                  │
                       ┌──────────┼──────────┐
                       ▼          ▼          ▼
                    RentCast   Mashvisor   Zillow
                    (Phase 1)  (Phase 3)  (Research
                                           Datasets)
```

---

## Tech Stack Decisions

**FastAPI over Django:** FastAPI gives you async support out of the box, which matters when you're making multiple external API calls (RentCast, Mashvisor) per request. It also auto-generates OpenAPI docs at `/docs`, which is a nice portfolio flex. Django's ORM is powerful but overkill here — SQLAlchemy with FastAPI gives you more control and is more common in backend engineering roles you're targeting.

**PostgreSQL over MongoDB:** Real estate data is inherently relational. A property has many deals, a user has many properties, deals have financial projections tied to market data snapshots. PostgreSQL handles this naturally and is the industry standard for financial data.

**Direct Context Injection over pgvector/RAG:** At the scale of a personal portfolio tool (5-50 properties), all deal data fits comfortably in a single LLM context window (~2,000-5,000 tokens). RAG adds real complexity (embedding pipeline, vector indexing, similarity search tuning, chunking strategy) and provides zero benefit at this scale. Serialize all user deals into the system prompt and let the LLM reason over the full dataset directly. If the app scales to thousands of properties per user, RAG becomes necessary — document this as a "future scalability path" but don't build it now. This decision must be defensible in an interview: "I chose direct context injection because my data volume fits in the context window. RAG would be premature optimization that adds complexity without measurable benefit. I know how to implement it — here's how I'd add it when scale demands it."

**React for Frontend:** Aligns with your career roadmap. A clean dashboard with interactive charts (Recharts or Chart.js) showing deal metrics, portfolio performance, and market comparisons demonstrates full-stack capability.

**React Bits for Animations:** React Bits (reactbits.dev) is an open-source library of 110+ animated React components. We use it for polished micro-interactions and entrance animations that elevate the UI from "generic CRUD app" to "professional financial tool." Components are copy-paste installed via shadcn CLI using the TS-TW (TypeScript + Tailwind) variant, so they integrate cleanly with our existing stack with zero runtime dependency. Key components: CountUp (animated KPI numbers), SpotlightCard (deal cards), AnimatedList (chatbot messages), BlurText (section headings), StarBorder (deal highlights), ClickSpark (button feedback), Aurora/Beams (auth page backgrounds). Animations are Phase 3-4 work — function ships before flash.

**Claude API for Chatbot:** You're already using Claude Pro for development. The API gives you the best reasoning quality for complex financial Q&A. Use a smaller/free model (Ollama + Llama locally) during development to save costs, then switch to Claude for production demos.

---

## Database Schema

### Core Tables

```sql
-- Users table with JWT auth support
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Properties are the central entity
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    address VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(2) NOT NULL,
    zip_code VARCHAR(10) NOT NULL,
    county VARCHAR(100),
    property_type VARCHAR(50) NOT NULL,  -- 'single_family', 'duplex', 'triplex', 'fourplex', 'multifamily'
    num_units INTEGER DEFAULT 1,
    bedrooms INTEGER,
    bathrooms NUMERIC(3,1),
    square_footage INTEGER,
    lot_size INTEGER,
    year_built INTEGER,
    -- External API references for data refresh
    rentcast_id VARCHAR(100),
    mashvisor_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Each property can have multiple deal analyses (different scenarios)
CREATE TABLE deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    deal_name VARCHAR(100),  -- e.g., "Conservative estimate", "Best case"
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'active', 'closed', 'passed'

    -- Purchase details
    purchase_price NUMERIC(12,2) NOT NULL,
    closing_costs NUMERIC(10,2) DEFAULT 0,
    rehab_costs NUMERIC(10,2) DEFAULT 0,
    after_repair_value NUMERIC(12,2),

    -- Financing
    down_payment_pct NUMERIC(5,2) DEFAULT 20.00,
    loan_amount NUMERIC(12,2),
    interest_rate NUMERIC(5,3),
    loan_term_years INTEGER DEFAULT 30,
    monthly_mortgage NUMERIC(10,2),

    -- Income (monthly)
    gross_monthly_rent NUMERIC(10,2) NOT NULL,
    other_monthly_income NUMERIC(10,2) DEFAULT 0,  -- laundry, parking, storage

    -- Expenses (monthly)
    property_tax_monthly NUMERIC(10,2),
    insurance_monthly NUMERIC(10,2),
    vacancy_rate_pct NUMERIC(5,2) DEFAULT 5.00,
    maintenance_rate_pct NUMERIC(5,2) DEFAULT 5.00,
    management_fee_pct NUMERIC(5,2) DEFAULT 10.00,
    hoa_monthly NUMERIC(10,2) DEFAULT 0,
    utilities_monthly NUMERIC(10,2) DEFAULT 0,

    -- Calculated metrics (stored for fast retrieval, recalculated on update)
    noi NUMERIC(12,2),              -- Net Operating Income (annual)
    cap_rate NUMERIC(6,3),          -- NOI / Purchase Price
    cash_on_cash NUMERIC(6,3),      -- Annual Cash Flow / Total Cash Invested
    monthly_cash_flow NUMERIC(10,2),
    annual_cash_flow NUMERIC(12,2),
    total_cash_invested NUMERIC(12,2),
    dscr NUMERIC(6,3),              -- Debt Service Coverage Ratio
    grm NUMERIC(6,2),               -- Gross Rent Multiplier
    irr_5yr NUMERIC(6,3),           -- Internal Rate of Return (5-year projection)
    irr_10yr NUMERIC(6,3),          -- Internal Rate of Return (10-year projection)
    equity_buildup_5yr NUMERIC(12,2),
    equity_buildup_10yr NUMERIC(12,2),

    -- Risk score (computed by risk engine)
    risk_score NUMERIC(5,2),        -- 0-100, lower is better
    risk_factors JSONB,             -- detailed breakdown of risk components

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Market data snapshots for comparison features
CREATE TABLE market_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zip_code VARCHAR(10) NOT NULL,
    city VARCHAR(100),
    state VARCHAR(2) NOT NULL,
    snapshot_date DATE NOT NULL,

    -- Market-level metrics
    median_home_value NUMERIC(12,2),
    median_rent NUMERIC(10,2),
    avg_price_per_sqft NUMERIC(10,2),
    avg_days_on_market INTEGER,
    inventory_count INTEGER,
    avg_cap_rate NUMERIC(6,3),
    avg_vacancy_rate NUMERIC(5,2),
    rent_to_price_ratio NUMERIC(6,4),  -- 1% rule check
    yoy_appreciation_pct NUMERIC(6,2),
    population_growth_pct NUMERIC(6,2),

    -- Data source tracking
    data_source VARCHAR(50),  -- 'rentcast', 'mashvisor', 'zillow_research'
    raw_response JSONB,       -- store full API response for debugging

    UNIQUE(zip_code, snapshot_date, data_source),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Portfolio tracking: actual performance vs projections
CREATE TABLE portfolio_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    acquisition_date DATE,
    current_value_estimate NUMERIC(12,2),
    actual_monthly_rent NUMERIC(10,2),
    actual_vacancy_days INTEGER DEFAULT 0,
    actual_monthly_expenses NUMERIC(10,2),
    notes TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Rental comps pulled from APIs
CREATE TABLE rental_comps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
    comp_address VARCHAR(255),
    comp_rent NUMERIC(10,2),
    comp_bedrooms INTEGER,
    comp_bathrooms NUMERIC(3,1),
    comp_sqft INTEGER,
    distance_miles NUMERIC(5,2),
    data_source VARCHAR(50),
    fetched_at TIMESTAMP DEFAULT NOW()
);

-- Chat history for the AI chatbot
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    -- Track which deals/data the assistant referenced
    referenced_deals UUID[],
    referenced_properties UUID[],
    -- Cost tracking
    input_tokens INTEGER,
    output_tokens INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Future Scalability: Vector Embeddings

If the platform scales beyond 50 properties per user (unlikely for the MVP audience), add pgvector for RAG-based retrieval:

```sql
-- NOT IMPLEMENTED IN MVP — documented for future reference
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE deal_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deal_id UUID REFERENCES deals(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON deal_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

---

## API Endpoint Design

### Authentication
```
POST   /api/v1/auth/register        — Create new user account
POST   /api/v1/auth/login            — Get JWT access + refresh tokens
POST   /api/v1/auth/refresh          — Refresh expired access token
GET    /api/v1/auth/me               — Get current user profile
```

### Properties
```
POST   /api/v1/properties            — Add a new property (manual or auto-fill from API)
GET    /api/v1/properties             — List all user's properties (paginated, filterable)
GET    /api/v1/properties/{id}        — Get property details with comps
PUT    /api/v1/properties/{id}        — Update property details
DELETE /api/v1/properties/{id}        — Remove property
POST   /api/v1/properties/lookup      — Auto-fill property data from RentCast by address
```

### Deal Analysis
```
POST   /api/v1/deals                  — Create a new deal analysis for a property
GET    /api/v1/deals                   — List all user's deals (filterable by status, property)
GET    /api/v1/deals/{id}              — Get full deal with all calculated metrics
PUT    /api/v1/deals/{id}              — Update deal inputs (triggers metric recalculation)
DELETE /api/v1/deals/{id}              — Remove deal
POST   /api/v1/deals/{id}/scenario     — Run what-if scenario (returns metrics without saving)
GET    /api/v1/deals/{id}/projections   — Get 5/10/20/30 year amortization + equity projections
GET    /api/v1/deals/{id}/sensitivity   — Sensitivity analysis (vary one input, see metric changes)
```

### Risk Scoring
```
GET    /api/v1/deals/{id}/risk        — Get risk score and breakdown for a deal
GET    /api/v1/risk/factors            — List all risk factors and their weights
```

### Market Comparison
```
GET    /api/v1/markets/{zip_code}           — Get current market snapshot for a zip
GET    /api/v1/markets/{zip_code}/history    — Historical market trends
GET    /api/v1/markets/compare               — Compare multiple zip codes side by side
GET    /api/v1/markets/top                   — Top markets by cap rate, appreciation, etc.
POST   /api/v1/markets/refresh               — Force refresh market data from APIs
```

### Portfolio
```
GET    /api/v1/portfolio                     — Portfolio summary (total value, total cash flow, etc.)
GET    /api/v1/portfolio/performance          — Performance over time (actual vs projected)
POST   /api/v1/portfolio/{deal_id}/actuals    — Log actual monthly performance
GET    /api/v1/portfolio/export               — Export portfolio data as CSV/PDF
```

### Chatbot
```
POST   /api/v1/chat                          — Send a message, get AI response (streaming)
GET    /api/v1/chat/sessions                  — List chat sessions
GET    /api/v1/chat/sessions/{id}             — Get full chat history for a session
DELETE /api/v1/chat/sessions/{id}             — Delete a chat session
```

---

## Core Engine: Deal Calculator

The deal calculator is the heart of the application. When a user creates or updates a deal, the engine recalculates all metrics. Here's the calculation flow:

```python
# Simplified calculation logic (actual implementation will be a service class)

# Step 1: Total Cash Invested
total_cash_invested = (purchase_price * down_payment_pct / 100) + closing_costs + rehab_costs

# Step 2: Loan Details
loan_amount = purchase_price - (purchase_price * down_payment_pct / 100)
monthly_mortgage = calculate_mortgage_payment(loan_amount, interest_rate, loan_term_years)

# Step 3: Effective Gross Income (monthly)
vacancy_loss = gross_monthly_rent * vacancy_rate_pct / 100
effective_gross_income = gross_monthly_rent + other_monthly_income - vacancy_loss

# Step 4: Operating Expenses (monthly)
maintenance = gross_monthly_rent * maintenance_rate_pct / 100
management = gross_monthly_rent * management_fee_pct / 100
total_operating_expenses = (
    property_tax_monthly + insurance_monthly + maintenance +
    management + hoa_monthly + utilities_monthly
)

# Step 5: Net Operating Income (annual)
noi = (effective_gross_income - total_operating_expenses) * 12

# Step 6: Cash Flow
monthly_cash_flow = effective_gross_income - total_operating_expenses - monthly_mortgage
annual_cash_flow = monthly_cash_flow * 12

# Step 7: Key Metrics
cap_rate = noi / purchase_price
cash_on_cash = annual_cash_flow / total_cash_invested
dscr = noi / (monthly_mortgage * 12)  # Debt Service Coverage Ratio
grm = purchase_price / (gross_monthly_rent * 12)  # Gross Rent Multiplier

# Step 8: IRR (requires numpy_financial or manual implementation)
# Projects cash flows over 5/10 years including:
#   - Annual cash flow (with rent growth assumption)
#   - Equity buildup from mortgage paydown
#   - Property appreciation
#   - Sale proceeds minus selling costs at exit
```

---

## Risk Scoring Engine

The risk score is a composite 0–100 score built from weighted factors. Lower scores indicate safer investments. **This is developer-owned code — the factor selection and weights are hand-chosen and must be defensible in an interview.**

```
Risk Factor                  Weight    Scoring Criteria
────────────────────────────────────────────────────────────
DSCR (Debt Coverage)         20%       < 1.0 = high risk, > 1.5 = low risk
Cash-on-Cash Return          15%       < 4% = high risk, > 10% = low risk
Vacancy Rate vs Market       10%       Above market avg = higher risk
LTV Ratio                    10%       > 80% = higher risk
Market Appreciation Trend    10%       Declining = high risk
Rent-to-Price Ratio          10%       < 0.6% = high risk (fails 1% rule badly)
Property Age                  5%       > 50 years = maintenance risk
Days on Market               5%       > 90 days = liquidity risk
Population Growth             5%       Declining = demand risk
Concentration Risk           5%       > 50% portfolio in one zip = high risk
Expense Ratio                5%       Operating expenses > 55% of income = risk
```

Each factor produces a sub-score of 0–100, which gets multiplied by its weight. The sum gives the final risk score. The `risk_factors` JSONB column stores the breakdown so the chatbot can explain *why* a deal is risky.

---

## AI Chatbot Architecture (Direct Context Injection)

The chatbot uses direct context injection to answer questions about the user's specific deals and portfolio. All deal data is serialized into the LLM prompt — no vector database or embedding pipeline needed at this scale.

### How It Works

1. **User sends a message** like "Which of my properties has the best cash flow?"
2. **The backend queries all deals for this user** from PostgreSQL (standard SQL, no vector search).
3. **Each deal is serialized into a text summary** with all key metrics.
4. **The serialized portfolio + user question** gets sent to the LLM with a system prompt.
5. **The LLM generates a response** grounded in actual deal data, not hallucinated numbers.

### What Gets Serialized Into Context

Every time the chatbot is invoked, we query the user's deals and serialize them:

```
DEAL: "123 Elm St, Sheboygan WI 53081"
Type: Duplex | 4 bed / 2 bath | 1,850 sqft | Built 1965
Purchase: $185,000 | Down: 20% ($37,000) | Loan: $148,000 @ 7.0%
Income: $1,800/mo rent | Vacancy: 5%
Cash Flow: $342/mo | $4,104/yr
Metrics: NOI $13,320 | Cap Rate 7.2% | CoC 11.1% | DSCR 1.45 | GRM 8.6
Risk: 28/100 (Low) — strong DSCR, good CoC, stable market
IRR: 14.2% (5yr) | 12.8% (10yr)
```

At 5-50 properties, this totals ~2,000-5,000 tokens — well within Claude's context window with room for conversation history and the system prompt.

### System Prompt Structure

```
You are a real estate investment analyst assistant for the MidwestDealAnalyzer
platform. You have access to the user's complete property portfolio and deal
analyses below. Answer questions using the provided deal data. If asked to
run scenarios (e.g., "what if vacancy goes to 10%?"), recalculate the relevant
metrics using the formulas you know. Always cite specific numbers from the
user's actual deals. If you don't have enough data to answer, say so.

PORTFOLIO SUMMARY:
Total Properties: {count}
Total Monthly Cash Flow: ${total}
Average Cap Rate: {avg}%
Average Risk Score: {avg}/100

USER'S DEALS:
{serialized_deal_summaries}

CONVERSATION HISTORY:
{recent_messages}
```

### Capabilities

The chatbot can answer questions like:
- "What's my total monthly cash flow across all properties?"
- "What happens to the Elm St deal if vacancy goes up to 10%?"
- "Compare my Sheboygan duplex to the Milwaukee property."
- "Which deal has the highest risk and why?"
- "Should I refinance the Elm St property at 6.5%?"

### Cost Controls

- Token budget: ~4,000 tokens per conversation turn (input + output)
- Rate limit: 20 chat requests per minute per user (add via existing middleware or slowapi when needed; optional for first pass)
- Log token usage per session for cost tracking
- Use Ollama + Llama locally during development to avoid API costs

### Future Scalability: RAG

If a user accumulates hundreds of properties and the serialized context exceeds the context window, migrate to pgvector-based RAG:
1. Add the `deal_embeddings` table (see Future Scalability in Database Schema)
2. Embed deal summaries using the same text format above
3. On each chat message, embed the query and retrieve top-K relevant deals via cosine similarity
4. Replace full portfolio serialization with retrieved context only

This migration path is documented but not implemented in the MVP.

---

## External API Integration Layer

### Data Pipeline Design

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│ User     │────▶│ API Gateway  │────▶│  Cache Layer  │
│ Request  │     │ (rate limit) │     │  (Redis/TTL)  │
└──────────┘     └──────┬───────┘     └──────┬────────┘
                        │ cache miss          │ cache hit
                        ▼                     │
                 ┌──────────────┐             │
                 │  RentCast /  │             │
                 │  Mashvisor   │             │
                 └──────┬───────┘             │
                        │                     │
                        ▼                     ▼
                 ┌──────────────┐     ┌──────────────┐
                 │  Normalize   │────▶│  PostgreSQL   │
                 │  & Store     │     │  (snapshots)  │
                 └──────────────┘     └──────────────┘
```

### Integration Priority

**Phase 1 (MVP — RentCast Free Tier):**
- Property lookup by address (auto-fill the deal input form)
- Rent estimates (validate user's rent assumptions)
- Comparable properties
- Market statistics by zip code

**Phase 3 (Mashvisor — Paid):**
- STR vs LTR comparison
- Neighborhood-level analytics
- Investment metrics (their cap rate, CoC estimates as benchmarks)
- Historical performance data

**Phase 3 (Zillow Research Datasets — Free):**
- ZHVI (Zillow Home Value Index) for market trend overlays
- Rent index data for Midwest market comparisons
- Loaded via CSV into market_snapshots table as a batch job

### Caching Strategy

External API responses should be cached aggressively since property data doesn't change minute-to-minute:
- Property data: 30 days TTL (structural attributes rarely change)
- Rent estimates: 14 days TTL
- Value estimates: 14 days TTL
- Market stats: 30 days TTL
- Comp data: 48 hours TTL

Store the raw API response in the `raw_response` JSONB column for debugging and reprocessing without burning another API call.

### Circuit Breaker

After 3 consecutive failures to an external API within 5 minutes, stop making requests and serve only cached data for 10 minutes before retrying. This prevents cascading failures and protects API quotas.

---

## Project Directory Structure

```
real-estate-analyzer/
├── README.md
├── CLAUDE.md                    ← Claude Code briefing document
├── ARCHITECTURE.md              ← This document
├── PRD.md                       ← Product Requirements Document
├── docker-compose.yml
├── .env.example
├── .pre-commit-config.yaml      ← Black, Prettier, isort, ruff hooks
├── .github/
│   └── workflows/
│       └── ci.yml               ← GitHub Actions: test + lint + deploy
│
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI app entry point + Sentry init
│   │   ├── config.py            ← Settings via Pydantic BaseSettings
│   │   ├── database.py          ← SQLAlchemy async engine + session
│   │   │
│   │   ├── models/              ← SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── property.py
│   │   │   ├── deal.py
│   │   │   ├── market.py
│   │   │   ├── portfolio.py
│   │   │   └── chat.py
│   │   │
│   │   ├── schemas/             ← Pydantic request/response schemas
│   │   │   ├── user.py
│   │   │   ├── property.py
│   │   │   ├── deal.py
│   │   │   ├── market.py
│   │   │   └── chat.py
│   │   │
│   │   ├── routers/             ← API endpoint definitions
│   │   │   ├── auth.py
│   │   │   ├── properties.py
│   │   │   ├── deals.py
│   │   │   ├── markets.py
│   │   │   ├── portfolio.py
│   │   │   ├── risk.py
│   │   │   └── chat.py
│   │   │
│   │   ├── services/            ← Business logic layer
│   │   │   ├── deal_calculator.py    ← DEVELOPER-OWNED
│   │   │   ├── risk_engine.py        ← DEVELOPER-OWNED
│   │   │   ├── chatbot.py            ← DEVELOPER-OWNED (prompt engineering + context injection)
│   │   │   ├── market_comparator.py
│   │   │   └── portfolio_tracker.py
│   │   │
│   │   ├── integrations/        ← External API clients
│   │   │   ├── rentcast.py
│   │   │   ├── mashvisor.py
│   │   │   └── zillow_research.py
│   │   │
│   │   ├── middleware/          ← Auth, rate limiting, error handling
│   │   │   ├── auth.py
│   │   │   ├── rate_limiter.py
│   │   │   └── error_handler.py
│   │   │
│   │   └── utils/
│   │       ├── financial.py     ← DEVELOPER-OWNED: Mortgage calc, IRR, amortization
│   │       ├── cache.py
│   │       └── logging.py       ← Structured JSON logging setup
│   │
│   ├── alembic/                 ← Database migrations
│   │   └── versions/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/                  ← React Bits animated components (Phase 3-4)
│   │   │   │   ├── CountUp.tsx
│   │   │   │   ├── BlurText.tsx
│   │   │   │   ├── GradientText.tsx
│   │   │   │   ├── SplitText.tsx
│   │   │   │   ├── DecryptedText.tsx
│   │   │   │   ├── SpotlightCard.tsx
│   │   │   │   ├── TiltedCard.tsx
│   │   │   │   ├── AnimatedList.tsx
│   │   │   │   ├── AnimatedContent.tsx
│   │   │   │   ├── StarBorder.tsx
│   │   │   │   ├── ClickSpark.tsx
│   │   │   │   ├── Magnet.tsx
│   │   │   │   ├── Dock.tsx
│   │   │   │   └── Aurora.tsx
│   │   │   ├── dashboard/           ← Dashboard page components
│   │   │   ├── deals/               ← Deal forms, cards, detail views
│   │   │   ├── chat/                ← Chatbot interface components
│   │   │   ├── markets/             ← Market comparison components
│   │   │   ├── portfolio/           ← Portfolio tracking components
│   │   │   └── layout/              ← Navbar, sidebar, footer, auth layout
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/                ← API client functions
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
│
├── tests/
│   ├── conftest.py              ← Fixtures: test DB, test client, mock APIs
│   ├── test_deal_calculator.py
│   ├── test_risk_engine.py
│   ├── test_api_deals.py
│   ├── test_api_properties.py
│   ├── test_api_auth.py
│   └── test_chatbot.py
│
└── scripts/
    └── seed_market_data.py      ← Load Zillow research CSVs
```

---

## Development Phases

### Week 0: PRD + Project Infrastructure (Before Any Code)

1. Write the PRD (product spec, user flows, wireframes, design specs)
2. Create GitHub repo with README skeleton
3. Run `claude /init` to generate CLAUDE.md, then customize with project conventions
4. Set up pre-commit hooks (Black, Prettier, isort, ruff)
5. Set up GitHub Actions CI (run tests on push — passes trivially at first)
6. Set up Sentry accounts (free tier for FastAPI and React)
7. Docker Compose for local dev (FastAPI + PostgreSQL + Redis)
8. Configure `.env.example` with all required environment variables

**Deliverable:** Repo with CI/CD passing, pre-commit hooks enforcing formatting, PRD written and reviewed.

### Phase 1: Deal Calculator + Risk Scoring + Minimal Frontend (Weeks 1–3) → DEPLOY

**Week 1 — Backend Foundation:**
- Set up FastAPI project with PostgreSQL and SQLAlchemy
- Implement user auth with JWT (register, login, token refresh)
- Create database schema with Alembic migrations
- Hand-write the deal calculator service with all financial metrics
- Let Claude Code scaffold models, schemas, routers, fixtures

**Week 2 — Risk Scoring + RentCast Integration:**
- Hand-write the 11-factor risk scoring engine
- Integrate RentCast for property lookup and rent estimates (auto-fill flow)
- Build CRUD endpoints for properties and deals (calculator runs on create/update)
- Write pytest tests for calculator, risk scoring, and all API endpoints

**Week 3 — Minimal Frontend + Deploy:**
- Set up React + Vite + Tailwind project scaffold
- Build the deal input form (address + purchase price as primary inputs, advanced fields in collapsible accordion)
- Build the deal results page (display all calculated metrics + risk score)
- Wire up auth (login/register) and API calls
- **Deploy to Vercel (frontend) + Railway (backend + PostgreSQL) — NON-NEGOTIABLE**
- Add Bugbot to repo for automated PR review

**Deliverable:** A recruiter can click the URL → enter address + price → see deal analysis with risk score. API has full test coverage on business logic.

### Phase 2: AI Chatbot (Weeks 4–6)

**Week 4 — Chatbot Backend:**
- Hand-write the chatbot service: system prompt, deal serialization, context injection
- Build chat endpoint with streaming response (SSE or WebSocket)
- Add chat session management (create, list, delete sessions)
- Add token budget and per-user rate limiting

**Week 5 — Chatbot Frontend + Scenario Analysis:**
- Build React chat interface (message list, input, streaming response display)
- Implement scenario analysis: "What if vacancy goes to 10%?" triggers recalculation
- Add deal references in responses (link to the deal being discussed)

**Week 6 — Polish + Cost Tracking:**
- Add conversation history to context window (multi-turn conversations)
- Log token usage per session for cost monitoring
- Write tests for chatbot endpoint (mock LLM responses)
- Deploy updated version

**Deliverable:** Chatbot answers questions about actual deals, runs scenarios, tracks costs.

### Phase 3: Market Comparisons + Dashboard + Animations Begin (Weeks 7–9)

**Week 7 — Market Data + Dashboard + First Animations:**
- Build market data pipeline (RentCast market stats + Zillow research CSVs for Midwest)
- Implement market comparison endpoints (compare zip codes side by side)
- Build dashboard page with portfolio KPI summary
- **Install React Bits:** CountUp (KPI numbers), BlurText (section headings), SpotlightCard (deal cards)
- Seed Midwest market data for Wisconsin, Illinois, Michigan, Minnesota

**Week 8 — Comparison Pages + More Animations:**
- Build market comparison page with side-by-side panels
- Enhance deal detail page with charts (amortization, cash flow projections, equity buildup)
- **Install React Bits:** AnimatedList (chat messages), AnimatedContent (page transitions), StarBorder (best/worst deals)

**Week 9 — Integration + Testing:**
- Mashvisor integration for deeper investment analytics (if budget allows)
- Cross-feature testing: deals → risk scores → chat about them → compare markets
- Deploy updated version

**Deliverable:** Compare zip codes, see risk breakdowns per deal, dashboard with animated KPIs.

### Phase 4: Portfolio Tracking + Polish (Weeks 10–12)

**Week 10 — Portfolio Features + Micro-interactions:**
- Portfolio tracking: log actual monthly performance vs projections
- Portfolio summary page with aggregated metrics
- **Install React Bits:** ClickSpark (action buttons), DecryptedText/SplitText (chatbot numbers), GradientText (risk labels)

**Week 11 — Auth Polish + Final Animations:**
- **Install React Bits:** Aurora/Beams (auth page backgrounds), Dock (optional navigation), Magnet (optional CTA buttons)
- Responsive design pass across all pages
- Export portfolio data as CSV

**Week 12 — Final Polish + Documentation:**
- Add screenshot/GIF to README
- Write "What I Built vs. What Claude Code Built" section
- Architecture Decision Records
- Performance optimization pass
- Final deploy

**Deliverable:** Fully deployed application with polished UI, complete documentation, and honest AI-usage transparency.

---

## Deployment Strategy

### Infrastructure

Production (e.g. Railway) uses **PostgreSQL** for the database. SQLite is for local development only and is not used or supported for production or Railway deployments.

| Service | Provider | Cost | Purpose |
|---------|----------|------|---------|
| Frontend | Vercel | Free tier | React app, instant deploys from GitHub |
| Backend | Railway | ~$5-10/month | FastAPI; must use PostgreSQL (add Postgres service, set DATABASE_URL) |
| PostgreSQL | Railway (same project) | Included | Production database; required for backend on Railway |
| Redis | Railway add-on | Included | Caching layer |
| Error Tracking | Sentry | Free tier | Exception monitoring |
| PR Review | Bugbot | Free/cheap | Automated code review |
| Domain | TBD | ~$12/year | midwestdealanalyzer.com or similar |

### CI/CD Pipeline

```
Developer pushes to feature branch
    │
    ▼
GitHub Actions runs:
    ├── ruff check + black --check (Python lint)
    ├── eslint (React lint)
    ├── pytest with coverage report
    └── frontend build check
    │
    ▼
Bugbot reviews PR automatically
    │
    ▼
Merge to main
    │
    ├──▶ Vercel auto-deploys frontend
    └──▶ Railway auto-deploys backend
```

### Environment Variables

Production (Railway) must use a **PostgreSQL** URL for `DATABASE_URL`. SQLite is for local dev only.

```
# Database (production = PostgreSQL; SQLite only for local dev)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# External APIs
RENTCAST_API_KEY=...
MASHVISOR_API_KEY=...        # Phase 3
ANTHROPIC_API_KEY=...        # Phase 2

# Auth
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Caching
REDIS_URL=redis://localhost:6379

# Monitoring
SENTRY_DSN_BACKEND=...
SENTRY_DSN_FRONTEND=...

# App
ENVIRONMENT=development       # development | staging | production
CORS_ORIGINS=http://localhost:3000,https://midwestdealanalyzer.com
```
