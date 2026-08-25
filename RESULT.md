# Results

## TWODIAL-E2E-V1 Verdict - FALSIFIED

R1 returns `rank3+-sufficient`: rank `2` beats rank `1` in all `3` sources but fails both the best-baseline and rank-`3` marginality gates in all `3`. The held-out metric is pooled task-standardized RMSE; the DataDecide multi-seed noise floor is `0.009521085`. Values below are produced by `scripts/build_rank2_r3_summary.py`; inputs `artifacts/rank2_r1_result.json`, `artifacts/rank2_r2_result.json`, `artifacts/rank2_r2_check.json`, and `artifacts/rank2_r2_jobs.csv`; command `sbatch slurm/build_rank2_r3_summary.sbatch`; output `artifacts/rank2_r3_summary.json`.

### Held-out error vs rank

| Source | Rank 1 | Rank 2 | Rank 3 | Rank 4 | Rank 5 | Rank 6 | Full linear | ExtraTrees |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Olmix | 0.859763 | 0.744424 | 0.679759 | 0.643566 | 0.614534 | 0.596423 | 0.584808 | 0.595049 |
| RegMix | 1.045725 | 0.959292 | 0.910766 | 0.858065 | 0.793127 | 0.710267 | 0.504774 | 0.669302 |
| DataDecide | 0.374847 | 0.320550 | 0.308837 | 0.301692 | 0.298746 | 0.298157 | 0.297821 | 0.351327 |

The curve plot is `artifacts/rank2_r1_curve.png`; exact unrounded cells and the `5` held-out folds are in `artifacts/rank2_r1_result.json`, produced by `scripts/run_rank2_r1.py` from the public Olmix, RegMix, and DataDecide tables with command `sbatch slurm/run_rank2_r1.sbatch`.

### GPU duel

All `12/12` registered runs completed `954` optimizer steps, `1000341504` tokens, and `13` task evaluations. Aggregate loss is the frozen mean of task-standardized validation CE; mean BPB is descriptive because its `13` task scales differ. The values are produced by `scripts/build_rank2_r3_summary.py` with the inputs, command, and output above; exact per-task/run values are in `artifacts/rank2_r2_jobs.csv`, produced by `scripts/collect_rank2_r2.py` with command `env RANK2_JOB_IDS=385435,385436,385478 sbatch --export=ALL,RANK2_JOB_IDS slurm/collect_rank2_r2.sbatch`.

| Arm | Seed | Aggregate standardized loss | Mean BPB | Status |
|---|---:|---:|---:|---|
| ExtraTrees/full nonparametric | 3406 | -0.251318 | 7.556964 | complete |
| ExtraTrees/full nonparametric | 3407 | -0.243606 | 7.572186 | complete |
| ExtraTrees/full nonparametric | 3408 | -0.254006 | 7.579789 | complete |
| Rank-selected | 3406 | -0.071098 | 7.856169 | complete |
| Rank-selected | 3407 | 0.121044 | 7.956989 | complete |
| Rank-selected | 3408 | -0.056177 | 7.896565 | complete |
| h-probe | 3406 | 0.135294 | 8.076130 | complete |
| h-probe | 3407 | 0.075539 | 8.076453 | complete |
| h-probe | 3408 | 0.028140 | 8.060925 | complete |
| Official RegMix | 3406 | 0.206980 | 8.297375 | complete |
| Official RegMix | 3407 | 0.167362 | 8.298964 | complete |
| Official RegMix | 3408 | 0.141846 | 8.305978 | complete |

Seed-mean BPB for every registered domain is shown below. Values are rounded to `4` decimals from `artifacts/rank2_r3_summary.json`, produced by `scripts/build_rank2_r3_summary.py` with the inputs and command above.

| Arm | arXiv | FreeLaw | PMC | Wiki | Math | GitHub | StackEx | Gutenberg | Pile-CC | Ubuntu | HN | PubMed Abs | USPTO |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ExtraTrees | 7.0203 | 7.6459 | 7.7629 | 8.7043 | 3.3898 | 8.4447 | 7.3048 | 7.9985 | 7.9426 | 8.3455 | 7.8726 | 8.6770 | 7.2965 |
| Rank-selected | 9.2127 | 7.3222 | 7.7050 | 7.8852 | 4.0701 | 9.3327 | 8.4447 | 7.0967 | 8.0600 | 9.5617 | 7.5463 | 8.7377 | 7.7671 |
| h-probe | 7.2094 | 8.3189 | 9.0078 | 8.6839 | 8.3224 | 7.5445 | 7.9679 | 7.4316 | 7.9228 | 8.2771 | 7.2665 | 8.6660 | 8.3063 |
| Official RegMix | 8.9992 | 8.1449 | 8.4095 | 8.2557 | 7.4851 | 9.7181 | 8.8977 | 7.8410 | 7.8300 | 8.4208 | 7.4254 | 8.3702 | 8.1125 |

The frozen effects and independent reproduction are:

| Contrast/metric | Point | Paired sigma | Effect (sigma) | 95% interval (sigma) | Registered reading |
|---|---:|---:|---:|---:|---|
| Rank-selected minus ExtraTrees loss | 0.247567 | 0.101779 | 2.432389 | [-0.051749, 4.916526] | falsifies at >1.0 |
| Official minus rank-selected loss | 0.174139 | 0.117712 | 1.479374 | [-1.004763, 3.963512] | support component passes at >=1.0 |
| h-probe minus selected, code/math | -0.058944 | 0.007947 | -7.417299 | [-9.901437, -4.933161] | magnitude passes at >=1.0 |
| h-probe minus selected, Pile-CC/Wiki | 0.422025 | 0.165824 | 2.545025 | [0.060887, 5.029163] | magnitude passes at >=1.0 |

The predicted-versus-observed h vector has cosine `0.277150` against the `>=0.70` support gate and sign agreement `8/13` against `>=10/13`. `scripts/check_rank2_r2_result.py` independently reproduces every effect and reports `31/31` checks passing in `artifacts/rank2_r2_check.json`; command `sbatch slurm/check_rank2_r2_result.sbatch`. The effect plot is `artifacts/rank2_r2_effects.png`. Successful and failed terminal-save attempts consumed `13.276667/13.241389`, totaling `26.518056` MI210 node-hours, as produced by `scripts/build_rank2_r3_summary.py` in `artifacts/rank2_r3_summary.json`.

<!-- RANK2_CONCLUSION_START -->
R1 does not support rank 2 as sufficient: all three public sources prefer rank 3 or higher under the frozen held-out gates. R2 then falsifies the registered end-to-end selection claim at the 27,133,184-parameter, 1,000,341,504-token anchor. The rank-selected mixture is worse than ExtraTrees by 2.432 sigma, although it beats the official RegMix mixture by 1.479 sigma. The h probe produces the predicted opposite code/math versus Pile-CC/Wikipedia family movement at -7.417 and +2.545 sigma, but its full 13-task direction has cosine 0.277 and only 8/13 matching signs. Thus a tradeoff axis is measurable, while the frozen two-dial law does not select a competitive mixture at this anchor. This is one model scale and does not establish scale invariance.
<!-- RANK2_CONCLUSION_END -->

Parameter/token counts and verdict thresholds in the conclusion are produced by `scripts/check_rank2_rocm_model.py`, `scripts/generate_rank2_r2_configs.py`, and `scripts/check_rank2_r2_result.py`; inputs `rank2_protocol.json`, `artifacts/rank2_r2_config_manifest.json`, and `artifacts/rank2_r2_jobs.csv`; commands `sbatch slurm/check_rank2_rocm_model.sbatch`, `sbatch slurm/generate_rank2_r2_configs.sbatch`, and `sbatch slurm/check_rank2_r2_result.sbatch`; outputs `artifacts/rank2_rocm_model_check.json`, `artifacts/rank2_r2_config_manifest.json`, and `artifacts/rank2_r2_check.json`.

### Minimum upgrade

The minimum scale-stability test is a new preregistration of the same `4` arms at RegMix `tinyllama_60M` with `3` new paired seeds, hence `12` successful jobs, the same `13` tasks, and at least the current `1000341504` tokens per job. A rank-2 scale-rescue claim must require rank-selected minus ExtraTrees at most `0.5` paired sigma, direction cosine at least `0.70`, and sign agreement at least `10/13`; recurrence above `1.0` sigma falsifies scale rescue. These numerical gates are unchanged fields of `rank2_protocol.json`, validated by `scripts/check_rank2_protocol.py` with command `sbatch slurm/check_rank2_protocol.sbatch`; the `tinyllama_60M` branch is the registered R2 power-rule scale in the same input. This is a future protocol, not a rescue analysis of the present data.

## ONEDIAL-V3 Act II Verdict - PARTIAL

ONEDIAL-V3 completes synthetic discovery and terminates `PARTIAL`. Both registered coordinate pipelines fail Q1 discovery, so Q1 is `inconclusive`, its confirmation split remains unread, and Q2-Q5 follow the frozen `inconclusive_by_Q1` death branch. The execution contains `4000` synthetic discovery records across `20` cells, `0` confirmation records, `0` real outcome tables, and `0` downstream scientific jobs. Every count and branch is produced by `scripts/check_onedial_q1_result.py` and `scripts/resolve_onedial_v3_dependencies.py`; inputs `protocol_onedial.json`, `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/Q1/discovery/shards`, `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/Q1/discovery/result.json`, and `artifacts/onedial_v3_q1_result_check.json`; commands `sbatch slurm/check_onedial_q1_result.sbatch` and `sbatch slurm/resolve_onedial_v3_dependencies.sbatch`; outputs `artifacts/onedial_v3_q1_result_check.json` and `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/dependency_resolution.json`.

| Question | Verdict | Dependency state | Recorded numerical result | Evidence |
|---|---|---|---|---|
| V3-Q1 | `inconclusive` | `no_discovery_pipeline_passed` | A rank-2 detection at `m=6/12`: interior `0.04/0`, structural zero `0/0`; B: interior `0.04/0.005`, structural zero `0/0`. A/B maximum rank-5 dimension>3 rate `0.005/0`; maximum rank-2 cosine median `0.4333935369/0.4368551769` versus `0.90`; selected pipelines `0` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/Q1/discovery/result.json` from `scripts/run_onedial_q1.py aggregate`, command `sbatch --export=ALL,ONEDIAL_PHASE=discovery,ONEDIAL_INPUT_ROOT=/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/Q1/discovery/shards,ONEDIAL_OUTPUT=/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/Q1/discovery/result.json slurm/onedial_q1_aggregate.sbatch` |
| V3-Q2 | `inconclusive` | `inconclusive_by_Q1` | Real outcome tables `0`; downstream tests `0`; residual dimension/effect `n/a` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/dependency_resolution.json` from `scripts/resolve_onedial_v3_dependencies.py`, command `sbatch slurm/resolve_onedial_v3_dependencies.sbatch` |
| V3-Q3 | `inconclusive` | `inconclusive_by_Q1` | Real outcome tables `0`; downstream tests `0`; bridge cosine/polarity `n/a` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/dependency_resolution.json` from `scripts/resolve_onedial_v3_dependencies.py`, command `sbatch slurm/resolve_onedial_v3_dependencies.sbatch` |
| V3-Q4 | `inconclusive` | `inconclusive_by_Q1` | Real outcome tables `0`; downstream tests `0`; curve fit/shuffle `n/a` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/dependency_resolution.json` from `scripts/resolve_onedial_v3_dependencies.py`, command `sbatch slurm/resolve_onedial_v3_dependencies.sbatch` |
| V3-Q5 | `inconclusive` | `inconclusive_by_Q1` | Real outcome tables `0`; downstream tests `0`; regret/attribution `n/a` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V3/dependency_resolution.json` from `scripts/resolve_onedial_v3_dependencies.py`, command `sbatch slurm/resolve_onedial_v3_dependencies.sbatch` |

The Q1 failure is a calibration result about the frozen test battery, not a falsification of the One-Dial scientific claim. The strictest observed gap is detector power: the largest registered rank-2 detection rate is `0.04` with Wilson lower `95%` bound `0.0204056321`, against required rate/lower-bound gates `0.80/0.75`; the largest rank-5 dimension>3 rate is `0.005` with lower bound `0.0008831687`, against `0.80/0.75`. The largest rank-2 cosine median/q05 pair is `0.4368551769/0.1212878759`, against `0.90/0.80`. Every rate, interval, quantile, and gate is produced by `scripts/run_onedial_q1.py aggregate`; input, command, and output are the Q1 aggregate input, command, and result above.

The minimum upgrade is a newly reviewed protocol, not a V3 rescue analysis: first calibrate the joint signal/noise/sample-size grid on new synthetic seed namespaces and require at least `0.80` rank-2 and rank-5 detection with Wilson lower `95%` bound at least `0.75`, while retaining null rate/Wilson upper bound at most `0.075/0.10`; then freeze one calibrated anchor before any real outcome access. These numerical targets are the unchanged Q1 gates in `protocol_onedial.json`, validated by `scripts/check_onedial_protocol.py`; input `protocol_onedial.json`; command `sbatch slurm/check_onedial_protocol.sbatch`; output `artifacts/onedial_protocol_check.json`.

## ONEDIAL-V2 Act II Verdict - PARTIAL

ONEDIAL-V2 terminates `PARTIAL` before synthetic realization. Its Q1 detector uses `999` permutations, so the minimum attainable p-value is `0.001`; Holm at familywise alpha `0.01` cannot reject the first of `11/17/23` residual tests for `m=12/18/24`. Q1 is therefore `inconclusive`, and the frozen death branch records Q2-Q5 as `inconclusive_by_Q1`. These numbers and branches are produced by `scripts/audit_onedial_q1_holm_resolution.py` and `scripts/resolve_onedial_v2_dependencies.py`; inputs `protocol_onedial.json` and `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V2/Q1/holm_resolution_audit.json`; commands `sbatch slurm/q1_holm_resolution_audit.sbatch` and `sbatch slurm/resolve_onedial_v2_dependencies.sbatch`; outputs `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V2/Q1/holm_resolution_audit.json` and `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V2/dependency_resolution.json`.

| Question | Verdict | Dependency state | Recorded numerical result | Evidence |
|---|---|---|---|---|
| V2-Q1 | `inconclusive` | `protocol_defect` | Impossible designs `3/4`; minimum p `0.001`; first Holm thresholds at `m=12/18/24` are `0.0009090909090909091/0.0005882352941176471/0.0004347826086956522`; selected pipelines `0` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V2/Q1/holm_resolution_audit.json` from `scripts/audit_onedial_q1_holm_resolution.py`, command `sbatch slurm/q1_holm_resolution_audit.sbatch` |
| V2-Q2 | `inconclusive` | `inconclusive_by_Q1` | Synthetic realizations `0`; real outcome tables `0`; downstream tests `0`; residual dimension/effect `n/a` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V2/dependency_resolution.json` from `scripts/resolve_onedial_v2_dependencies.py`, command `sbatch slurm/resolve_onedial_v2_dependencies.sbatch` |
| V2-Q3 | `inconclusive` | `inconclusive_by_Q1` | Real outcome tables `0`; downstream tests `0`; bridge cosine/polarity `n/a` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V2/dependency_resolution.json` from `scripts/resolve_onedial_v2_dependencies.py`, command `sbatch slurm/resolve_onedial_v2_dependencies.sbatch` |
| V2-Q4 | `inconclusive` | `inconclusive_by_Q1` | Real outcome tables `0`; downstream tests `0`; curve fit/shuffle `n/a` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V2/dependency_resolution.json` from `scripts/resolve_onedial_v2_dependencies.py`, command `sbatch slurm/resolve_onedial_v2_dependencies.sbatch` |
| V2-Q5 | `inconclusive` | `inconclusive_by_Q1` | Real outcome tables `0`; downstream tests `0`; regret/attribution `n/a` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL_V2/dependency_resolution.json` from `scripts/resolve_onedial_v2_dependencies.py`, command `sbatch slurm/resolve_onedial_v2_dependencies.sbatch` |

The resolution floor is not an observed weak effect. Even an observed statistic exceeding all `999` null permutations has p-value `1/1000`; the registered detector would require at least `1099/1699/2299` permutations merely to make first-factor rejection numerically attainable at `m=12/18/24`. The registered shortfalls are `100/700/1300`, and the rank-`2` detection-rate upper bound at those designs is `0.0` against the required `0.80`. Every number is produced by `scripts/audit_onedial_q1_holm_resolution.py`; input, command, and output are the Q1 audit input, command, and output above.

V2 therefore supplies no evidence for or against a residual tradeoff axis and leaves H015/H016 unchanged. Any executable successor must be a newly frozen protocol that resolves the permutation/Holm granularity before generating outcomes; increasing the V2 permutation count after authorization is forbidden by the mutation rule. Evidence for `0` synthetic realizations, `0` real tables, and the `PARTIAL` branch: `scripts/resolve_onedial_v2_dependencies.py`; inputs, command, and output are listed above.

## One-Dial Act II Verdict - PARTIAL

The frozen One-Dial battery returns `PARTIAL`. Q1 is `inconclusive` because its approved protocol declares `3` interior truth scenarios but defines `0` interior generators, and the public designs cannot supply full-rank strictly positive subsets. The frozen Q1 death branch therefore records Q2-Q5 as `inconclusive_by_Q1`; all `5` scientific verdicts are `inconclusive`, not supported or falsified. These counts and branches are produced by `scripts/audit_onedial_q1_design.py` and `scripts/resolve_onedial_dependencies.py`; inputs `protocol_onedial.json`, `/work1/ruixiangtang/rw761/data_mix_public/olmix_rq2/m{6,12,18,24}_ratios.csv`, and `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/Q1/design_audit.json`; commands `sbatch slurm/q1_design_audit.sbatch` and `sbatch slurm/resolve_onedial_dependencies.sbatch`; outputs `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/Q1/design_audit.json` and `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/dependency_resolution.json`.

| Question | Verdict | Dependency state | Recorded numerical result | Evidence |
|---|---|---|---|---|
| Q1 | `inconclusive` | `protocol_defect` | Strictly positive rows at `m=6/12/18/24`: `5/0/0/0`; centered-log ranks `4/0/0/0` versus required `5/11/17/23`; selected pipelines `0` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/Q1/design_audit.json` from `scripts/audit_onedial_q1_design.py`, command `sbatch slurm/q1_design_audit.sbatch` |
| Q2 | `inconclusive` | `inconclusive_by_Q1` | Real outcome tables `0`; downstream tests `0`; residual dimension/effect `n/a` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/dependency_resolution.json` from `scripts/resolve_onedial_dependencies.py`, command `sbatch slurm/resolve_onedial_dependencies.sbatch` |
| Q3 | `inconclusive` | `inconclusive_by_Q1` | Real outcome tables `0`; downstream tests `0`; bridge cosine/polarity `n/a` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/dependency_resolution.json` from `scripts/resolve_onedial_dependencies.py`, command `sbatch slurm/resolve_onedial_dependencies.sbatch` |
| Q4 | `inconclusive` | `inconclusive_by_Q1` | Real outcome tables `0`; downstream tests `0`; curve fit/shuffle `n/a` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/dependency_resolution.json` from `scripts/resolve_onedial_dependencies.py`, command `sbatch slurm/resolve_onedial_dependencies.sbatch` |
| Q5 | `inconclusive` | `inconclusive_by_Q1` | Real outcome tables `0`; downstream tests `0`; regret/attribution `n/a` | `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/dependency_resolution.json` from `scripts/resolve_onedial_dependencies.py`, command `sbatch slurm/resolve_onedial_dependencies.sbatch` |

The decisive Q1 input audit found `125/130/129/127` finite rows at `m=6/12/18/24`, with exact-zero cells `349/1162/1911/2634`; rows containing at least one exact zero are `120/130/129/127`. The approved mutation rule forbids adding a positive closure, a new synthetic design, or another DGP after this audit. Every count is produced by `scripts/audit_onedial_q1_design.py`; inputs are the four official Olmix ratio tables and `protocol_onedial.json`; command `sbatch slurm/q1_design_audit.sbatch`; output `/work1/ruixiangtang/rw761/data_mix_artifacts/ONEDIAL/Q1/design_audit.json`.

This result leaves H015/H016's descriptive concentration measurement unchanged but does not answer whether a residual tradeoff axis exists. The minimum admissible upgrade is a fresh protocol version that defines the interior weight generator and its scale before any synthetic calibration or real-outcome access; it cannot be a correction to ONEDIAL-V1. Evidence for the unchanged Q1 outcome quarantine and `0` selected pipelines: `scripts/resolve_onedial_dependencies.py`; inputs and command are the dependency-resolution inputs and command above.

## CANDIDATE FINDING - H016

H015's affine response concentration survives `3` frozen output metrics on the same `110` official Olmix tasks: raw BPB, task-standardized BPB, and equal-family-quadratic weighting over Math/Code/QA task counts `7/19/84`. Across `m=6/12/18/24`, all `12/12` rank conditions and `8/8` rank-`2` overlap conditions pass. The largest rank-fraction `95%` upper bound is `0.3451602555029466`, the smallest raw-versus-alternative overlap `5%` lower bound is `0.7553062395308168`, and the smallest rank deficit is `37.71672810247446` bootstrap sigma. This is robustness to `3` specified diagonal norms, not evidence that correlated task duplicates were removed; its fallback review score remains N/F/I `4/6/4`.

Evidence for every number: `scripts/test_h016.py`; the eight official inputs, `10000`-bootstrap spectra, overlaps, task mapping, and conditions are in `/work1/ruixiangtang/rw761/data_mix_artifacts/H016/result.json`; command `sbatch slurm/h016_l0.sbatch`; Slurm job `384588`.

## H015 Continuation Verdict

H015/H016 establishes one reproducible descriptive fact: the affine response spectrum in the released Olmix `30M` swarms remains concentrated under `3` frozen diagonal codomain metrics. It does not yet establish a paper-level predictive mechanism or a better data-mixing method. H016's review score is `4/6/4`; the predictive-rank repair H017 scored `6/4/6`; the nonlinear-mechanism repair H018 scored `4/2/5` and received an overlap veto; the RankShareMix method repair H019 scored `5/5/4`. All `3` downstream lines stopped before testing, so completed downstream test count is `0` and validated new-method count is `0`.

The candidate-line extension used `0/60` MI210 node-hours. Evidence for the scores, veto, and zero submitted-test counts: `reviews/candidate_round5.json`, `reviews/candidate_round5_h017_repair.json`, `reviews/candidate_round5_h018_repair.json`, `reviews/candidate_round6_repair.json`, and the H017/H018/H019 stop entries in `EXPERIMENTS.md`; the `60`-node-hour ceiling is produced by `scripts/build_final_summary.py` from `protocol.json` and the candidate-line `30%` rule.

## CANDIDATE FINDING — H015

Across Olmix's official nested top-`m` 30M RQ2 swarms, the centered raw-BPB affine response has stable rank near `1.23` while nominal ilr dimension grows from `5` to `23`. Discovery rank fractions at `m=6/12` are `0.24628975134617892/0.11203295581408268`; independent `m=18/24` confirmation gives `0.07280427145046091/0.05332770154720674`. The smallest confirmation rank-deficit effect is `342.73550076880593` bootstrap sigma, and the stable-rank log-log slope is `-0.0030170525337915827` with `95%` upper bound `0.03448212813935515`. This is a raw-BPB global-OLS spectral measurement, not evidence that only one mixture direction is statistically identifiable or that swarm size can be reduced.

Evidence for every number: `scripts/test_h015.py`; the eight official inputs are listed in `/work1/ruixiangtang/rw761/data_mix_artifacts/H015/result.json`; command `sbatch slurm/h015_l0.sbatch`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H015/result.json`; Slurm job `384402`.

## CLOSED FINDING — H011

The literal displayed assumptions of GRAPE Theorem 2.2 admit strongly convex source and target losses whose raw target-loss variance increases at every finite iteration. Discovery gives first-step increase `0.15999999999999992`; independent `7`-dimensional forward-mode confirmation gives minimum analytic variance derivative `1.3333333333333333` on the invariant trajectory and update error `0`. Three exact repeats give sigma `0`, so the nonzero effect is `infinite` sigma. The scope is the displayed theorem: it does not establish failure under an unstated global-gradient interpretation.

Evidence for every number: `scripts/test_h011.py`; inputs are listed in `/work1/ruixiangtang/rw761/data_mix_artifacts/H011/result.json`; command `sbatch slurm/h011_l0.sbatch`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H011/result.json`; Slurm job `384367`.

Research status: closed. The theorem-audit result is retained, but this line receives no further experiment budget.

## CLOSED FINDING — H003

OP-MIX pretraining's fitted adapter coefficients are passed through the proxy table and final sampler as if they were effective data ratios. Discovery over `5` components gives median/max L1 coordinate error `0.1699068579672292/0.19997472781501544`; independent `7`-component confirmation gives `0.1775721961553033/0.19998872518171068`. Three exact repeats give sigma `0` in both splits, so both nonzero effects are `infinite` sigma. The continual path is a negative control because it stores effective ratios explicitly.

Evidence for every number: `scripts/test_h003.py`; inputs are the three source files listed in `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json`; command `sbatch slurm/h003_l0.sbatch`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json`; Slurm job `384365`.

Research status: closed. The implementation-audit result is retained, but this line receives no further experiment budget.

## CLOSED FINDING — H006

The literal displayed assumptions of GRAPE Theorem 2.1 admit a stationary-source counterexample. Discovery and independent `7`-dimensional automatic-differentiation confirmation each give target optimality gap `0.6321205588285577`, update norm `0`, and derivative-check error `0`; three exact repeats give sigma `0`, so the nonzero gap is `infinite` sigma. This finding is limited to the displayed theorem and does not test a strong-convexity repair or empirical GRAPE performance.

Evidence for every number: `scripts/test_h006.py`; inputs `/work1/ruixiangtang/rw761/data_mix_artifacts/paper_text/grape_2505.20380.txt` and `references/grape_2505.20380.pdf`; command `sbatch slurm/h006_l0.sbatch`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H006/result.json`; Slurm job `384364`.

Research status: closed. The theorem-audit result is retained, but this line receives no further experiment budget.

## Final Verdicts

| ID | Type | Level | Review N/F/I | Verdict | Research status | Supported effect (sigma) | Evidence |
|---|---|---:|---:|---|---|---:|---|
| H002 | measurement | L0 | `8/6/7` | `inconclusive` | `complete` | n/a | `/work1/ruixiangtang/rw761/data_mix_artifacts/H002/result.json` |
| H003 | audit | L0 | `9/6/7` | `supported` | `closed` | `infinite` | `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json` |
| H004 | audit | L0 | `8/5/8` | `falsified` | `complete` | n/a | `/work1/ruixiangtang/rw761/data_mix_artifacts/H004/result.json` |
| H006 | audit | L0 | `7/9/6` | `supported` | `closed` | `infinite` | `/work1/ruixiangtang/rw761/data_mix_artifacts/H006/result.json` |
| H007 | audit | L0 | `5/7/6` | `falsified` | `complete` | n/a | `/work1/ruixiangtang/rw761/data_mix_artifacts/H007/result.json` |
| H011 | audit | L0 | `6/8/7` | `supported` | `closed` | `infinite` | `/work1/ruixiangtang/rw761/data_mix_artifacts/H011/result.json` |
| H013 | measurement | L0 | `7/8/6` | `falsified` | `complete` | n/a | `/work1/ruixiangtang/rw761/data_mix_artifacts/H013/result.json` |
| H014 | constructive | L0 | `6/8/7` | `inconclusive` | `complete` | n/a | `/work1/ruixiangtang/rw761/data_mix_artifacts/H014/result.json` |
| H015 | measurement | L0 | `6/7/5` | `supported` | `candidate` | `342.73550076880593` | `/work1/ruixiangtang/rw761/data_mix_artifacts/H015/result.json` |
| H016 | measurement | L0 | `4/6/4` | `supported` | `candidate` | `37.71672810247446` | `/work1/ruixiangtang/rw761/data_mix_artifacts/H016/result.json` |

Completion audit: `10` reviewed, pre-registered hypotheses completed at L0, comprising `5` supported, `3` falsified, and `2` inconclusive. Audit hypotheses are `5/10 = 0.5`, below the `0.60` ceiling; `5` completed hypotheses are measurement or constructive, above the required `2`. The assumption inventory passes with `27` assumptions across `13` methods and maximum method share `0.1111111111111111`. GPU use is `0/200` MI210 node-hours, and literature expansion is `15/15` papers.

Research portfolio: H003, H006, and H011 are closed; H015 is the primary candidate line and H016 is its codomain-norm robustness result. Closure changes research allocation, not the recorded experimental verdicts.

## Stopped Continuation Gates

| ID | Type | Final review N/F/I | Overlap veto | Submitted tests | Disposition | Evidence |
|---|---|---:|---:|---:|---|---|
| H017 v2 | measurement | `6/4/6` | no | `0` | repair exhausted; undefined zero handling and invalid nested uncertainty | `reviews/candidate_round5_h017_repair.json` |
| H018 v2 | measurement | `4/2/5` | yes | `0` | repair exhausted; task-unit mismatch and prior-work overlap | `reviews/candidate_round5_h018_repair.json` |
| H019 v2 | constructive | `5/5/4` | no | `0` | repair exhausted; reused evaluation set, miscalibrated inference, underdefined baselines/optimizer | `reviews/candidate_round6_repair.json` |

Every score, veto, test count, and disposition in this table is recorded by the cited review JSON and the corresponding append-only H017/H018/H019 stop entry in `EXPERIMENTS.md`.

## Next Minimum Upgrade

H015: the minimum evidentiary upgrade is a newly reviewed L1 hypothesis using `20` newly trained mixtures, `14` fit mixtures, `6` untouched mixture coordinates, and `3` independent training seeds per mixture, for at most `60` jobs. Rank-`2` prediction must beat every frozen same-budget baseline on every untouched split by at least `2` training-seed sigma. This is a new hypothesis requirement, not permission to resubmit H017 or H019 after their `1/1` repairs.

H016: propagate item-level benchmark uncertainty on an untouched validation corpus with `3` codomain norms, `3` training seeds, and at least `100` untouched tasks. Every norm must retain a rank-fraction upper `95%` bound at most `0.60`, and the leading rank-`2` overlap lower `5%` bound must remain at least `0.60`.

Evidence for every number in the final table, completion audit, line status, and upgrade design: `scripts/build_final_summary.py`; inputs `protocol.json`, `artifacts/assumptions_check.json`, `reviews/candidate_round1.json` through `reviews/candidate_round5.json`, and the `10` result JSON files listed in `artifacts/final_summary.json`; command `sbatch slurm/final_summary.sbatch`; output `artifacts/final_summary.json`.
