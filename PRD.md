# PRD — MidwestDealAnalyzer

**Product Requirements Document**
**Version:** 1.0
**Date:** February 18, 2026
**Author:** Ivan Flores
**Status:** Draft — Review before Phase 1 begins

---

## 1. Product Vision

**One-liner:** A full-stack real estate investment analyzer for Wisconsin rental markets that turns a property address and purchase price into a comprehensive deal analysis with AI-powered insights.

**Why this exists:** Ivan is actively hunting duplexes in Sheboygan and Milwaukee. The existing tools (BiggerPockets calculators, spreadsheets, Mashvisor's consumer product) are either too generic, too manual, or too expensive. This tool solves a real problem — evaluating whether a specific property is a good rental investment in a specific Midwest market — while simultaneously demonstrating production-quality full-stack engineering for job applications.

**What makes it different from a generic calculator:**
- Midwest-specific defaults and market data (Wisconsin vacancy rates, Sheboygan tax ranges, Milwaukee rent comps)
- 11-factor risk scoring algorithm that goes beyond simple cash flow
- AI chatbot that reasons about YOUR deals, not generic advice
- Auto-fill from APIs — enter an address and get a full analysis without manual data entry
- Honest about the role of AI in its construction (README transparency)

---

## 2. Target Users

### Primary: Ivan (the developer)
- 23-year-old aspiring real estate investor in Sheboygan, WI
- Evaluating duplexes in the $150K–$280K range
- Wants to quickly screen properties from Zillow/Realtor.com listings
- Needs to compare multiple deals and understand risk before making offers
- Has basic real estate knowledge but wants data-driven confidence

### Secondary: Technical Recruiters & Hiring Managers
- Spending 30–60 seconds evaluating the live demo
- Looking for: deployed URL works, clean UI, professional engineering practices
- Need to see something impressive in under 10 seconds
- Will skim the README for architecture decisions and AI transparency

### Tertiary: Other Midwest Rental Investors (future)
- Small-scale landlords evaluating 1–10 properties
- Want a free or cheap alternative to paid analysis tools
- Need Midwest-specific data, not national averages

---

## 3. Problem Statement

Evaluating a rental property investment currently requires:
1. Finding the listing (Zillow, Realtor.com, MLS)
2. Manually entering 15+ data points into a spreadsheet or calculator
3. Researching market-level data (vacancy rates, rent comps, appreciation trends) separately
4. Running multiple scenarios by hand (what if vacancy is 8%? what if rates drop?)
5. Comparing deals by switching between tabs and spreadsheets
6. No risk assessment beyond gut feeling

**This tool collapses steps 2–6 into one flow:** enter address + price → get everything automatically → ask the AI questions → save and compare.

---

## 4. Core User Journeys

### Journey 1: Analyze a New Property (the primary loop)

This is the journey that must work flawlessly from Phase 1. Everything else builds on top of it.

```
Step 1: LAND
    User arrives at the app (logged in or not)
    Sees a clean interface with a prominent search/input area
    [If first visit] → "Try with sample data" button loads a Sheboygan duplex example

Step 2: INPUT
    User enters: Street address + City/State (or just full address)
    User enters: Asking/purchase price
    Clicks "Analyze Deal"

Step 3: AUTO-FILL (happens in 2-5 seconds)
    Backend calls RentCast with the address
    Returns: bedrooms, bathrooms, sqft, year built, property type, tax records
    Returns: rent estimate, comparable rentals nearby
    Pre-fills all form fields with API data + Midwest defaults:
        - Financing: 20% down, 7.0% rate, 30-year fixed
        - Expenses: insurance $120/mo, maintenance 5%, management 10%
        - Vacancy: 5% (Wisconsin average)
    User sees the pre-filled values with source labels

Step 4: REVIEW (optional)
    Advanced users expand the accordion to adjust pre-filled values
    Each field shows its source: "From RentCast", "Wisconsin avg", "Standard terms"
    Most users skip this and go straight to results

Step 5: RESULTS
    Full deal analysis page appears:
        - Hero section: Monthly cash flow (large), risk score badge
        - Key metrics row: NOI, cap rate, cash-on-cash, DSCR, GRM
        - Financing summary: loan amount, monthly mortgage, total cash needed
        - Expense breakdown: itemized monthly costs
        - Risk score: 0-100 with color-coded label + factor breakdown
        - Projections: 5-year and 10-year IRR, equity buildup chart
    All financial numbers animate from 0 to value (CountUp, Phase 3)
    Risk score has color-coded gradient label (Phase 3)

Step 6: SAVE
    User clicks "Save to Portfolio" (requires login)
    If not logged in → redirect to register/login → return to results
    Deal appears in their portfolio for future reference
```

### Journey 2: Chat About a Deal (Phase 2)

```
Step 1: User is viewing a deal analysis (or their portfolio)
Step 2: Clicks "Ask AI" button → chat panel opens
Step 3: Types a question: "What happens if vacancy goes to 10%?"
Step 4: Chatbot loads all user's deals into context
Step 5: Responds with recalculated metrics and explanation
Step 6: User follows up: "Compare this to my Milwaukee property"
Step 7: Chatbot references both deals with specific numbers
```

### Journey 3: Compare Markets (Phase 3)

```
Step 1: User navigates to Markets page
Step 2: Enters two zip codes (e.g., 53081 Sheboygan vs 53202 Milwaukee)
Step 3: Side-by-side comparison appears:
    - Median home value, median rent, cap rate, vacancy, appreciation, population
Step 4: User sees which market has better fundamentals for their strategy
```

### Journey 4: Track Portfolio Performance (Phase 4)

```
Step 1: User has multiple saved deals
Step 2: Dashboard shows aggregate metrics (total cash flow, avg cap rate, total equity)
Step 3: For acquired properties, user logs actual monthly income/expenses
Step 4: Dashboard shows actual vs projected performance over time
```

---

## 5. Feature Requirements by Phase

### Phase 1 — MVP (Weeks 1–3) ✦ MUST DEPLOY

**Backend:**
| Feature | Priority | Description |
|---------|----------|-------------|
| User auth | P0 | Register, login, JWT tokens, refresh flow |
| Property CRUD | P0 | Create, read, update, delete properties |
| Deal CRUD | P0 | Create, read, update, delete deal analyses |
| Deal calculator | P0 | All financial metrics: NOI, cap rate, CoC, DSCR, GRM, IRR, equity buildup |
| Risk scoring | P0 | 11-factor composite score (0-100) with factor breakdown |
| RentCast auto-fill | P0 | Property lookup by address, rent estimates, tax data |
| RentCast caching | P0 | Cache responses 14-30 days to protect 50 calls/month |
| Input validation | P0 | Reject invalid financial inputs with clear error messages |
| Data isolation | P0 | Users can only see their own data |
| Rate limiting | P1 | Per-user limits on API endpoints |
| Health check | P1 | `/health` endpoint for monitoring |

**Frontend:**
| Feature | Priority | Description |
|---------|----------|-------------|
| Auth pages | P0 | Login and register forms |
| Deal input form | P0 | Address + price primary, advanced inputs in accordion |
| Deal results page | P0 | All metrics displayed clearly with risk score |
| Property lookup | P0 | Address input triggers RentCast auto-fill |
| Saved deals list | P1 | Simple list of user's saved deal analyses |
| Responsive layout | P1 | Works on desktop and tablet (mobile is stretch) |
| Loading states | P1 | Skeleton/spinner while API calls resolve |
| Error states | P1 | Clear messages when things fail |

**Infrastructure:**
| Feature | Priority | Description |
|---------|----------|-------------|
| Deploy to Vercel + Railway | P0 | Live URL accessible to recruiters |
| CI/CD pipeline | P0 | Tests run on every push (already set up in Week 0) |
| Sentry error tracking | P1 | Catch unhandled exceptions in production |
| Structured logging | P1 | JSON logs on API requests and external calls |

### Phase 2 — AI Chatbot (Weeks 4–6)

| Feature | Priority | Description |
|---------|----------|-------------|
| Chat endpoint (streaming) | P0 | SSE or WebSocket for real-time responses |
| Deal context injection | P0 | Serialize all user deals into LLM prompt |
| Chat UI | P0 | Message list, input, streaming display |
| Session management | P0 | Create, list, delete chat sessions |
| Scenario analysis | P1 | "What if X?" triggers recalculation in response |
| Token budget | P1 | Cap at ~4000 tokens per turn |
| Cost tracking | P1 | Log token usage per session |
| Conversation history | P2 | Multi-turn context within a session |

### Phase 3 — Market Comparisons + Dashboard (Weeks 7–9)

| Feature | Priority | Description |
|---------|----------|-------------|
| Market data pipeline | P0 | RentCast market stats + Zillow CSV import |
| Market comparison page | P0 | Side-by-side zip code comparison |
| Dashboard | P0 | Portfolio KPI summary with deal cards |
| React Bits animations | P1 | CountUp, BlurText, SpotlightCard, AnimatedList |
| Charts | P1 | Amortization, cash flow projections, equity buildup |
| Mashvisor integration | P2 | Deeper analytics if budget allows |

### Phase 4 — Portfolio Tracking + Polish (Weeks 10–12)

| Feature | Priority | Description |
|---------|----------|-------------|
| Portfolio tracking | P0 | Log actual monthly performance |
| Actual vs projected | P0 | Compare real numbers to deal projections |
| Export (CSV) | P1 | Download portfolio data |
| Remaining React Bits | P1 | ClickSpark, GradientText, Aurora, Dock |
| Responsive polish | P1 | Full mobile support |
| README finalization | P0 | Screenshots, GIF, final "What I Built" section |

---

## 6. Screen Specifications

### Screen 1: Landing / Deal Input (the first thing anyone sees)

**URL:** `/` (unauthenticated) or `/dashboard` (authenticated)

**Purpose:** Get the user to a deal analysis as fast as possible. This screen exists to serve the 10-second rule.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  NAVBAR: Logo / MidwestDealAnalyzer        [Login] [Register]│
├─────────────────────────────────────────────────────────────┤
│                                                              │
│          Analyze Your Next Rental Investment                 │
│          Midwest-focused deal analysis with AI insights      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  🏠  Enter property address                         │    │
│  │      ___________________________________________    │    │
│  │                                                     │    │
│  │  💰  Purchase price                                 │    │
│  │      $ _______________                              │    │
│  │                                                     │    │
│  │           [ Analyze Deal ]                          │    │
│  │                                                     │    │
│  │  Or: [Try with sample data →]                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ 11-Factor│  │ AI Chat  │  │ Market   │                  │
│  │ Risk     │  │ About    │  │ Compare  │                  │
│  │ Scoring  │  │ Your     │  │ WI Zip   │                  │
│  │          │  │ Deals    │  │ Codes    │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│  Three feature cards below the fold (brief descriptions)     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Behavior:**
- Address field: Free text input. On submit, backend parses and sends to RentCast.
- Purchase price: Numeric input with `$` prefix, comma formatting as user types.
- "Analyze Deal" button: Triggers the full flow (lookup → calculate → display results).
- "Try with sample data": Pre-fills with 1847 N 21st St, Sheboygan WI, $195,000 (or a similar realistic Sheboygan duplex). Does NOT require login. Shows results immediately.
- Feature cards: Static content explaining the three differentiators. Scroll down to see them.
- If user is logged in, this becomes the dashboard (Phase 3) with the input form still prominent.

**Loading state:** After clicking "Analyze Deal", show a skeleton screen with the results layout but placeholder shimmer bars. Text below: "Looking up property details..." → "Calculating metrics..." → "Scoring risk..."

**Error states:**
- Address not found: "We couldn't find that property. Check the address and try again."
- RentCast quota exhausted: "Property lookup is temporarily unavailable. You can still enter details manually." → expand the advanced form with all fields editable.
- Network error: "Something went wrong. Please try again."

### Screen 2: Deal Results (the money screen)

**URL:** `/deals/:id` or `/deals/preview` (unsaved analysis)

**Purpose:** Show the complete deal analysis. This is what the recruiter sees after 10 seconds. It must look impressive and communicate financial competence.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  NAVBAR: Logo    Deals  Markets  Portfolio  Chat    [User ▾]│
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1847 N 21st St, Sheboygan WI 53081                        │
│  Duplex · 4 bed / 2 bath · 1,850 sqft · Built 1965         │
│  [Save to Portfolio]  [Edit Inputs]  [Ask AI]               │
│                                                              │
│  ┌─────────────────┐  ┌─────────────────────────────────┐  │
│  │  MONTHLY CASH   │  │  RISK SCORE                     │  │
│  │  FLOW           │  │                                 │  │
│  │  $342           │  │  28 / 100                       │  │
│  │  (large, green) │  │  ● Low Risk (green badge)       │  │
│  └─────────────────┘  └─────────────────────────────────┘  │
│                                                              │
│  ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐       │
│  │ NOI    ││Cap Rate││  CoC   ││ DSCR   ││  GRM   │       │
│  │$13,320 ││ 7.2%   ││ 11.1%  ││ 1.45   ││ 8.6    │       │
│  └────────┘└────────┘└────────┘└────────┘└────────┘       │
│                                                              │
│  ── Financing Summary ──────────────────────────────────    │
│  Purchase Price    $185,000  │  Loan Amount    $148,000     │
│  Down Payment      $37,000   │  Monthly Mortgage $985       │
│  Closing Costs     $5,550    │  Interest Rate   7.0%        │
│  Total Cash In     $42,550   │  Loan Term       30 years    │
│                                                              │
│  ── Monthly Expense Breakdown ──────────────────────────    │
│  Gross Rent         $1,800   │  Vacancy (5%)     -$90       │
│  Other Income       $0       │  Property Tax     -$280      │
│  ─────────────────────────   │  Insurance        -$120      │
│  Effective Income   $1,710   │  Maintenance (5%) -$90       │
│                              │  Management (10%) -$180      │
│                              │  ─────────────────────────   │
│                              │  Total Expenses   -$760      │
│                              │  Mortgage         -$985      │
│                              │  ─────────────────────────   │
│                              │  NET CASH FLOW    $342/mo    │
│                                                              │
│  ── Risk Score Breakdown ───────────────────────────────    │
│  DSCR Coverage        ████████░░  82/100 (Low Risk)         │
│  Cash-on-Cash Return  ███████░░░  75/100 (Low Risk)         │
│  Vacancy vs Market    ████████░░  80/100 (Low Risk)         │
│  LTV Ratio            ██████░░░░  60/100 (Moderate)         │
│  Market Appreciation  ███████░░░  72/100 (Low Risk)         │
│  Rent-to-Price Ratio  █████████░  88/100 (Low Risk)         │
│  Property Age         ████░░░░░░  40/100 (Moderate)         │
│  Days on Market       ███████░░░  70/100 (Low Risk)         │
│  Population Growth    ██████░░░░  65/100 (Low Risk)         │
│  Concentration Risk   ██████████  100/100 (N/A - first)     │
│  Expense Ratio        ███████░░░  72/100 (Low Risk)         │
│  ──────────────────────────────────────────────             │
│  COMPOSITE SCORE: 28/100 — Low Risk                         │
│                                                              │
│  ── Projections ────────────────────────────────────────    │
│  [5-Year IRR: 14.2%]  [10-Year IRR: 12.8%]                 │
│  [Equity buildup chart placeholder — Recharts, Phase 3]     │
│                                                              │
│  ── Advanced: Edit Inputs (collapsed accordion) ────────    │
│  [Expand to see and modify all pre-filled values]           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Behavior:**
- All financial numbers display with proper formatting ($1,800.00, 7.2%, 1.45x).
- Monthly cash flow: Green if positive, red if negative. This is the hero number.
- Risk score badge: Green (0-33 "Low Risk"), Yellow (34-66 "Moderate Risk"), Red (67-100 "High Risk").
- Risk factor bars: Visual progress bars showing each factor's contribution. Hoverable for explanation tooltip.
- "Save to Portfolio": If not logged in, prompts login first, then saves. If logged in, saves immediately.
- "Edit Inputs": Scrolls to / expands the advanced accordion at the bottom. Changing any value triggers immediate recalculation (debounced, 500ms).
- "Ask AI": Opens chat panel (Phase 2 — hidden in Phase 1).
- Charts: Placeholder text in Phase 1, replaced with Recharts in Phase 3.

### Screen 3: Auth Pages (Login / Register)

**URL:** `/login`, `/register`

**Purpose:** Minimal friction to save deals. These must look polished because they're the first "real" interaction.

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  [Aurora animated gradient background — Phase 4]            │
│                                                              │
│              MidwestDealAnalyzer                             │
│                                                              │
│         ┌──────────────────────────────┐                    │
│         │                              │                    │
│         │   Email                      │                    │
│         │   ________________________   │                    │
│         │                              │                    │
│         │   Password                   │                    │
│         │   ________________________   │                    │
│         │                              │                    │
│         │   [Full Name — register only] │                   │
│         │                              │                    │
│         │        [ Log In ]            │                    │
│         │                              │                    │
│         │   Don't have an account?     │                    │
│         │   Register →                 │                    │
│         │                              │                    │
│         └──────────────────────────────┘                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Behavior:**
- Phase 1: Simple white card on neutral background. Clean and functional.
- Phase 4: Aurora animated gradient background added behind the card.
- After login: Redirect to the page user came from (or dashboard if direct visit).
- After register: Auto-login and redirect.
- Validation: Email format, password minimum 8 characters. Show errors inline.

### Screen 4: Chat Interface (Phase 2)

**URL:** `/chat` or slide-over panel from any deal page

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  NAVBAR                                                      │
├───────────────────┬─────────────────────────────────────────┤
│  Chat Sessions    │                                         │
│  ──────────────   │  Portfolio Overview                     │
│  ● Elm St deal    │  ──────────────────────                 │
│  ● General Q&A    │  You: What happens to my Elm St deal    │
│  ● Comparing...   │  if vacancy goes up to 10%?             │
│  [+ New Chat]     │                                         │
│                   │  AI: If vacancy increases to 10%, your  │
│                   │  monthly cash flow drops from $342 to   │
│                   │  $252. Your DSCR falls to 1.32, still   │
│                   │  above the 1.25 lender threshold. Your  │
│                   │  cash-on-cash return drops from 11.1%   │
│                   │  to 7.1%. The risk score increases from │
│                   │  28 to 37 (Moderate Risk). This deal    │
│                   │  still cash-flows positively even at    │
│                   │  double the market vacancy rate.        │
│                   │                                         │
│                   │  You: ___________________________       │
│                   │                         [Send]          │
│                   │                                         │
└───────────────────┴─────────────────────────────────────────┘
```

### Screen 5: Dashboard (Phase 3)

**URL:** `/dashboard`

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  NAVBAR                                                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Portfolio Overview                                          │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ Total    │ │ Avg Cap  │ │ Total    │ │ Active   │      │
│  │ Cash Flow│ │ Rate     │ │ Equity   │ │ Deals    │      │
│  │ $1,247/mo│ │ 7.8%     │ │ $84,200  │ │ 4        │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
│  [CountUp animation on all numbers — Phase 3]               │
│                                                              │
│  ┌─── Analyze New Property ─────────────────────────┐       │
│  │  Address: ________________  Price: $________      │       │
│  │                                  [Analyze Deal]   │       │
│  └───────────────────────────────────────────────────┘       │
│                                                              │
│  Your Deals                                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │★ 1847 N 21st │ │ 2301 W Vliet │ │ 415 Erie Ave │        │
│  │  Sheboygan   │ │  Milwaukee   │ │  Sheboygan   │        │
│  │  $342/mo     │ │  $289/mo     │ │  $415/mo     │        │
│  │  Risk: 28    │ │  Risk: 41    │ │  Risk: 22    │        │
│  │  CoC: 11.1%  │ │  CoC: 8.4%   │ │  CoC: 13.2%  │        │
│  │  [View Deal] │ │  [View Deal] │ │  [View Deal] │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  [SpotlightCard on each — Phase 3]                          │
│  [StarBorder on best CoC (green) + highest risk (red)]      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Design System

### Color Palette

This is a financial analysis tool. The palette communicates trust, precision, and professionalism — not startup energy or gaming vibes.

**Primary Colors:**
| Name | Hex | Usage |
|------|-----|-------|
| Navy | `#1B2A4A` | Navbar, headings, primary text |
| Slate | `#334155` | Secondary text, card headers |
| White | `#FFFFFF` | Card backgrounds, page background |
| Off-White | `#F8FAFC` | Page background (alternative), table stripes |

**Accent Colors:**
| Name | Hex | Usage |
|------|-----|-------|
| Blue | `#2563EB` | Primary buttons, links, active states |
| Blue Light | `#3B82F6` | Hover states, secondary accents |
| Blue Subtle | `#EFF6FF` | Selected row highlight, info badges |

**Semantic Colors (financial):**
| Name | Hex | Usage |
|------|-----|-------|
| Green | `#16A34A` | Positive cash flow, low risk, good metrics |
| Green Light | `#DCFCE7` | Green background badge (Low Risk) |
| Yellow | `#CA8A04` | Moderate risk, caution metrics |
| Yellow Light | `#FEF9C3` | Yellow background badge (Moderate Risk) |
| Red | `#DC2626` | Negative cash flow, high risk, bad metrics |
| Red Light | `#FEE2E2` | Red background badge (High Risk) |

**Neutral (UI chrome):**
| Name | Hex | Usage |
|------|-----|-------|
| Border | `#E2E8F0` | Card borders, dividers, input borders |
| Muted | `#94A3B8` | Placeholder text, disabled states, labels |
| Background | `#F1F5F9` | Section backgrounds, sidebar |

**Rule:** Green and red are reserved exclusively for financial meaning (positive/negative). Never use green for a generic "success" toast or red for a generic "error" — use blue for informational states and a muted red for form validation errors.

### Typography

| Element | Font | Weight | Size | Color |
|---------|------|--------|------|-------|
| H1 (page titles) | Inter | 700 (Bold) | 28px / 1.75rem | Navy |
| H2 (section heads) | Inter | 600 (Semibold) | 22px / 1.375rem | Navy |
| H3 (card titles) | Inter | 600 (Semibold) | 18px / 1.125rem | Slate |
| Body text | Inter | 400 (Regular) | 16px / 1rem | Slate |
| Small/labels | Inter | 500 (Medium) | 14px / 0.875rem | Muted |
| Financial numbers | JetBrains Mono | 600 (Semibold) | Varies | Context-dependent |
| KPI hero numbers | JetBrains Mono | 700 (Bold) | 36px / 2.25rem | Green or Red |

**Why monospace for numbers:** Financial figures must align visually in tables and comparison views. Proportional fonts make "$1,234" and "$9,876" different widths, which looks sloppy in a data-heavy dashboard. JetBrains Mono is clean, modern, and free — it doesn't feel like a terminal.

**Font loading:** Import Inter from Google Fonts (or bundle). Import JetBrains Mono from Google Fonts. Use `font-display: swap` to prevent layout shift.

### Spacing & Layout

- **Base unit:** 4px (Tailwind default). All spacing is multiples of 4px.
- **Card padding:** 24px (p-6)
- **Section margin:** 32px (my-8) between major sections
- **Grid:** 12-column on desktop, collapses to single column on mobile
- **Max content width:** 1280px (max-w-7xl), centered
- **Card border radius:** 12px (rounded-xl)
- **Card shadow:** `shadow-sm` default, `shadow-md` on hover
- **Dashboard KPI cards:** Equal width in a 4-column grid (lg:grid-cols-4)
- **Deal cards:** 3-column grid (lg:grid-cols-3), 2-column on tablet, 1 on mobile

### Component Patterns

**Buttons:**
- Primary: Blue background, white text, rounded-lg, py-2.5 px-5. Hover: Blue Light.
- Secondary: White background, blue border, blue text. Hover: Blue Subtle background.
- Danger: Red background, white text. Used only for delete actions.
- All buttons: 16px font, medium weight, min-width 120px for consistency.

**Cards:**
- White background, Border color border, rounded-xl, shadow-sm.
- On hover: shadow-md + slight scale(1.01) transition (200ms ease).
- SpotlightCard wrapper replaces the hover shadow in Phase 3.

**Form inputs:**
- Border color border, rounded-lg, py-2.5 px-4, placeholder in Muted.
- Focus: ring-2 ring-Blue, border-Blue.
- Error: ring-2 ring-Red, error text below in Red, 14px.
- Financial inputs: Right-aligned text, monospace font, `$` prefix inside the input.

**Badges (risk score):**
- Low Risk (0-33): Green text on Green Light background, rounded-full, px-3 py-1.
- Moderate Risk (34-66): Yellow text on Yellow Light background.
- High Risk (67-100): Red text on Red Light background.

**Data tables:**
- Striped rows (alternating White / Off-White).
- Header row: Slate background, white text, sticky on scroll.
- Financial numbers: Right-aligned, monospace.
- Sortable columns: Arrow indicator, click to sort.

### Mood & Aesthetic

**Think:** Clean Bloomberg terminal meets a modern SaaS dashboard. Data-forward, not decoration-forward. Every pixel serves the numbers.

**NOT:** Startup landing page (too much whitespace, too few numbers). Not a gaming dashboard (too dark, too many gradients). Not a spreadsheet (too dense, no visual hierarchy).

**Reference touchstones:**
- Stripe Dashboard (clean layout, clear hierarchy, professional)
- Linear (modern feel, subtle animations, functional beauty)
- Bloomberg Terminal (data density done right, monospace numbers)
- Notion (typography, spacing, cards)

---

## 8. Technical Constraints

These are non-negotiable architectural decisions. See ARCHITECTURE.md for full rationale.

| Constraint | Decision | Rationale |
|-----------|----------|-----------|
| Backend framework | FastAPI | Async for external API calls, auto-generated docs, common in target roles |
| Database | PostgreSQL 16 | Relational data model, industry standard for financial data |
| ORM | SQLAlchemy 2.0 (async) | Full control, common in backend roles |
| Frontend | React 18 + Vite + TypeScript | Career roadmap alignment, Vercel-native |
| Styling | Tailwind CSS | Utility-first, fast iteration, consistent spacing |
| Chatbot approach | Direct context injection | Data volume fits in context window, RAG is premature |
| Primary API | RentCast (free tier) | 50 calls/month, commercial use allowed |
| Auth | JWT (access + refresh tokens) | Stateless, standard pattern |
| Backend deploy | Railway | Managed PostgreSQL included, supports FastAPI |
| Frontend deploy | Vercel | Free tier, React-native, instant deploys |
| Python formatting | Black + isort + ruff | Enforced via pre-commit hooks |
| JS/TS formatting | Prettier + ESLint | Enforced via pre-commit hooks |
| Testing | pytest from day one | 80%+ coverage on business logic |
| Financial math | Decimal, never float | Non-negotiable for accuracy |

---

## 9. Security Requirements

| Requirement | Implementation | Phase |
|-------------|---------------|-------|
| Password hashing | bcrypt via passlib | 1 |
| JWT tokens | 30-min access, 7-day refresh, revocable | 1 |
| Data isolation | Every query filters by user_id | 1 |
| Input validation | Pydantic schemas + explicit financial range checks | 1 |
| API keys server-side only | Frontend never calls external APIs directly | 1 |
| Rate limiting (general) | 100 req/min per user via slowapi | 1 |
| Rate limiting (API proxy) | 10 req/min per user on property lookup | 1 |
| Rate limiting (chat) | 20 req/min per user | 2 |
| Token budget | ~4000 tokens per chat turn | 2 |
| CORS | Whitelist production + localhost origins only | 1 |
| No secrets in code | All keys in env vars, .env in .gitignore | 0 |
| Error sanitization | Never leak stack traces or SQL to client | 1 |

---

## 10. Success Metrics

### The Recruiter Test (most important)
- **10-second demo:** Recruiter clicks URL → enters address + price → sees deal analysis. Under 10 seconds total. If this fails, nothing else matters.
- **Professional impression:** The results page looks like a real financial tool, not a homework assignment.
- **README scan:** Recruiter spends 30 seconds on README, sees: live demo link, architecture diagram, "What I Built" section, and closes the tab impressed.

### Technical Quality Metrics
- **Test coverage:** 80%+ on deal calculator and risk scoring engine
- **CI/CD green:** Every merge to main passes lint + tests + build
- **Error rate:** < 1% of API requests result in 5xx errors (via Sentry)
- **API response time:** Deal analysis completes in < 3 seconds (including RentCast lookup, or < 500ms from cache)
- **Zero data leaks:** No test should be able to access another user's data

### Product Metrics (if tracking, nice-to-have)
- Deals analyzed per session
- Chat messages per session
- Return visits (do users come back to compare more properties?)

---

## 11. Claude Code Boundaries

This section is duplicated from CLAUDE.md for completeness. The PRD must specify what the AI assistant builds vs. what the developer builds, because this distinction is the project's core differentiator.

### Developer writes by hand (defensible in interview):
- `deal_calculator.py` — All financial calculation logic
- `risk_engine.py` — 11-factor risk scoring with chosen weights
- `chatbot.py` — LLM prompt engineering, context injection, response handling
- `financial.py` — Mortgage math, IRR, amortization schedule
- Database schema design decisions
- API endpoint design decisions
- Risk factor selection and weight justification

### Claude Code scaffolds (plumbing):
- SQLAlchemy model definitions
- Pydantic request/response schemas
- FastAPI route handlers (CRUD operations)
- Authentication middleware
- External API client wrappers
- React components and pages
- Test fixtures and scaffolding
- CI/CD and deployment configuration

### The interview line:
> "I used AI tools for scaffolding and plumbing — route definitions, model classes, React layout. The deal calculation engine, risk scoring algorithm, and chatbot prompt engineering are entirely mine. I chose the 11 risk factors. I chose the weights. I can derive every financial formula on a whiteboard. Here's why DSCR gets 20% weight and property age gets 5%..."

---

## 12. Explicit Non-Goals (Out of Scope)

These are features someone might reasonably expect but that we are intentionally NOT building:

| Feature | Why not |
|---------|---------|
| Mobile app (native) | Web app is sufficient for portfolio demo and personal use |
| Multi-user teams / shared portfolios | Single-user tool. Multi-tenancy adds complexity without portfolio value |
| Real-time MLS feed | Requires MLS access agreements. Users paste addresses from Zillow manually |
| Property photo gallery | RentCast doesn't return photos. Address + metrics is enough |
| Automated deal alerts | Requires background jobs + notification system. Phase 5+ if ever |
| PDF report generation | Nice-to-have but not MVP. CSV export covers the export need |
| STR (short-term rental) analysis | LTR only for MVP. STR data requires AirDNA or Mashvisor paid tier |
| Payment processing / subscription | This is a free tool. No monetization needed for portfolio demo |
| Admin panel | Single user, no admin needs |
| Internationalization | English only, USD only, US markets only |
| pgvector / RAG chatbot | Direct context injection handles the scale. Documented as future path |

---

## 13. Open Questions

All Phase 1 open questions have been resolved. See OPEN_QUESTIONS.md for decision log.

| # | Question | Status | Decision |
|---|----------|--------|----------|
| 1 | Domain name — midwestdealanalyzer.com? .dev? .app? | Resolved | Deploy to *.vercel.app subdomain for Phase 1. Buy custom domain later. |
| 2 | RentCast free tier — is 50 calls/month enough for dev + demo? | Resolved | Free tier (50 calls/month) is sufficient. Mock all calls in dev/test. Cache 30 days in production. |
| 3 | Sample data property — which specific Sheboygan address for "Try with sample data"? | Resolved | 1515 N 7th St, Sheboygan WI 53081. Duplex, $220,000, 5 bed / 2 bath, 2,330 sqft, built 1900. Hard-code this for the "Try with sample data" button. |
| 4 | Chart library — Recharts vs Chart.js? | Resolved | Recharts. React-native, JSX composable, works with Tailwind. |
| 5 | Auth — support Google OAuth in addition to email/password? | Resolved | Email/password only. No Google OAuth for MVP. |
| 6 | Chat streaming — SSE vs WebSocket? | Resolved | SSE (Server-Sent Events). Simpler than WebSocket, sufficient for one-direction streaming. |
| 7 | React Bits Dock navigation — use it or go with standard sidebar? | Resolved | Standard sidebar. No React Bits Dock. |

---

*This PRD is a living document. Update the "Open Questions" table as decisions are made. Update phase priorities if scope changes. The feature tables are the source of truth for what gets built and when.*
