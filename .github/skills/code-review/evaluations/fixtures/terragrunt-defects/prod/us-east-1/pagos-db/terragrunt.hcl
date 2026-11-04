include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source = "git::git@github.com:TODO-org/infrastructure-catalog.git//modules/aurora-postgresql?ref=main"
}

dependency "red" {
  config_path = "../red"

  mock_outputs = {
    vpc_id             = "vpc-00000000"
    private_subnet_ids = ["subnet-00000000"]
  }
  mock_outputs_allowed_terraform_commands = ["validate", "plan", "apply"]
}

inputs = {
  name            = "pagos-prod"
  engine_version  = "16.4"
  vpc_id          = dependency.red.outputs.vpc_id
  subnet_ids      = dependency.red.outputs.private_subnet_ids
  master_username = "pagos_admin"
  master_password = "Pagos2026!Prod"
}
