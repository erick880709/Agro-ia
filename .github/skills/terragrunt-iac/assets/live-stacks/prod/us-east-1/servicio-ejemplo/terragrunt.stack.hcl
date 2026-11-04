# Stack "servicio-ejemplo" en prod. Compone units del catálogo con values del ambiente.
# Promoción: non-prod adopta primero la nueva versión del catálogo; prod la sigue en un PR aparte.

locals {
  catalog = "git::git@github.com:TODO-org/infrastructure-catalog.git"
  version = "v1.0.0"
  nombre  = "servicio-ejemplo-prod"
}

unit "tabla" {
  source = "${local.catalog}//units/ejemplo-tabla?ref=${local.version}"
  path   = "tabla"

  values = {
    version  = local.version
    name     = "${local.nombre}-tabla"
    hash_key = "Id"
  }
}

unit "servicio" {
  source = "${local.catalog}//units/ejemplo?ref=${local.version}"
  path   = "servicio"

  values = {
    version            = local.version
    name               = local.nombre
    visibility_timeout = 512
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
