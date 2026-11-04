# ---------------------------------------------------------------------------------------------------------------------
# CONFIGURACIÓN RAÍZ DE TERRAGRUNT
# Incluida por todos los units: genera provider y backend, y define el catálogo.
# Dueño: TODO equipo de plataforma
# ---------------------------------------------------------------------------------------------------------------------

terragrunt_version_constraint = ">= 1.2.0, < 2.0.0"

locals {
  account_vars = read_terragrunt_config(find_in_parent_folders("account.hcl"))
  region_vars  = read_terragrunt_config(find_in_parent_folders("region.hcl"))

  account_name = local.account_vars.locals.account_name
  account_id   = local.account_vars.locals.aws_account_id
  aws_region   = local.region_vars.locals.aws_region

  tags = {
    managed_by  = "terragrunt"
    environment = local.account_name
    repo        = "TODO-org/infrastructure-live"
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOT
provider "aws" {
  region              = "${local.aws_region}"
  allowed_account_ids = ["${local.account_id}"]

  default_tags {
    tags = ${jsonencode(local.tags)}
  }
}
EOT
}

remote_state {
  backend = "s3"
  config = {
    bucket       = "tfstate-${local.account_id}-${local.aws_region}-an"
    key          = "pagos/terraform.tfstate"
    region       = local.aws_region
    encrypt      = true
    use_lockfile = true
  }
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
}

catalog {
  urls = [
    "https://github.com/TODO-org/infrastructure-catalog",
  ]
}
