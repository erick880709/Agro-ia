# Unit de catálogo: solo se usa desde un stack (lee `values`). No ejecutar aislado.
include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source                 = "../..//modules/ejemplo-tabla"
  update_source_with_cas = true
}

inputs = {
  # Obligatorios
  name     = values.name
  hash_key = values.hash_key

  # Opcionales
  hash_key_type = try(values.hash_key_type, "S")
  billing_mode  = try(values.billing_mode, "PAY_PER_REQUEST")
}
