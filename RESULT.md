# Results

## CANDIDATE FINDING - H016

H015's affine response concentration survives `3` frozen output metrics on the same `110` official Olmix tasks: raw BPB, task-standardized BPB, and equal-family-quadratic weighting over Math/Code/QA task counts `7/19/84`. Across `m=6/12/18/24`, all `12/12` rank conditions and `8/8` rank-`2` overlap conditions pass. The largest rank-fraction `95%` upper bound is `0.3451602555029466`, the smallest raw-versus-alternative overlap `5%` lower bound is `0.7553062395308168`, and the smallest rank deficit is `37.71672810247446` bootstrap sigma. This is robustness to `3` specified diagonal norms, not evidence that correlated task duplicates were removed; its fallback review score remains N/F/I `4/6/4`.

Evidence for every number: `scripts/test_h016.py`; the eight official inputs, `10000`-bootstrap spectra, overlaps, task mapping, and conditions are in `/work1/ruixiangtang/rw761/data_mix_artifacts/H016/result.json`; command `sbatch slurm/h016_l0.sbatch`; Slurm job `384588`.

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

Completion audit: `10` reviewed, pre-registered hypotheses completed at L0, comprising `5` supported, `3` falsified, and `2` inconclusive. Audit hypotheses are `5/10 = 0.5`, below the `0.60` ceiling; `5` completed hypotheses are measurement or constructive, above the required `2`. The assumption inventory passes with `27` assumptions across `13` methods and maximum method share `0.1111111111111111`. GPU use is `0/200` MI210 node-hours, and literature expansion is `13/15` papers.

Research portfolio: H003, H006, and H011 are closed; H015 is the primary candidate line and H016 is its codomain-norm robustness result. Closure changes research allocation, not the recorded experimental verdicts.

## Next Minimum Upgrade

H015: remain at L0 and repeat the frozen spectrum analysis under `3` codomain norms: raw BPB, z-scored BPB, and task-family-aggregated BPB, using `10000` bootstraps per norm. Norm robustness requires every rank-fraction `95%` upper bound to be at most `0.60` and every slope `95%` upper bound to be at most `0.75`.

Evidence for every number in the final table, completion audit, line status, and upgrade design: `scripts/build_final_summary.py`; inputs `protocol.json`, `artifacts/assumptions_check.json`, `reviews/candidate_round1.json` through `reviews/candidate_round4.json`, and the nine result JSON files listed in `artifacts/final_summary.json`; command `sbatch slurm/final_summary.sbatch`; Slurm job `384549`, output `artifacts/final_summary.json`.
