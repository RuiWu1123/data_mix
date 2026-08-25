# Two-Dial End-to-End Protocol

Protocol ID is `TWODIAL-E2E-V1`; execution order is R1 then R2 then R3, with no confirmation pause. R1 has a `2` hour wall-clock ceiling; R2 targets `4` arms times `3` paired seeds = `12` completed training jobs and requires at least `10` jobs with all `13` validation losses. Every number and rule is validated by `scripts/check_rank2_protocol.py`; inputs `rank2_protocol.json` and this file; command `sbatch slurm/check_rank2_protocol.sbatch`; output `artifacts/rank2_protocol_check.json`.

## Frozen model

The only claim is `loss(w,t) = c_t + g(w) a_t + h(w) b_t + noise`, with `2` shared linear directions in zero-safe Hellinger mixture coordinates and task scalars `a_t,b_t`. Hellinger is selected because it maps exact-zero mixture cells without adding a replacement hyperparameter. Every count and definition is validated by `scripts/check_rank2_protocol.py`; inputs, command, and output are the protocol-check inputs, command, and output above.

## R1 gate

Five SHA folds evaluate rank-constrained OLS at ranks `1` through `6`, full OLS, and ExtraTrees with `500` trees and leaf size `2`. The metric is pooled task-standardized heldout RMSE. DataDecide final-step multi-seed `log(perplexity)` supplies `sigma_DD`, defined as the median seed standard error across eligible recipe-model-task cells with at least `2` seeds. Every number and estimator setting is validated by `scripts/check_rank2_protocol.py`; inputs, command, and output are listed above.

Rank `2` passes one source only when its error is within `0.5 sigma_DD` of the better full/ExtraTrees baseline, rank `1` minus rank `2` is at least `1.0 sigma_DD`, and rank `2` minus rank `3` is at most `0.5 sigma_DD`. Passing at least `2/3` sources yields `rank2-sufficient`; rank `1` within `0.5 sigma_DD` of the best baseline in at least `2/3` sources yields `rank1-sufficient`; otherwise the result is `rank3+-sufficient`. Every threshold and vote count is validated by `scripts/check_rank2_protocol.py`; inputs, command, and output are listed above.

## R2 contest

Training reuses RegMix commit `dd9d1c3b2d7c1756b1a90f0ad7603068e9856cc6`: its `tinyllama_1M` model, GPT-NeoX tokenizer, packed preprocessing, `PackedDataset`, and `CombinedDataset` mixture sampler. Each job uses sequence length `2048`, global/device batches `512/16`, `954` optimizer steps, `1000341504` tokens, `100` warmup steps, learning rate `0.0004` to `0.00001`, AdamW betas `0.9/0.95`, weight decay `0.1`, gradient clip `1.0`, bf16 mixed precision, `1` GPU, and a `4` hour limit. Every number and upstream pin is validated by `scripts/check_rank2_protocol.py`; inputs, command, and output are listed above.

The `4` frozen arm constructors are selected-rank RegMix, ExtraTrees, official RegMix, and an h-axis probe. The probe is chosen among released candidates at L1 distance `0.20` to `0.60` from the selected-rank mixture after orienting h by code/math versus Pile-CC/Wikipedia task loadings. Seeds are `3406/3407/3408`; evaluation reports cross entropy and BPB on `13` released RegMix validation domains using `50` batches per domain. Every number and arm rule is validated by `scripts/check_rank2_protocol.py`; inputs, command, and output are listed above.

Support requires the `10`-job gate, at least `2` seeds per arm, selected-rank minus ExtraTrees loss at most `0.5` paired sigma, improvement over official RegMix at least `1.0` paired sigma, predicted/observed task-effect cosine at least `0.70`, sign agreement at least `10/13`, and opposite code/math versus Pile-CC/Wikipedia changes each at least `1.0` paired sigma. Falsification requires the completion gate plus degradation versus ExtraTrees above `1.0` sigma, direction cosine below `0`, or sign agreement at most `6/13`; otherwise the scientific result is inconclusive. Fewer than `10` complete jobs after at most `3` attempts per arm-seed is incomplete. Every threshold, count, and retry rule is validated by `scripts/check_rank2_protocol.py`; inputs, command, and output are listed above.

## R3 output

R3 must include the rank-error curve with both baselines and `sigma_DD`, all GPU job numbers and sigma effects, a conclusion of at most `200` words, and a minimum upgrade. The required artifact count and word ceiling are validated by `scripts/check_rank2_protocol.py`; inputs, command, and output are listed above.
