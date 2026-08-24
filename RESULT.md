# Results

## CANDIDATE FINDING — H011

The literal displayed assumptions of GRAPE Theorem 2.2 admit strongly convex source and target losses whose raw target-loss variance increases at every finite iteration. Discovery gives first-step increase `0.15999999999999992`; independent `7`-dimensional forward-mode confirmation gives minimum analytic variance derivative `1.3333333333333333` on the invariant trajectory and update error `0`. Three exact repeats give sigma `0`, so the nonzero effect is `infinite` sigma. The scope is the displayed theorem: it does not establish failure under an unstated global-gradient interpretation.

Evidence for every number: `scripts/test_h011.py`; inputs are listed in `/work1/ruixiangtang/rw761/data_mix_artifacts/H011/result.json`; command `sbatch slurm/h011_l0.sbatch`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H011/result.json`; Slurm job `384367`.

## CANDIDATE FINDING — H003

OP-MIX pretraining's fitted adapter coefficients are passed through the proxy table and final sampler as if they were effective data ratios. Discovery over `5` components gives median/max L1 coordinate error `0.1699068579672292/0.19997472781501544`; independent `7`-component confirmation gives `0.1775721961553033/0.19998872518171068`. Three exact repeats give sigma `0` in both splits, so both nonzero effects are `infinite` sigma. The continual path is a negative control because it stores effective ratios explicitly.

Evidence for every number: `scripts/test_h003.py`; inputs are the three source files listed in `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json`; command `sbatch slurm/h003_l0.sbatch`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H003/result.json`; Slurm job `384365`.

## CANDIDATE FINDING — H006

The literal displayed assumptions of GRAPE Theorem 2.1 admit a stationary-source counterexample. Discovery and independent `7`-dimensional automatic-differentiation confirmation each give target optimality gap `0.6321205588285577`, update norm `0`, and derivative-check error `0`; three exact repeats give sigma `0`, so the nonzero gap is `infinite` sigma. This finding is limited to the displayed theorem and does not test a strong-convexity repair or empirical GRAPE performance.

Evidence for every number: `scripts/test_h006.py`; inputs `/work1/ruixiangtang/rw761/data_mix_artifacts/paper_text/grape_2505.20380.txt` and `references/grape_2505.20380.pdf`; command `sbatch slurm/h006_l0.sbatch`; result `/work1/ruixiangtang/rw761/data_mix_artifacts/H006/result.json`; Slurm job `384364`.

The final verdict table is populated after all reviewed, pre-registered tests complete.
