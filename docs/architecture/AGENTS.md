# Agent Notes

`docs/architecture/` is documentation only. Keep business logic in
[`../../src/`](../../src/), orchestration in [`../../scripts/`](../../scripts/),
and generated artifacts under [`../../output/`](../../output/).

- These pages describe structure; the authoritative contracts live in
  [`../reference/rendering-reproducibility.md`](../reference/rendering-reproducibility.md)
  and the per-directory `AGENTS.md`/`README.md` pairs under `src/` and `scripts/`.
- Do not hand-author volatile counts (track count, sheaf-law count, theorem
  count). State them only where a file you read fixes them, and prefer linking to
  the producer over copying the value.
- When a layer, track, gate, or formal witness changes, update the relevant page
  here and re-run `uv run python scripts/validate_outputs.py` to confirm the
  described contract still holds.
- Do not describe network or LLM behavior in the default path — the exemplar has
  none.
