# Results

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
