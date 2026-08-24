# Append-Only Experiment Ledger

Historical entries below must never be edited or deleted. Corrections are new entries that cite the superseded entry.

## Literature additions

- ADD-REF-DOREMI — DoReMi: Optimizing Data Mixtures Speeds Up Language Model Pretraining. Reason: foundational comparator explicitly required by the task and directly attacked by Aioli and Olmix. Evidence: `scripts/reference_inventory.py`; input `references/doremi_2305.10429.pdf`; command `python scripts/reference_inventory.py --references references --vendor vendor --output artifacts/reference_inventory.json`.
- ADD-REF-DOGE — DoGE: Domain Reweighting with Generalization Estimation. Reason: foundational gradient-based mixing method explicitly required by the task and directly analyzed by Aioli and Olmix. Evidence: `scripts/reference_inventory.py`; input `references/doge_2310.15393.pdf`; command `python scripts/reference_inventory.py --references references --vendor vendor --output artifacts/reference_inventory.json`.
- ADD-REF-DATADECIDE — DataDecide: How to Predict Best Pretraining Data with Small Experiments. Reason: released multi-scale, multi-seed results enable zero-GPU tests of mixing transfer assumptions. Evidence: `scripts/reference_inventory.py`; input `references/datadecide_2504.11393.pdf`; command `python scripts/reference_inventory.py --references references --vendor vendor --output artifacts/reference_inventory.json`.
- ADD-REF-ADMIRE — ADMIRE-BayesOpt: Accelerated Data Mixture Re-weighting for Language Models with Bayesian Optimization. Reason: it is the closest uncertainty-aware sequential alternative to the multi-fidelity mixing framework and directly tests whether cross-scale proxy choice improves target mixture search. Evidence: `scripts/reference_inventory.py`; input `references/admire_bayesopt_2508.11551.pdf`; command `python scripts/reference_inventory.py --references references --vendor vendor --output artifacts/reference_inventory.json`.
- ADD-REF-TIKMIX — TiKMiX: Take Data Influence into Dynamic Mixture for Language Model Pre-training. Reason: it is the closest dynamic influence-based comparator for GRAPE, DoGE, and RegMix-D assumptions about gradient or trajectory sufficiency. Evidence: `scripts/reference_inventory.py`; input `references/tikmix_2508.17677.pdf`; command `python scripts/reference_inventory.py --references references --vendor vendor --output artifacts/reference_inventory.json`.
- ADD-REF-MERGEMIX — MergeMix: Efficient Data Mixture Optimization via Model Merging. Reason: it is the closest model-merging proxy prior to OP-MIX and is necessary to assess novelty of adapter-interpolation mixing. Evidence: `scripts/reference_inventory.py`; input `references/mergemix_2601.17858.pdf`; command `python scripts/reference_inventory.py --references references --vendor vendor --output artifacts/reference_inventory.json`.
- ADD-REF-INTERNAL-REPETITION — Internal Data Repetition Destroys Language Models. Reason: it provides the closest adverse evidence for repetition-aware mixing laws and tests whether repetition topology, not only repetition count, controls degradation. Evidence: `scripts/reference_inventory.py`; input `references/internal_repetition_2606.24998.pdf`; command `python scripts/reference_inventory.py --references references --vendor vendor --output artifacts/reference_inventory.json`.

## REVIEW-CALIBRATION

- Date: 2026-08-24.
- Blindness: reviewer launched with `fork_turns=none` and received only two one-page calibration hypotheses plus the reference filename list.
- CAL-RM raw scores: novelty 6, falsifiability 9, impact 8; oral-level REJECT. The three closest works were Data Mixing Laws, DoReMi, and DoGE; strongest objections were prior overlap, global-rank versus top-region validity, and transported baselines.
- CAL-DG raw scores: novelty 6, falsifiability 8, impact 7; oral-level REJECT. The three closest works were DoReMi, Skill-It, and Learning to Reweight Examples; strongest objections were local versus long-horizon utility, gradient-norm confounding, and narrow empirical breadth.
- Calibration action: because both published core hypotheses fell below the threshold of 7 only on novelty, subsequent reviews use a novelty offset of 1. The substantial-overlap veto and thresholds of 7 for all calibrated dimensions remain unchanged.
- Budget action: conservative token accounting forced relative-selection mode before candidate review because cumulative use 386781 exceeded the review-generation pool limit 200000 under the total budget 500000.
- Evidence: `scripts/check_review.py` and `scripts/check_budget.py`; inputs `reviews/calibration.json`, `protocol.json`, `artifacts/budget_snapshot_20260824.json`; commands `python scripts/check_review.py reviews/calibration.json --threshold 7 --novelty-offset 1` and `python scripts/check_budget.py --protocol protocol.json --snapshot artifacts/budget_snapshot_20260824.json`.

## JOB-384355 — L0 environment setup

- Date: 2026-08-24. Slurm state `COMPLETED`, elapsed `00:00:43`, exit code `0:0`, requested nodes `1`, requested CPUs `4`, MI210 GPU count `0`, and MI210 node-hours `0`.
- Output versions: NumPy `2.5.2`, pandas `3.0.5`, SciPy `1.18.1`, scikit-learn `1.9.0`.
- Evidence: `slurm/setup_l0_env.sbatch`; inputs `slurm/setup_l0_env.sbatch` and the public Python package index; commands `sbatch slurm/setup_l0_env.sbatch` and `sacct -j 384355 --format=JobID,State,Elapsed,ExitCode -n -P`; raw output `/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/setup_l0_env-384355.out`.

## BUDGET-CORRECTION-001

- Date: 2026-08-24. This entry supersedes only the budget action in `REVIEW-CALIBRATION`; it does not alter that historical entry or the completed review.
- The user raised the total token budget from `500000` to `50000000`. The generation-and-review pool is therefore `20000000` tokens (`50000000 * 0.4`), while the captured cumulative use was `477562`; the conservative cutoff check returns `forced_relative_selection=false`.
- Consequence: absolute review resumes for new candidates. The already completed relative-selection result for H002/H003/H006 remains recorded and may be tested because it was valid under the budget in force when issued.
- Evidence: `scripts/check_budget.py`; inputs `protocol.json`, `artifacts/budget_snapshot_20260824_after_raise.json`; command `python scripts/check_budget.py --protocol protocol.json --snapshot artifacts/budget_snapshot_20260824_after_raise.json`; output `artifacts/budget_status_20260824_after_raise.json`.

## H001 v1 — REJECTED

- ID/date/type/level: H001, 2026-08-24, measurement, L0.
- One-page statement: RegMix can have high global proxy-to-target rank agreement while failing in the decision-relevant Pareto region. This attacks A001, A009, and A027. The original papers report global rank/prediction transfer but do not test the conjunction below. The public 64-mixture Pile grid was to use IDs 0–31 for discovery and 32–63 for confirmation, with uniform mean validation loss as the frozen target.
- Falsifier and minimum detectable effect: support required top-quartile overlap below `0.50` and selected target regret above `2` domain-bootstrap sigma in both halves; overlap at least `0.50` or regret at most `2` sigma would falsify. The minimum overlap deficit was `0.125`; `10000` domain-stratified bootstrap replicates were proposed. Cost was zero GPU.
- Why proposed as new: RegMix reports global Spearman; the page attempted to separate global prediction from local decision quality.
- Review conclusion: raw scores N/F/I `5/6/7`, calibrated `6/6/7`; REJECT, substantial-overlap veto, unresolved fatal objection, not fallback eligible.
- Nearest prior work and differences: RegMix reports global Spearman on the same swarm, whereas H001 targeted top-quartile overlap and regret; DataDecide uses pairwise decision accuracy over 25 recipes, 14 sizes, and three seeds, whereas H001 targeted an extreme region; *Can Small Training Runs Reliably Guide Data Curation?* already centers top-k decision regret, leaving mainly a dataset/statistic change; ADMIRE-BayesOpt uses prospective uncertainty, whereas H001 was retrospective.
- Three strongest objections: the statement required high global correlation but set no Spearman threshold; domain resampling is not target-training seed noise; and the two ID halves were not shown exchangeable while overlap moves in `0.125` increments. The first is a fatal statement-to-test mismatch.
- Disposition: abandoned without test. The closest 2026 prior creates substantial overlap, so repair is not eligible.
- Evidence for every count, threshold, and score in this entry: `scripts/check_review.py`; inputs `reviews/candidate_round1.json`, `references/regmix.pdf`, `references/datadecide_2504.11393.pdf`, and the linked prior metadata stored in the review; command `python scripts/check_review.py reviews/candidate_round1.json --threshold 7 --novelty-offset 1`; output `artifacts/candidate_round1_check.json`.
