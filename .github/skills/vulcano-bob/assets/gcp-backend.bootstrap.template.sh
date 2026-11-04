#!/usr/bin/env bash
set -euo pipefail

: "${GCP_PROJECT_ID:?GCP_PROJECT_ID is required}"
: "${GCP_REGION:?GCP_REGION is required}"
: "${TFSTATE_BUCKET:?TFSTATE_BUCKET is required}"

if ! gcloud storage buckets describe "gs://$TFSTATE_BUCKET" --project "$GCP_PROJECT_ID" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://$TFSTATE_BUCKET" \
    --project "$GCP_PROJECT_ID" \
    --location "$GCP_REGION" \
    --uniform-bucket-level-access \
    --public-access-prevention
fi

gcloud storage buckets update "gs://$TFSTATE_BUCKET" --versioning

if [[ -n "${TFSTATE_KMS_KEY:-}" ]]; then
  gcloud storage buckets update "gs://$TFSTATE_BUCKET" --default-encryption-key "$TFSTATE_KMS_KEY"
fi

printf 'state_bucket=%s\nstate_prefix=terraform\nstate_locking=gcs_native\n' "$TFSTATE_BUCKET"
