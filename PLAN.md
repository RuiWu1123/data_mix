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

## Reflection after rejection streak 1

Round 1 produced `0` absolute passes among `6` candidates. H001 and H005 received substantial-overlap vetoes; H001–H005 each had an unresolved statement-to-test or estimand objection, while H006 missed only the impact threshold. The calibrated N/F/I vectors were H001 `6/6/7`, H002 `8/6/7`, H003 `9/6/7`, H004 `8/5/8`, H005 `6/6/7`, and H006 `7/9/6`.

The next round is constrained by four lessons:

- Do not propose another generic proxy-ranking-versus-decision-regret claim; DataDecide and the ICLR 2026 proxy-practice work already occupy that space.
- Define one common held-out estimand, the unit of resampling, and a noise source that corresponds to the claim; domain or mixture bootstrap variance cannot be called training-seed variance.
- For implementation audits, trace the value through its final consumer and make support conditional on that trace; algebraic coordinate differences alone are insufficient.
- Prefer constructive or measurement hypotheses with a predeclared intervention and an effect threshold, because a literal theorem typo can be crisp yet remain below oral-level impact.

Evidence for all round sizes and scores in this reflection: `scripts/check_review.py`; input `reviews/candidate_round1.json`; command `python scripts/check_review.py reviews/candidate_round1.json --threshold 7 --novelty-offset 1`; output `artifacts/candidate_round1_check.json`.
