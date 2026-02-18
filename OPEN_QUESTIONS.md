# Open Questions Tracker

This file tracks open questions from the PRD that need decisions before or during development phases.

**Last Updated:** February 18, 2026  
**Status:** All Phase 1 questions resolved ✅

---

## Active Questions

| # | Question | Status | Decision | Notes |
|---|----------|--------|----------|-------|
| 1 | Domain name — midwestdealanalyzer.com? .dev? .app? | Resolved | Deploy to *.vercel.app subdomain for Phase 1. Buy custom domain later. | Use Vercel default subdomain initially |
| 2 | RentCast free tier — is 50 calls/month enough for dev + demo? | Resolved | Free tier (50 calls/month) is sufficient. Mock all calls in dev/test. Cache 30 days in production. | Aggressive caching strategy protects quota |
| 3 | Sample data property — which specific Sheboygan address for "Try with sample data"? | Resolved | 1515 N 7th St, Sheboygan WI 53081. Duplex, $220,000, 5 bed / 2 bath, 2,330 sqft, built 1900. Hard-code this for the "Try with sample data" button. | Real Sheboygan duplex property |
| 4 | Chart library — Recharts vs Chart.js? | Resolved | Recharts. React-native, JSX composable, works with Tailwind. | Better React integration |
| 5 | Auth — support Google OAuth in addition to email/password? | Resolved | Email/password only. No Google OAuth for MVP. | Simpler implementation, sufficient for MVP |
| 6 | Chat streaming — SSE vs WebSocket? | Resolved | SSE (Server-Sent Events). Simpler than WebSocket, sufficient for one-direction streaming. | One-way streaming is sufficient for chatbot |
| 7 | React Bits Dock navigation — use it or go with standard sidebar? | Resolved | Standard sidebar. No React Bits Dock. | Standard navigation is clearer for financial tool |

---

## Decision Log

### February 18, 2026 - All Phase 1 Open Questions Resolved

**Question #1: Domain Name**
**Decision:** Deploy to *.vercel.app subdomain for Phase 1. Buy custom domain later.
**Rationale:** Vercel provides free subdomain, no upfront cost. Custom domain can be added later when needed.
**Impact:** No domain purchase required for Phase 1 deployment.

**Question #2: RentCast Free Tier**
**Decision:** Free tier (50 calls/month) is sufficient. Mock all calls in dev/test. Cache 30 days in production.
**Rationale:** Aggressive caching (30 days) protects quota. Mocking in dev/test prevents quota waste during development.
**Impact:** No paid API tier needed. Caching strategy critical for production.

**Question #3: Sample Data Property**
**Decision:** 1515 N 7th St, Sheboygan WI 53081. Duplex, $220,000, 5 bed / 2 bath, 2,330 sqft, built 1900.
**Rationale:** Real Sheboygan duplex property provides authentic demo data for recruiters.
**Impact:** Hard-code this property data for "Try with sample data" button.

**Question #4: Chart Library**
**Decision:** Recharts. React-native, JSX composable, works with Tailwind.
**Rationale:** Better React integration, composable JSX API aligns with React patterns.
**Impact:** Use Recharts for all charts in Phase 3+.

**Question #5: Authentication**
**Decision:** Email/password only. No Google OAuth for MVP.
**Rationale:** Simpler implementation, sufficient for MVP. OAuth adds complexity without immediate benefit.
**Impact:** Simpler auth flow, faster Phase 1 delivery.

**Question #6: Chat Streaming**
**Decision:** SSE (Server-Sent Events). Simpler than WebSocket, sufficient for one-direction streaming.
**Rationale:** Chatbot only needs server-to-client streaming. SSE is simpler to implement and maintain.
**Impact:** Simpler implementation for Phase 2 chatbot.

**Question #7: Navigation**
**Decision:** Standard sidebar. No React Bits Dock.
**Rationale:** Standard navigation is clearer and more familiar for a financial tool. Dock is more experimental.
**Impact:** Use standard sidebar navigation throughout the app.

---

## Notes

- Update this file as questions are resolved
- Reference PRD.md Section 13 for original questions
- Add new questions here as they arise during development
