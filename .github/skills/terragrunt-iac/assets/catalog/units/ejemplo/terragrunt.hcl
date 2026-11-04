# Unit de catálogo: solo se usa desde un stack (lee `values`). No ejecutar aislado.
# La dependencia hacia la tabla la inyecta el stack mediante `autoinclude`.
include "root" {
  path = find_in_parent_folders("root.hcl")
}

terraform {
  source                 = "../..//modules/ejemplo"
  update_source_with_cas = true
}

inputs = {
  name               = values.name
  visibility_timeout = try(values.visibility_timeout, 30)
}
