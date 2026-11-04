#!/usr/bin/env bash
set -euo pipefail

: "${AWS_REGION:?AWS_REGION is required}"
: "${TFSTATE_BUCKET:?TFSTATE_BUCKET is required}"

if ! aws s3api head-bucket --bucket "$TFSTATE_BUCKET" >/dev/null 2>&1; then
  if [[ "$AWS_REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$TFSTATE_BUCKET" --region "$AWS_REGION"
  else
    aws s3api create-bucket --bucket "$TFSTATE_BUCKET" --region "$AWS_REGION" \
      --create-bucket-configuration "LocationConstraint=$AWS_REGION"
  fi
fi

aws s3api put-public-access-block --bucket "$TFSTATE_BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-versioning --bucket "$TFSTATE_BUCKET" --versioning-configuration Status=Enabled

if [[ -n "${TFSTATE_KMS_KEY_ID:-}" ]]; then
  encryption="{\"Rules\":[{\"ApplyServerSideEncryptionByDefault\":{\"SSEAlgorithm\":\"aws:kms\",\"KMSMasterKeyID\":\"$TFSTATE_KMS_KEY_ID\"},\"BucketKeyEnabled\":true}]}"
else
  encryption='{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
fi
aws s3api put-bucket-encryption --bucket "$TFSTATE_BUCKET" --server-side-encryption-configuration "$encryption"

printf 'state_bucket=%s\nstate_key_prefix=terraform\nstate_lockfile=true\n' "$TFSTATE_BUCKET"
