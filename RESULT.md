# Results

## CANDIDATE FINDING — H015

Across Olmix's official nested top-`m` 30M RQ2 swarms, the centered raw-BPB affine response has stable rank near `1.23` while nominal ilr dimension grows from `5` to `23`. Discovery rank fractions at `m=6/12` are `0.24628975134617892/0.11203295581408268`; independent `m=18/24` confirmation gives `0.07280427145046091/0.05332770154720674`. The smallest confirmation rank-deficit effect is `342.73550076880593` bootstrap sigma, and the stable-rank log-log slope is `-0.0030170525337915827` with `95%` upper bound `0.03448212813935515`. This is a raw-BPB global-OLS spectral measurement, not evidence that only one mixture direction is statistically identifiable or that swarm size can be reduced.

Evidence for every number: `scripts/test_h015.py`; the eight official inputs are listed in `/work1/ruixiangtang/rw761/data_mix_artifacts/H015/result.json`; command `sbatch slurm/h015_l0.sbatch`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H015/result.json`; Slurm job `384402`.

## CANDIDATE FINDING — H011

The literal displayed assumptions of GRAPE Theorem 2.2 admit strongly convex source and target losses whose raw target-loss variance increases at every finite iteration. Discovery gives first-step increase `0.15999999999999992`; independent `7`-dimensional forward-mode confirmation gives minimum analytic variance derivative `1.3333333333333333` on the invariant trajectory and update error `0`. Three exact repeats give sigma `0`, so the nonzero effect is `infinite` sigma. The scope is the displayed theorem: it does not establish failure under an unstated global-gradient interpretation.

Evidence for every number: `scripts/test_h011.py`; inputs are listed in `/work1/ruixiangtang/rw761/data_mix_artifacts/H011/result.json`; command `sbatch slurm/h011_l0.sbatch`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H011/result.json`; Slurm job `384367`.

## CANDIDATE FINDING — H003

OP-MIX pretraining's fitted adapter coefficients are passed through the proxy table and final sampler as if they were effective data ratios. Discovery over `5` components gives median/max L1 coordinate error `0.1699068579672292/0.19997472781501544`; independent `7`-component confirmation gives `0.1775721961553033/0.19998872518171068`. Three exact repeats give sigma `0` in both splits, so both nonzero effects are `infinite` sigma. The continual path is a negative control because it stores effective ratios explicitly.

Evidence for every number: `scripts/test_h003.py`; inputs are the three source files listed in `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json`; command `sbatch slurm/h003_l0.sbatch`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json`; Slurm job `384365`.

## CANDIDATE FINDING — H006

The literal displayed assumptions of GRAPE Theorem 2.1 admit a stationary-source counterexample. Discovery and independent `7`-dimensional automatic-differentiation confirmation each give target optimality gap `0.6321205588285577`, update norm `0`, and derivative-check error `0`; three exact repeats give sigma `0`, so the nonzero gap is `infinite` sigma. This finding is limited to the displayed theorem and does not test a strong-convexity repair or empirical GRAPE performance.

Evidence for every number: `scripts/test_h006.py`; inputs `/work1/ruixiangtang/rw761/data_mix_artifacts/paper_text/grape_2505.20380.txt` and `references/grape_2505.20380.pdf`; command `sbatch slurm/h006_l0.sbatch`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H006/result.json`; Slurm job `384364`.

## Final Verdicts

| ID | Type | Level | Review N/F/I | Verdict | Supported effect (sigma) | Evidence |
|---|---|---:|---:|---|---:|---|
| H002 | measurement | L0 | `8/6/7` | `inconclusive` | n/a | `/work1/ruixiangtang/rw761/data_mix_artifacts/H002/result.json` |
| H003 | audit | L0 | `9/6/7` | `supported` | `infinite` | `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json` |
| H004 | audit | L0 | `8/5/8` | `falsified` | n/a | `/work1/ruixiangtang/rw761/data_mix_artifacts/H004/result.json` |
| H006 | audit | L0 | `7/9/6` | `supported` | `infinite` | `/work1/ruixiangtang/rw761/data_mix_artifacts/H006/result.json` |
| H007 | audit | L0 | `5/7/6` | `falsified` | n/a | `/work1/ruixiangtang/rw761/data_mix_artifacts/H007/result.json` |
| H011 | audit | L0 | `6/8/7` | `supported` | `infinite` | `/work1/ruixiangtang/rw761/data_mix_artifacts/H011/result.json` |
| H013 | measurement | L0 | `7/8/6` | `falsified` | n/a | `/work1/ruixiangtang/rw761/data_mix_artifacts/H013/result.json` |
| H014 | constructive | L0 | `6/8/7` | `inconclusive` | n/a | `/work1/ruixiangtang/rw761/data_mix_artifacts/H014/result.json` |
| H015 | measurement | L0 | `6/7/5` | `supported` | `342.73550076880593` | `/work1/ruixiangtang/rw761/data_mix_artifacts/H015/result.json` |

Completion audit: `9` reviewed, pre-registered hypotheses completed at L0, comprising `4` supported, `3` falsified, and `2` inconclusive. Audit hypotheses are `5/9 = 0.5555555555555556`, below the `0.60` ceiling; `4` completed hypotheses are measurement or constructive, above the required `2`. The assumption inventory passes with `27` assumptions across `13` methods and maximum method share `0.1111111111111111`. GPU use is `0/200` MI210 node-hours, and literature expansion is `10/15` papers.

## Next Minimum Upgrades

H003: run an L1 matched comparison of direct-coefficient and affine-corrected final samplers using `160000000` parameters, `3200000000` training tokens, `2` arms, and `3` seeds per arm. The correction advances only if mean target loss falls by at least `2` seed sigma and no domain loss rises by more than `1` sigma.

H006: remain at L0 and add an explicit source-target progress constant; property-test the repaired statement on `10000` strongly convex quadratic instances with minimum progress constant `0.1`. Any post-bound optimality gap above `1e-10` falsifies the repair.

H011: run an L1 GRAPE-versus-fixed-mixture proxy with `60000000` parameters, `7` target domains, `2` arms, and `3` seeds per arm, logging every `100` updates. The concern advances only if the GRAPE variance slope is positive by more than `2` seed sigma over the first `10` logged intervals.

H015: remain at L0 and repeat the frozen spectrum analysis under `3` codomain norms: raw BPB, z-scored BPB, and task-family-aggregated BPB, using `10000` bootstraps per norm. Norm robustness requires every rank-fraction `95%` upper bound to be at most `0.60` and every slope `95%` upper bound to be at most `0.75`.

Evidence for every number in the final table, completion audit, and upgrade designs: `scripts/build_final_summary.py`; inputs `protocol.json`, `artifacts/assumptions_check.json`, `reviews/candidate_round1.json` through `reviews/candidate_round4.json`, and the nine result JSON files listed in `artifacts/final_summary.json`; command `sbatch slurm/final_summary.sbatch`; Slurm job `384414`, output `artifacts/final_summary.json`.
