# Variables de la cuenta non-prod. Leídas por root.hcl.
locals {
  account_name   = "non-prod"
  aws_account_id = get_env("TG_NON_PROD_ACCOUNT_ID", "000000000000") # TODO: reemplazar por el ID real
}
