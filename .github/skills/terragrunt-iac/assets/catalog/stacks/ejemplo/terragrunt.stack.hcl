# Stack de catálogo: servicio de ejemplo + su tabla.
# Uso desde live:
#   stack "ejemplo" {
#     source = "git::git@github.com:TODO-org/infrastructure-catalog.git//stacks/ejemplo?ref=v1.2.0"
#     path   = "ejemplo"
#     values = { name = "pagos-dev" }
#   }

locals {
  name = values.name
}

unit "tabla" {
  source                 = "../..//units/ejemplo-tabla"
  update_source_with_cas = true
  path                   = "tabla"

  values = {
    name     = "${local.name}-tabla"
    hash_key = try(values.hash_key, "Id")
  }
}

unit "servicio" {
  source                 = "../..//units/ejemplo"
  update_source_with_cas = true
  path                   = "servicio"

  values = {
    name               = local.name
    visibility_timeout = try(values.visibility_timeout, 30)
  }

  autoinclude {
    dependency "tabla" {
      config_path = unit.tabla.path

      mock_outputs = {
        name = "tabla-mock"
        arn  = "arn:aws:dynamodb:us-east-1:000000000000:table/tabla-mock"
      }
      mock_outputs_allowed_terraform_commands = ["validate", "plan", "init"]
    }

    inputs = {
      table_name = dependency.tabla.outputs.name
      table_arn  = dependency.tabla.outputs.arn
    }
  }
}
