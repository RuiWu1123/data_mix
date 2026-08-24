#!/usr/bin/env bash
set -euo pipefail

destination="${WORK:?WORK must be set}/data_mix_public/olmix_rq2"
base="https://huggingface.co/datasets/allenai/olmix/resolve/main"
mkdir -p "$destination"

for domains in 6 12 18; do
  source_dir="study/rq2/dclm_swarm_${domains}_topics"
  for name in ratios.csv metrics.csv meta.json; do
    curl -L --fail --retry 3 "$base/$source_dir/$name" \
      --output "$destination/m${domains}_${name}"
  done
done

for name in ratios.csv metrics.csv meta.json; do
  curl -L --fail --retry 3 "$base/dclm_swarm/$name" \
    --output "$destination/m24_${name}"
done

sha256sum "$destination"/* > "$destination/SHA256SUMS"
wc -l "$destination"/*.csv > "$destination/LINE_COUNTS"
