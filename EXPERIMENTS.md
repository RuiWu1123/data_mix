# Append-Only Experiment Ledger

Historical entries below must never be edited or deleted. Corrections are new entries that cite the superseded entry.

## Literature additions

- ADD-REF-DOREMI — DoReMi: Optimizing Data Mixtures Speeds Up Language Model Pretraining. Reason: foundational comparator explicitly required by the task and directly attacked by Aioli and Olmix. Evidence: `scripts/reference_inventory.py`; input `references/doremi_2305.10429.pdf`; command `python scripts/reference_inventory.py --references references --vendor vendor --output artifacts/reference_inventory.json`.
- ADD-REF-DOGE — DoGE: Domain Reweighting with Generalization Estimation. Reason: foundational gradient-based mixing method explicitly required by the task and directly analyzed by Aioli and Olmix. Evidence: `scripts/reference_inventory.py`; input `references/doge_2310.15393.pdf`; command `python scripts/reference_inventory.py --references references --vendor vendor --output artifacts/reference_inventory.json`.
- ADD-REF-DATADECIDE — DataDecide: How to Predict Best Pretraining Data with Small Experiments. Reason: released multi-scale, multi-seed results enable zero-GPU tests of mixing transfer assumptions. Evidence: `scripts/reference_inventory.py`; input `references/datadecide_2504.11393.pdf`; command `python scripts/reference_inventory.py --references references --vendor vendor --output artifacts/reference_inventory.json`.
