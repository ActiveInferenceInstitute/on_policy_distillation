# Review dispositions

External-review responses for the manuscript, as evidence-bound disposition
ledgers. Each ledger maps every review item (claim audit, structural
recommendations, citation requests, visualization audit) to LANDED /
DEFERRED / REJECTED, with the carrying file named per row.

- [`deep-review-2026-06.md`](deep-review-2026-06.md) — disposition of the
  2026-06 external deep review; bulk implemented in Run-5 commit `66fe40b`,
  remainder in the run that authored the ledger.
- [`critical-review-2026-06.md`](critical-review-2026-06.md) — disposition of
  the 2026-06 critical-review hardening pass: retitle, finite sequential-shift
  witness, citation provenance, and deferred public-release requests.
- [`redteam-scholarship-visualization-2026-06.md`](redteam-scholarship-visualization-2026-06.md)
  — disposition of the RedTeam scholarship/visualization hardening pass:
  sequential-shift sensitivity, figure-source binding, and distribution-shift
  scholarship context.

Conventions: a row is LANDED only when a repository file carries the change;
items blocked on external re-verification (e.g. primary-source table numbers)
stay DEFERRED with the blocking condition stated; rejections state the reason
(usually a conflict with the figure-source-map or compose contract).
