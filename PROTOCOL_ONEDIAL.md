# One-Dial Confirmatory Protocol

Protocol ID: `ONEDIAL-V3`. Second-act execution status: NOT AUTHORIZED. This document and `protocol_onedial.json` freeze the first-act design; after confirmation, every method and threshold is immutable. The authoritative source for every numerical choice in this document is `protocol_onedial.json`; the static reproduction command is `sbatch slurm/check_onedial_protocol.sbatch`, implemented by `scripts/check_onedial_protocol.py` with inputs `protocol_onedial.json`, this file, and `EXPERIMENTS.md`.

## Claim and estimand

For task loss after task-wise centering and fit-split scaling,

```text
loss(w,t) = mu_t + g(w) a_t + h(w) b_t + epsilon(w,t).
```

The H015/H016 first task singular vector is the total-quality loading `a`; the current claim is that cross-fitted removal of this rank-`1` component leaves one reproducible tradeoff loading `b`. The strict thesis claim requires exactly `1` residual factor. The user-requested Q2 acceptance envelope permits between `1` and `3` significant residual factors, but the wider result can produce only `PARTIAL`, never `SURVIVED`.

All computation is L0 with `0` GPUs and `0` GPU node-hours. Real-data uncertainty uses exactly `2000` single-layer row or target-vector bootstrap replicates. No bootstrap is nested inside another bootstrap. Null tests use `4999` permutations and are not reused as confidence intervals. Seeds are derived from the first `8` SHA256 bytes of the protocol ID plus an analysis label. Evidence for all numbers and formulas: `scripts/check_onedial_protocol.py`; input `protocol_onedial.json`; command `sbatch slurm/check_onedial_protocol.sbatch`.

## Frozen common pipeline

Rows are assigned to `2` cross-fitting folds by SHA256 of dataset, scale, and immutable row ID. Task standardization is learned only from the fit fold, uses `ddof=1`, and fails if a task standard deviation is below `1e-8`. Rank-`1` is fit on the opposite fold and subtracted only from held-out rows; held-out residuals are then stacked to estimate `h`. The response operator is unregularized OLS with an intercept, followed by SVD of the task-by-coordinate coefficient matrix.

For only the first `4` residual singular directions, the permutation p-value is `(1 + count(s_j_perm >= s_j_obs))/(1 + 4999)`. Holm correction controls familywise alpha `0.01` over exactly these `4` directions; significant dimension is the longest leading sequence for which every adjusted test rejects. 最小可达 p=0.0002，为 0.0025 的首道门槛留出 12.5 倍分辨率余量。覆盖注册判定空间的完备集：维度 1-3 的支持判定与"超过 3"的证伪判定各自只依赖这 4 个指标。A bootstrap resamples rows once within each original hash fold, refits the complete cross-fitted estimator, and sign-aligns `h` to the point estimate. It never bootstraps a bootstrap result.

Q1 chooses exactly one coordinate pipeline before any real outcome analysis. Pipeline A is the H015-compatible Helmert ilr map with multiplicative zero replacement `1e-6`; its frozen audits use `1e-8` and `1e-4`. Pipeline B is the zero-safe Hellinger map `sqrt(w)` followed by the Helmert basis and uses replacement `0`. If both pass synthetic discovery, A wins; if only B passes, B is frozen for Q2-Q5. No real outcome may influence this choice.

Discovery and confirmation are separate scale blocks or independent synthetic seed namespaces for every question. A discovery failure quarantines that question's confirmation unless the question specifies an independent external audit. Evidence for every number: `scripts/check_onedial_protocol.py`; inputs `protocol_onedial.json`, `scripts/test_h015.py`, and `scripts/test_h016.py`; command `sbatch slurm/check_onedial_protocol.sbatch`.

## Permanent Act I feasibility obligation

Before any future protocol freeze or Act II authorization, `scripts/check_onedial_feasibility.py` must enumerate and pass all `3` reachability-pair categories: minimum attainable p-value versus every corrected or registered p threshold; available rows or counts versus every required rank or minimum count; and sample or resample count versus every registered quantile-tail resolution. Any failed or unenumerated pair blocks freezing and execution. The mandatory artifact is `artifacts/onedial_v3_feasibility_check.json`; inputs are `protocol_onedial.json` and the four official Olmix ratio tables; command `sbatch slurm/check_onedial_feasibility.sbatch`.

## Q1 - Synthetic calibration with true zeros

Discovery uses `m=6/12` and `200` independent synthetic replicates per truth scenario; confirmation uses `m=18/24`, a disjoint SHA namespace, and `400` replicates per scenario. For every phase, `m`, interior scenario, and zero-based replicate index, the interior generator draws a fresh `n_m` by `m` weight matrix from symmetric Dirichlet alpha `1.0`, where `n_m` is the finite weight-row count of the corresponding unmodified Olmix ratio table. It uses NumPy PCG64 with the little-endian uint64 formed from the first `8` bytes of SHA256 over `ONEDIAL-V2:Q1-interior-weights:` plus the phase seed namespace, `m`, scenario, and replicate index in the exact serialization frozen in `protocol_onedial.json`. Each response has `110` orthonormal task loadings, noise sigma `1.0`, and singular values `2.0/0.5/0.35/0.30/0.25`. The five scenarios are interior rank-`1`, interior rank-`2`, interior rank-`5`, structural-zero rank-`1`, and structural-zero rank-`2`. Structural-zero scenarios continue to use the unmodified real Olmix design and generate responses in its zero-safe Hellinger coordinates, so success cannot be obtained by defining the truth in terms of the `1e-6` replacement.

Every synthetic replicate uses the exact Q2 permutation p-value and Holm dimension detector. The independent synthetic replicates, rather than a bootstrap around a bootstrap, provide calibration uncertainty.

Support requires, in both interior and structural-zero cases: null false-positive rate at most `0.075` with Wilson upper `95%` bound at most `0.10`; rank-`2` detection at least `0.80` with Wilson lower `95%` bound at least `0.75`; rank-`5` detection as more than `3` residual factors at least `0.80` with Wilson lower bound at least `0.75`; and recovered rank-`2` `h` cosine median at least `0.90` with `5%` quantile at least `0.80`. Pipeline choice uses discovery only, and only the selected pipeline is evaluated on confirmation.

Falsify Q1 if the selected pipeline misses any confirmation conjunction in either confirmation design. Return `inconclusive` if neither pipeline passes discovery or a declared synthetic rank is not constructible. Death branch: either non-support state prevents all real outcome access and records Q2-Q5 as `inconclusive_by_Q1`.

[agent-added] The rank-`1` structural-zero null is a leverage false-positive control; the rank-`5` scenario verifies that a pipeline able to find `h` can also reject the registered dimension ceiling.

Evidence for every number and branch: `scripts/check_onedial_protocol.py`; input `protocol_onedial.json` at `questions.Q1`; command `sbatch slurm/check_onedial_protocol.sbatch`.

## Q2 - Does Olmix contain a residual h of dimension at most three?

Discovery uses only `m=6/12`; confirmation uses only `m=18/24`. Tasks are the finite intersection across all `4` official releases, frozen before fitting. The null independently permutes each task's cross-fitted residual rows, adds the fixed held-out `g` prediction, and refits the complete estimator. The permutation p-value includes the observed statistic.

Every discovery and confirmation design must satisfy: `p_h <= 0.01`; significant residual dimension in `[1,3]`; `h` energy divided by total operator energy at least `0.05` with bootstrap lower `95%` bound at least `0.02`; `h` energy divided by residual operator energy at least `0.50` with lower bound at least `0.35`; within-split cross-scale loading cosine at least `0.70` with lower bound at least `0.50`; and cosine at least `0.80` under every frozen alternative coordinate, with significant-dimension disagreement at most `1`.

Support Q2 only if all conjunctions pass. Falsify it if a valid design has no significant `h`, more than `3` significant residual factors, or misses an effect/stability threshold. A validity failure is `inconclusive`. If Hellinger was selected in Q1, its `g` must align to the H015-compatible ilr `g` with point cosine at least `0.80` and bootstrap lower bound at least `0.60`; failure makes Q2 `inconclusive`, because it would no longer peel the direction pinned by the claim.

[agent-added] Exact One-Dial requires significant residual dimension exactly `1` and residual-energy bootstrap lower bound at least `0.50`. This flag is required for overall `SURVIVED`. [agent-added] The total-quality interpretation of `g` additionally requires at least `0.80` of task loadings to share its oriented sign.

Death branch: discovery failure leaves confirmation unread. Scientific Q2 falsification makes Q4/Q5 `falsified_by_Q2`, while Q3 may still run because it is an independent external-axis audit. Evidence for every number and branch: `scripts/check_onedial_protocol.py`; input `protocol_onedial.json` at `questions.Q2`; command `sbatch slurm/check_onedial_protocol.sbatch`.

## Q3 - Do task loadings replicate in RegMix and DataDecide?

There is no common raw task basis across all three releases, so Q3 freezes two bridges before data fitting. The exact downstream-task bridge between Olmix and DataDecide contains `8` outputs: ARC-Challenge, ARC-Easy, CommonsenseQA, HellaSwag, PIQA, SocialIQA, WinoGrande, and macro-averaged MMLU. The macro validation-loss bridge between RegMix and DataDecide contains `5` outputs: web, wiki, science, code, and books. The exact column mappings are immutable in `protocol_onedial.json`; learned matching, CCA, post-hoc rotations, or dropping a target are forbidden.

RegMix discovery is the official `1M` train table; confirmation is the official `60M` and `1B` test tables, reported separately. DataDecide discovery uses sizes `4M/6M/8M/10M/14M/16M/20M/60M`; confirmation uses `90M/150M/300M/530M/750M/1B`. Olmix discovery and confirmation remain `m=6/12` and `m=18/24`. The DataDecide task-level artifact is pinned to revision `b59512bb1b0b5dc02bfc469e0531be11149203d9` and must be downloaded under `$WORK` through Slurm before columns are inspected.

Olmix uses lower-is-better BPB, with MMLU subtasks averaged before scaling. RegMix uses released validation loss, with each frozen macro averaged before scaling. DataDecide downstream responses are fixed to `-log(max(correct_prob_per_char,1e-12))` at the maximum released step per recipe/model/task/seed, then averaged over seeds. DataDecide validation responses use `log(perplexity)` under the same final-step and seed rule. Recipes are a categorical one-hot design, centered within model size; no recipe-vector reconstruction is attempted.

Global singular-vector sign is nonidentifiable. The exact bridge freezes polarity by requiring `b_mmlu - mean(b_arc_easy,b_hellaswag) > 0`; the macro bridge requires `b_code - mean(b_web,b_wiki) > 0`. An anchor magnitude at most `1e-8` is invalid. Support requires each external `h` to have permutation `p <= 0.01` and residual-energy share at least `0.40`; each bridge must have point cosine at least `0.70`, bootstrap lower `95%` bound at least `0.40`, and relative sign agreement at least `6/8` exact tasks or `4/5` macro targets. Both bridges must pass in discovery and confirmation.

Falsify Q3 when all inputs and validity gates pass but either confirmation bridge misses a threshold. Missing/incompatible pinned task results, a missing frozen target, or an undefined polarity anchor yields `inconclusive`, not a substitute mapping.

[agent-added] The two bridges are reported independently. They test task-side `b_t` replication and cannot establish identical input-space functions `h(w)` across incompatible mixture domains.

Evidence for every number, revision, and mapping: `scripts/check_onedial_protocol.py`; inputs `protocol_onedial.json`, `vendor/regmix/data/*.csv`, `vendor/datadecide/perplexity_metrics_by_group.csv`, and the pinned DataDecide repository; command `sbatch slurm/check_onedial_protocol.sbatch`.

## Q4 - Do optimum mixtures lie on a one-dimensional dial curve?

Discovery freezes `a,b` from `m=6` and evaluates oracle choices only in `m=12`; confirmation freezes axes from `m=18` and evaluates only `m=24`. The validation-objective set has `512` members: `110` one-hot tasks and `402` SHA-seeded Dirichlet vectors with concentration `0.05`. SHA256 splits objectives equally into curve-fit and curve-evaluation halves, each requiring at least `200` objectives.

For each objective `v`, the registered dial coordinate is `theta_v = atan2(v dot b, v dot a)`. Its actual oracle mixture is the finite released row minimizing `v dot loss(w)`. In zero-safe Hellinger mixture coordinates, each coordinate is fit as a cubic spline of theta with degree `3` and `7` interior theta-quantile knots determined without outcomes. The spline is fit on one objective half and scored by multivariate held-out `R^2` on the other.

The null holds `g` fixed, independently permutes every task residual across target mixtures, recomputes oracle selections, and repeats the same frozen-form curve for `4999` permutations. Support requires held-out `R^2 >= 0.80` with single-layer target-bootstrap lower `95%` bound at least `0.70`, shuffle `p <= 0.01`, observed `R^2` at least `0.10` above the shuffle `99%` quantile, at least `10` distinct oracle mixtures, and theta span at least `0.75` radians, in both discovery and confirmation.

Falsify Q4 if a valid split misses any conjunction. Return `inconclusive` for undersized objective halves, an unresolved oracle tie above tolerance `1e-10`, or an unavailable Q2 dial. A tie within tolerance is broken only by SHA256 row ID.

[agent-added] Held-out objectives, the shuffle margin, distinct-oracle gate, and angle-span gate jointly prevent a small discrete candidate set from manufacturing high curve fit.

Evidence for every number and branch: `scripts/check_onedial_protocol.py`; input `protocol_onedial.json` at `questions.Q4`; command `sbatch slurm/check_onedial_protocol.sbatch`.

## Q5 - Can frozen g,h select near-optimal mixtures from fewer points?

Discovery freezes task axes from `m=6` and selects in `m=12`; confirmation freezes axes from `m=18` and selects in `m=24`. The One-Dial budgets are `2(m+1)`: `26` discovery points and `50` confirmation points. The comparison budgets are `3(m+1)`: `39` and `75`, a fixed point reduction of `0.3333333333333333`. Pilots are selected without outcomes by farthest-first traversal in the Q1-selected coordinates, starting nearest uniform and resolving ties by row hash.

One-Dial freezes source task loadings `a,b`, estimates a task intercept from target pilots, projects pilot residuals onto `a,b`, fits two unregularized affine score maps, and predicts all nonpilot candidates. Baselines are same-budget full multi-output affine OLS, same-budget per-objective affine OLS, and `3(m+1)`-point full multi-output affine OLS. All use the same pilot order and the Q4 objective set.

Regret is selected-minus-oracle objective loss divided by candidate objective-loss IQR. Support requires at least `0.80` top-decile selections with bootstrap lower `95%` bound at least `0.70`; median normalized regret at most `0.10` with bootstrap upper bound at most `0.15`; paired regret relative to the best same-budget baseline with upper bound at most `0.02`; paired regret relative to the larger-budget baseline with upper bound at most `0.05`; and at least `50` nonpilot candidates, in both stages.

Falsify Q5 if a valid stage misses any condition. Rank-deficient pilots, target IQR at most `1e-8`, or unavailable frozen source loadings yield `inconclusive`. The claim is limited to retrospective public-table observation efficiency, not newly trained models or target-scale transfer.

[agent-added] Attribution control independently permutes `a,b` over tasks. One-Dial must reduce normalized regret by at least `0.05`, with bootstrap lower `95%` bound at least `0.02`, or Q5 is falsified even if absolute regret passes.

Evidence for every number and branch: `scripts/check_onedial_protocol.py`; input `protocol_onedial.json` at `questions.Q5`; command `sbatch slurm/check_onedial_protocol.sbatch`.

## Overall verdict and immutable execution policy

`SURVIVED` requires Q1-Q5 supported and the Q2 exact-`1` agent-added gate. `KILLED` takes precedence if any of Q1-Q4 is falsified, including dependency falsification. `PARTIAL` applies when no Q1-Q4 question is falsified but at least one result is inconclusive, Q5 is falsified, or Q2 satisfies dimension at most `3` without satisfying exact-`1`.

During Act II, each question is committed as `ledger: Q<n> <verdict>`. A discovered protocol defect is appended to `EXPERIMENTS.md`, that question stops, and no criterion, split, mapping, or estimator is changed. The execution order is Q1 through Q5; every job runs through Slurm, and every completed job is appended with state, elapsed time, exit code, and zero-GPU accounting.

Evidence for every number, label, and command: `scripts/check_onedial_protocol.py`; inputs `protocol_onedial.json` and `EXPERIMENTS.md`; command `sbatch slurm/check_onedial_protocol.sbatch`.
