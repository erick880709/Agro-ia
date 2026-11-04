# Variables de prod. Leídas por root.hcl.
locals {
  account_name   = "prod"
  aws_account_id = get_env("TG_PROD_ACCOUNT_ID", "000000000000") # TODO
}
