# Open Questions Tracker

This file tracks open questions from the PRD that need decisions before or during development phases.

**Last Updated:** February 18, 2026

---

## Active Questions

| # | Question | Status | Decision | Notes |
|---|----------|--------|----------|-------|
| 1 | Domain name — midwestdealanalyzer.com? .dev? .app? | Open | TBD | Check availability and price before Phase 1 deployment |
| 2 | RentCast free tier — is 50 calls/month enough for dev + demo? | Open | TBD | Test during Phase 1, may need paid tier if insufficient |
| 3 | Sample data property — which specific Sheboygan address for "Try with sample data"? | Open | TBD | Pick a real duplex listing, hard-code the pre-filled data |
| 4 | Chart library — Recharts vs Chart.js? | Open | TBD | Prototype both in Phase 3, pick whichever is simpler |
| 5 | Auth — support Google OAuth in addition to email/password? | Open | TBD | Email/password for MVP, OAuth is Phase 4 stretch goal |
| 6 | Chat streaming — SSE vs WebSocket? | Open | TBD | Decide in Phase 2. SSE is simpler, WebSocket is more flexible |
| 7 | React Bits Dock navigation — use it or go with standard sidebar? | Open | TBD | Standard sidebar for Phase 1, evaluate Dock in Phase 4 |

---

## Decision Log

Decisions will be logged here as they are made.

### Example Format:
```
## [Date] - Question #X: [Question Title]
**Decision:** [What was decided]
**Rationale:** [Why this decision was made]
**Impact:** [What this affects]
```

---

## Notes

- Update this file as questions are resolved
- Reference PRD.md Section 13 for original questions
- Add new questions here as they arise during development
