#!/usr/bin/env bash
set -euo pipefail

destination="/work1/ruixiangtang/rw761/awesome-pretraining/data_mix/references"
curl -L --fail --retry 3 "https://arxiv.org/pdf/1801.07922" \
  --output "$destination/vector_dimension_reduction_1801.07922.pdf"
curl -L --fail --retry 3 "https://arxiv.org/pdf/2401.02735" \
  --output "$destination/shared_active_subspace_2401.02735.pdf"
curl -L --fail --retry 3 "https://arxiv.org/pdf/1907.11572" \
  --output "$destination/sequential_active_subspaces_1907.11572.pdf"
sha256sum \
  "$destination/vector_dimension_reduction_1801.07922.pdf" \
  "$destination/shared_active_subspace_2401.02735.pdf" \
  "$destination/sequential_active_subspaces_1907.11572.pdf"
