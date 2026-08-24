# Autonomous Data-Mixing Exploration Plan

Scope is restricted to LLM pretraining data mixing. Adjacent data selection, cleaning, and general scaling-law work is admitted only when it is necessary to attack a numbered mixing assumption.

The machine-readable constraints are in `protocol.json`. Validate their use with the task-specific scripts named in each ledger entry; the authoritative input is the user goal in this thread.

Current sequence:

- Inventory and read every seed and added paper; pin official source repositories.
- Build `ASSUMPTIONS.md` with paired paper and code locations, then run `scripts/check_assumptions.py`.
- Calibrate a context-free reviewer on published hypotheses before candidate review.
- Pre-register only accepted or fallback-admitted hypotheses in append-only `EXPERIMENTS.md`.
- Prefer public-table analyses; submit any training exclusively through Slurm batch jobs.
- Confirm discoveries on held-out splits or independent seeds and report all effects in noise-standard-deviation units.
- Finish with the required quota table in `RESULT.md`, or close early only on a protocol stop condition.
