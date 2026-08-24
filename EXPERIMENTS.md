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

## H002 v1 — PREREGISTERED, admitted-by-fallback

- ID/date/type/level: H002, 2026-08-24, measurement, L0. Attacks A017 and A024.
- One-page statement: under the published additive data-mixing scaling law, the point optimum is not statistically identified: resampling mixture blocks produces materially separated optimal weight vectors whose target losses are practically indistinguishable on one common, untouched upper-scale criterion. The source paper reports point optima and predictive error but does not report an argmin confidence set.
- Why previously untested: Data Mixing Laws reports fitted surfaces, the multi-fidelity framework represents acquisition uncertainty, and Explaining DMSL reports point optima; none reports bootstrap set-identification for the frozen Apple additive law on this released SlimPajama table.
- Frozen falsifier and minimum detectable effect: support requires all three conditions: median pairwise L1 distance among bootstrap optima above `0.10`; at least one coordinate's percentile `95%` interval wider than `0.10`; and median common-evaluator loss difference among those optima at most `2` sigma. Failure of any condition falsifies H002. Use `1000` mixture-block bootstraps, with lower model sizes for generation and upper model sizes untouched until confirmation.
- Reviewer: raw N/F/I `7/6/7`, calibrated `8/6/7`; absolute REJECT with unresolved fatal objection, no overlap veto; relative rank `3`, hence admitted-by-fallback.
- Nearest priors: Scaling Laws for Optimal Data Mixtures gives the attacked point optima; Data Mixing Laws fits selected response surfaces without argmin sets; Data Mixture Optimization uses uncertainty prospectively rather than diagnosing this deterministic law; Explaining DMSL gives mechanistic point optima without confidence regions.
- Three strongest objections: per-bootstrap self-evaluation was not a common estimand; numerical optimizer dispersion could masquerade as non-identifiability; and the scale split/target/mixture-block bootstrap were underspecified.
- Frozen response in the design: every generated optimum is scored by one common upper-scale response surface fitted only after generation; each bootstrap uses `20` deterministic multistarts and must have optimizer spread at most `1e-6` in objective plus KKT/simplex residual at most `1e-6`; model-size halves, target size, mixture keys, and resampling unit are emitted in the result artifact. These are validity checks, not changed support thresholds; failing a validity check yields `inconclusive`.
- Cost: zero GPU, one Slurm CPU job. Evidence will be a JSON result plus the batch log. No result data have been inspected at preregistration time.
- Evidence for every count, threshold, score, and literature count in this entry: `scripts/check_review.py`; inputs `reviews/candidate_round1.json`, `references/scaling_laws_optimal_mixtures_2507.09404.pdf`, `vendor/ml_scalefit/examples/fit_dmsl.py`, and `vendor/ml_scalefit/data/dmsl_llm_slimpajama.csv`; command `python scripts/check_review.py reviews/candidate_round1.json --threshold 7 --novelty-offset 1`; output `artifacts/candidate_round1_check.json`.

## H003 v1 — PREREGISTERED, admitted-by-fallback

- ID/date/type/level: H003, 2026-08-24, audit, L0. Attacks A020.
- One-page statement: OP-MIX pretraining fits weights over probes trained on `0.9 e_i + 0.1 u`, but its final pretraining sampler consumes those coefficients as direct data ratios without applying or inverting the affine map `q = 0.9 a + 0.1 u`; consequently a material fraction of released candidate coordinates differ from the data coordinates actually represented by the proxy.
- Original-paper coverage: Algorithm 1 and Appendix B idealize pure-domain probes; Appendix A.2 states the `90%/10%` probe recipe. Figure 8 studies proxy regret but does not isolate this coordinate contract. Code locations are `vendor/on_policy_mix/pipeline/pretrain_opm.py:453`, `vendor/on_policy_mix/pretrain.py:321`, and `vendor/on_policy_mix/pipeline/pretrain_opm.py:248`.
- Why previously untested: MergeMix studies merge/data-rank consistency, while OLMix and RegMix use actual mixture coordinates; no nearest prior traces this affine coordinate contract through OP-MIX's final sampler.
- Frozen falsifier and minimum detectable effect: H003 is supported only if static source tracing finds no affine expansion/inversion before final sampling and, in both discovery and confirmation, the maximum candidate L1 coordinate error exceeds `1e-12` and the median is at least `0.02`. It is falsified if the final path applies the correct map or either split has maximum error at most `1e-12`; otherwise it is inconclusive. Discovery uses the paper's first fixed candidate-generation seed and `5` domains; confirmation uses a disjoint seed and a `7`-domain synthetic generalization. Continual OP-MIX is a negative control and must map its explicit ratio fields within `1e-12`.
- Noise/effect: this is deterministic contract evaluation repeated over `3` exact invocations. If all repetitions agree, sigma is `0`; a nonzero coordinate effect is reported as `infinite` sigma with its absolute L1 magnitude. Any repeat disagreement yields `inconclusive`.
- Reviewer: raw N/F/I `8/6/7`, calibrated `9/6/7`; absolute REJECT with fatal objections, no overlap veto; fallback rank `1`, hence admitted-by-fallback.
- Nearest priors: OP-Mix is the audited source; MergeMix shares merging proxies but not this affine trace; OLMix uses separately trained mixture coordinates; RegMix uses actual ratios.
- Three strongest objections and frozen response: the original universal wording was inconsistent with max/median, so the claim is limited to the declared distribution; the continual-style formula might not match pretraining, so the test derives `q = 0.9a + 0.1u` from the five-probe code; and algebra alone is insufficient, so source tracing to the final sampler is a required support condition.
- Cost: zero GPU, one Slurm CPU job. No test output was inspected before this entry.
- Evidence for every count, threshold, score, and code-line number in this entry: `scripts/check_review.py`; inputs `reviews/candidate_round1.json`, `references/op_mix_2605.15220.pdf`, and the cited `vendor/on_policy_mix` files; command `python scripts/check_review.py reviews/candidate_round1.json --threshold 7 --novelty-offset 1`; output `artifacts/candidate_round1_check.json`.

## H004 v1 — REJECTED

- ID/date/type/level: H004, 2026-08-24, audit, L0. Attacked A026 and A027.
- One-page statement: target-fidelity rows designated as ADMIRE test rows remain in the acquisition/training pool, so reported test MSE and target-search efficiency are not out of sample. The proposed trace would intersect row IDs across fitting, acquisition, and evaluation; support required nonempty overlap, contamination fraction at least `0.05`, and corrected replay changing mean MSE or target regret by at least `2` random-seed sigma. The Pile path was discovery and IFT was confirmation. Cost was zero GPU.
- Original coverage/novelty claim: ADMIRE reports multi-fidelity optimization but not a temporal row-lineage audit; earlier multi-fidelity work uses a separate simulator split.
- Review conclusion: raw N/F/I `7/5/8`, calibrated `8/5/8`; REJECT with unresolved fatal objection, no overlap veto; non-overlap fallback rank `4`, not admitted.
- Nearest prior work and differences: ADMIRE explicitly optimizes over a finite training pool; Data Mixture Optimization uses a separate 422/50 predictor split; RegMix separates regression and target mixtures; standard multi-fidelity BO legitimately acquires target-fidelity candidates after paying their cost.
- Three strongest objections: the page likely conflates finite-pool BO with supervised test leakage; row-ID intersection lacks the required temporal label trace; and changing either MSE or regret cannot establish invalidity of both, while the shared IFT pipeline is not independent confirmation.
- Disposition: abandoned without test. A repair would first need to identify a paper-claimed held-out estimand, so the current public-code observation is insufficient.
- Evidence for every count, threshold, and score in this entry: `scripts/check_review.py`; inputs `reviews/candidate_round1.json`, `references/admire_bayesopt_2508.11551.pdf`, and `vendor/admire_bayesopt/mfbayesopt_maxvalue.py`; command `python scripts/check_review.py reviews/candidate_round1.json --threshold 7 --novelty-offset 1`; output `artifacts/candidate_round1_check.json`.

## H005 v1 — REJECTED

- ID/date/type/level: H005, 2026-08-24, measurement, L0. Attacked A014 and A015.
- One-page statement: high held-out point-prediction R-squared does not certify low mixture-selection regret in the public 472-run multi-fidelity table. The proposed frozen test used leave-one-model-size-out evaluation and hashed domain halves; support required at least one scale with R-squared at least `0.90` and selected regret above `2` sigma in both halves, using `10000` mixture-block bootstrap replicates. Cost was zero GPU.
- Why proposed as new: the attacked work reports predictor fit before optimization, while the page sought a direct decision-certification test.
- Review conclusion: raw N/F/I `5/6/7`, calibrated `6/6/7`; REJECT, substantial-overlap veto, unresolved fatal objection, not fallback eligible.
- Nearest prior work and differences: Data Mixture Optimization already reports scale-varying optima and R-squared before GP decisions; RegMix links rank fit to selected mixtures; DataDecide directly uses pairwise decision accuracy; *Can Small Training Runs Reliably Guide Data Curation?* already defines top-k decision regret.
- Three strongest objections: leave-one-scale-out changes the published protocol, which includes half the target-scale runs; choosing at least one scale after inspection creates multiplicity; and hashed domain halves reuse the same models/mixtures/noise while the bootstrap does not replace target-model seeds.
- Disposition: abandoned without test because the central certification critique substantially overlaps two nearer works. Repair is not eligible.
- Evidence for every count, threshold, and score in this entry: `scripts/check_review.py`; inputs `reviews/candidate_round1.json`, `references/multifidelity_multiscale_2503.21023.pdf`, `references/datadecide_2504.11393.pdf`, and `vendor/data_recipes/results/data_mixing_runs.pkl`; command `python scripts/check_review.py reviews/candidate_round1.json --threshold 7 --novelty-offset 1`; output `artifacts/candidate_round1_check.json`.

## H006 v1 — PREREGISTERED, admitted-by-fallback

- ID/date/type/level: H006, 2026-08-24, audit, L0. Attacks A018.
- One-page statement: the literal displayed assumptions of GRAPE Theorem 2.1 admit a smooth, globally bounded-gradient target and constant source losses for which every GRAPE update is zero away from the target optimum, so the displayed global epsilon-optimal convergence conclusion does not follow.
- Original-paper coverage: GRAPE Section 2.1, Theorem 2.1, and Appendix C.1 give the convergence statement/proof; the prose immediately before the theorem mentions strong convexity, but the displayed theorem does not include it. The original paper does not test a stationary-source counterexample. The empirical update is located at `vendor/grape/src/trainer.py:816` and `vendor/grape/src/trainer.py:975`.
- Why previously untested: standard nonconvex theory distinguishes stationarity from global optimality, while DoGE and group DRO do not make this exact source-to-target bridge; no nearest work supplies a literal GRAPE counterexample.
- Frozen falsifier and minimum detectable effect: discovery uses target `f(theta)=1-exp(-theta^2)`, initialization `theta=1`, and one constant source loss. Confirmation uses the same target coordinate embedded in `7` dimensions with `7` distinct constant source values and independently implemented forward-mode automatic differentiation. H006 is supported only if every explicitly incorporated displayed assumption is satisfied, source-gradient/update norm is at most `1e-12`, and the target optimality gap exceeds `0.50` in both constructions. It is falsified if an incorporated displayed assumption fails or either update norm exceeds `1e-12`; ambiguity about incorporation yields `inconclusive`.
- Noise/effect: run each construction `3` exact repetitions. Agreement gives sigma `0`, with a nonzero optimality gap reported as `infinite` sigma; disagreement yields `inconclusive`.
- Reviewer: raw N/F/I `6/9/6`, calibrated `7/9/6`; absolute REJECT solely because impact is below oral threshold, no fatal objection for the literal theorem, no overlap veto; fallback rank `2`, hence admitted-by-fallback.
- Nearest priors: GRAPE is the audited theorem; DoGE uses alignment without the same global claim; group DRO optimizes its constituent group losses; standard smooth nonconvex theory guarantees stationarity without stronger structure.
- Three strongest objections and scope response: preceding prose invokes strong convexity, so the conclusion is limited to the literal displayed theorem; the chosen target is not strongly convex, so no claim is made about an intended corrected theorem or empirical GRAPE; and all referenced displayed definitions/assumptions must be enumerated before declaring support.
- Cost: zero GPU, one Slurm CPU job. No test output was inspected before this entry.
- Evidence for every count, threshold, score, and code-line number in this entry: `scripts/check_review.py`; inputs `reviews/candidate_round1.json`, `references/grape_2505.20380.pdf`, and `vendor/grape/src/trainer.py`; command `python scripts/check_review.py reviews/candidate_round1.json --threshold 7 --novelty-offset 1`; output `artifacts/candidate_round1_check.json`.

## H003 v1 — RESULT ATTEMPT 1

- Date/verdict: 2026-08-24, `inconclusive`. Review status remains `admitted-by-fallback`, calibrated N/F/I `9/6/7`.
- Discovery (`5` components, seed `0`, `1000` candidates): median/max L1 coordinate error `0.1699068579672292/0.19997472781501544`; all three repeat medians were exactly `0.1699068579672292`, but NumPy's sample standard deviation returned `3.3993498887762956e-17`, so the implementation did not recognize exact agreement.
- Independent confirmation (`7` components, seed `1729`, `1000` candidates): median/max L1 error `0.1775721961553033/0.19998872518171068`; three repeats gave sigma `0` and infinite-sigma effect. Both splits exceed the frozen median `0.02` and maximum `1e-12` thresholds.
- Source trace: all five booleans were true, including final direct coefficient expansion and the continual-path effective-ratio negative control. The numerical/source hypothesis conditions pass, but the preregistered repeat-validity implementation failed due solely to the discovery sigma artifact.
- Job accounting: Slurm job `384362`, state `COMPLETED`, elapsed `00:00:01`, exit `0:0`, MI210 GPUs `0`, MI210 node-hours `0`.
- Evidence: `scripts/test_h003.py` and `slurm/h003_l0.sbatch`; inputs are the three `vendor/on_policy_mix/pipeline` files listed in `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json`; command `sbatch slurm/h003_l0.sbatch`; raw log `/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h003-384362.out`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json`; accounting command `sacct -j 384362 --format=JobID,State,Elapsed,ExitCode -n -P`.

## H003 v1 — RESCUE 1 PREREGISTRATION

- Date: 2026-08-24. This is rescue analysis `1` of the allowed maximum `2` for the same hypothesis/data pair. It corrects only the repeat-agreement implementation; hypothesis, splits, source assertions, and effect thresholds remain frozen.
- Correction: define repeat sigma as exactly `0` when all three stored repeat statistics compare equal, otherwise use the sample standard deviation. This matches the preregistered phrase “all repetitions agree” and prevents a floating reduction artifact from overriding bitwise-equal inputs.
- Decision rule: rerun the unchanged job. The existing supported/falsified/inconclusive logic then applies without any threshold change.
- Evidence for all counts and the observed trigger: `scripts/test_h003.py`; input `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json`; diagnostic command `python -c "import json; p=json.load(open('/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json')); print(p['discovery']['repeat_medians'], p['discovery']['sigma'])"`; implementation and rerun occur only after this entry.

## H006 v1 — RESULT

- ID/date/type/level/verdict: H006, 2026-08-24, audit, L0, `supported`. Review status `admitted-by-fallback`; calibrated N/F/I `7/9/6`.
- Discovery: the one-dimensional construction satisfies every displayed Theorem 2.1 condition found by the parser. At `theta=1`, the target optimality gap is `0.6321205588285577`, source-gradient norm and update norm are `0`, and the analytic-versus-dual derivative error is `0`.
- Independent confirmation: the separately instantiated `7`-dimensional dual-number construction has the same `0.6321205588285577` gap, update norm `0`, and AD error `0`. The global gradient/smoothness bounds are `0.8577638849607068/2.0`; learning rate `0.25` is within the `0.5` bound; both regularizers are `1.0`.
- Noise/effect: three repetitions per construction give sigma `0`; the nonzero `0.6321205588285577` gap is `infinite` sigma and exceeds the preregistered `0.50` threshold. The conclusion is restricted to the literal displayed theorem.
- Job accounting: Slurm job `384364`, state `COMPLETED`, elapsed `00:00:00`, exit `0:0`, MI210 GPUs `0`, MI210 node-hours `0`.
- Evidence: `scripts/test_h006.py` and `slurm/h006_l0.sbatch`; inputs `/work1/ruixiangtang/rw761/data_mix_artifacts/paper_text/grape_2505.20380.txt` and `references/grape_2505.20380.pdf`; command `sbatch slurm/h006_l0.sbatch`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H006/result.json`; raw log `/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h006-384364.out`; accounting command `sacct -j 384364 --format=JobID,State,Elapsed,ExitCode -n -P`.

## H003 v1 — RESCUE 1 RESULT

- ID/date/type/level/verdict: H003, 2026-08-24, audit, L0, `supported`. Review status `admitted-by-fallback`; calibrated N/F/I `9/6/7`.
- Discovery (`5` components, seed `0`, `1000` candidates): median/max L1 coordinate error `0.1699068579672292/0.19997472781501544`. Three equal repeat medians give sigma `0` and an `infinite`-sigma effect.
- Independent confirmation (`7` components, seed `1729`, `1000` candidates): median/max error `0.1775721961553033/0.19998872518171068`; three equal repeats again give sigma `0` and an `infinite`-sigma effect. Both medians exceed `0.02` and maxima exceed `1e-12`.
- Source result: pretraining specifications contain only coefficient weights, the proxy reader falls back to those weights as ratios, new probes contain `0.9` new-domain mass, and final training directly expands coefficients; the continual implementation's explicit effective ratios pass the negative control.
- Job accounting: Slurm job `384365`, state `COMPLETED`, elapsed `00:00:01`, exit `0:0`, MI210 GPUs `0`, MI210 node-hours `0`.
- Evidence: corrected `scripts/test_h003.py` and `slurm/h003_l0.sbatch`; source inputs listed in `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json`; command `sbatch slurm/h003_l0.sbatch`; raw log `/work1/ruixiangtang/rw761/data_mix_artifacts/slurm/h003-384365.out`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json`; accounting command `sacct -j 384365 --format=JobID,State,Elapsed,ExitCode -n -P`.
