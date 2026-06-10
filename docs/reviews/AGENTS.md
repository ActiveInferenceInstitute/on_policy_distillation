# Agent guidance — docs/reviews/

- Each file is a disposition ledger for one external review; never edit a
  ledger to change history — append corrections with a dated note.
- A disposition row must name the repository file that carries the change;
  "implemented" without a file path is not evidence.
- DEFERRED rows state the blocking condition; do not silently resolve them —
  re-verify against the primary source first.
- New reviews get a new file `<review-id>.md` following the structure of
  `deep-review-2026-06.md`, plus an entry in `README.md`.
