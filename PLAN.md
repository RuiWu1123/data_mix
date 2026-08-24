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

## Reflection after rejection streak 2

Round 2 again produced `0` absolute passes among `6` candidates, bringing the cumulative total to `12` REJECTs and triggering relative selection. The scores show two distinct failure modes: H012's exact artifact audit reached falsifiability `9` but novelty/impact only `3/4`; H010's broadly useful bootstrap idea received a substantial-overlap veto because simulator-input uncertainty is an established field. H008 similarly confused target-side label auditing with a deployable proxy-side decision rule.

Generation after this reflection is restricted as follows:

- No additional single-paper clerical audit is eligible; the next measurement must estimate a quantity across at least three independent mixing methods or datasets.
- No generic confidence interval, abstention, bootstrap-world, or regressor swap is eligible as the novelty claim.
- A construction must follow from a numbered mixing assumption and define an intervention absent from the nearest methods, with discovery and confirmation on method-disjoint public artifacts.
- Because the current six fallback admissions would contain four audits, at least one additional completed entry must be measurement or constructive so that the final audit fraction is at most `0.60`.

Evidence for every count and score: `scripts/check_review.py`; input `reviews/candidate_round2.json`; command `python scripts/check_review.py reviews/candidate_round2.json --threshold 7 --novelty-offset 0`; output `artifacts/candidate_round2_check.json`.

## Final State

The autonomous loop is complete: `9` hypotheses finished reviewed, pre-registered L0 tests, with `4` supported, `3` falsified, and `2` inconclusive verdicts. The audit share is `5/9 = 0.5555555555555556`; `4` completed tests are measurement or constructive. H003, H006, and H011 are closed with their verdicts retained; H015 is the sole candidate research line. All required documents exist, assumption and completion quotas pass, literature expansion is `10/15`, and GPU accounting is `0/200` MI210 node-hours.

Evidence for every number: `scripts/build_final_summary.py` and `scripts/check_final.py`; inputs `protocol.json`, `artifacts/assumptions_check.json`, `reviews/candidate_round1.json` through `reviews/candidate_round4.json`, the nine result JSON files listed in `artifacts/final_summary.json`, and the six required Markdown documents; commands `sbatch slurm/final_summary.sbatch` and `sbatch slurm/final_check.sbatch`; outputs `artifacts/final_summary.json` and `artifacts/final_check.json`.

## H015 Continuation State

The continuation adds H016 as the `10`th completed L0 test. The portfolio now contains `5` supported, `3` falsified, and `2` inconclusive verdicts; audit share is `5/10 = 0.5`, and measurement/constructive count is `5`. H016 confirms H015 under `3` frozen codomain metrics, with smallest rank deficit `37.71672810247446` bootstrap sigma, but its review score is only `4/6/4` and its claim excludes task de-duplication, intrinsic dimension, and predictive sample efficiency.

Three bridges from the spectral measurement stopped at the review gate: H017 v2 scored `6/4/6`, H018 v2 scored `4/2/5` with a substantial-overlap veto, and H019 v2 scored `5/5/4`; each submitted `0` test jobs. Therefore the continuation validates no paper-level predictive mechanism and no better data-mixing method. H003, H006, and H011 remain closed. Literature expansion is at its hard cap `15/15`; total GPU use and H015-extension GPU use are `0/200` and `0/60` MI210 node-hours.

Evidence for every number: `scripts/build_final_summary.py`, `scripts/test_h016.py`, and `scripts/check_final.py`; inputs `protocol.json`, `/work1/ruixiangtang/rw761/data_mix_artifacts/H016/result.json`, `reviews/candidate_round5.json`, `reviews/candidate_round5_h017_repair.json`, `reviews/candidate_round5_h018_repair.json`, `reviews/candidate_round6_repair.json`, and the `10` result JSON files listed in `artifacts/final_summary.json`; commands `sbatch slurm/h016_l0.sbatch`, `sbatch slurm/final_summary.sbatch`, and `sbatch slurm/final_check.sbatch`; outputs `artifacts/final_summary.json` and `artifacts/final_check.json`.
