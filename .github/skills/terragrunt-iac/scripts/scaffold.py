#!/usr/bin/env python3
"""scaffold — genera el esqueleto de un repo Terragrunt 1.x (live con stacks o catálogo).

Ejemplos:
  python scaffold.py --tipo live --nube aws   --destino ./infrastructure-live --ambientes non-prod,prod --region us-east-1 --ci github
  python scaffold.py --tipo live --nube azure --destino ./live --ambientes dev,qa,prod --region eastus2 --ci azure-devops
  python scaffold.py --tipo catalog --destino ./infrastructure-catalog
Los valores a completar quedan marcados con TODO. Luego: terragrunt hcl fmt && python tg_lint.py <destino>
"""
import argparse
import os
import shutil
import sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(SKILL, "assets")
TG_VERSION, TOFU_VERSION = "1.2.1", "1.13.1"

ROOT_COMMON_HEAD = '''# ---------------------------------------------------------------------------------------------------------------------
# CONFIGURACIÓN RAÍZ DE TERRAGRUNT — incluida por todos los units (provider, backend, catálogo)
# Dueño: TODO
# ---------------------------------------------------------------------------------------------------------------------

terragrunt_version_constraint = ">= 1.2.0, < 2.0.0"
'''

ROOT = {
    "aws": None,  # se copia assets/live-stacks/root.hcl
    "azure": ROOT_COMMON_HEAD + '''
locals {
  sub_vars    = read_terragrunt_config(find_in_parent_folders("sub.hcl"))
  region_vars = read_terragrunt_config(find_in_parent_folders("region.hcl"))

  sub_name        = local.sub_vars.locals.subscription_name
  subscription_id = local.sub_vars.locals.subscription_id
  tenant_id       = local.sub_vars.locals.tenant_id
  location        = local.region_vars.locals.location

  tags = {
    managed_by  = "terragrunt"
    environment = local.sub_name
  }
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOT
provider "azurerm" {
  features {}
  subscription_id = "${local.subscription_id}"
  tenant_id       = "${local.tenant_id}"
}
EOT
}

remote_state {
  backend = "azurerm"
  config = {
    subscription_id      = local.subscription_id
    resource_group_name  = "rg-tfstate-${local.sub_name}"
    storage_account_name = "sttfstate${replace(local.sub_name, "-", "")}" # TODO: 3-24 caracteres, único global
    container_name       = "tfstate"
    key                  = "${path_relative_to_include()}/tofu.tfstate"
    use_azuread_auth     = true

    # Solo bootstrap (no se pasan a OpenTofu)
    location                   = local.location
    account_replication_type   = "GRS"
    enable_soft_delete         = true
    soft_delete_retention_days = 30
  }
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
}
''',
    "gcp": ROOT_COMMON_HEAD + '''
locals {
  project_vars = read_terragrunt_config(find_in_parent_folders("project.hcl"))
  region_vars  = read_terragrunt_config(find_in_parent_folders("region.hcl"))

  project_name = local.project_vars.locals.project_name
  project_id   = local.project_vars.locals.project_id
  region       = local.region_vars.locals.region
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite_terragrunt"
  contents  = <<EOT
provider "google" {
  project = "${local.project_id}"
  region  = "${local.region}"

  default_labels = {
    managed_by  = "terragrunt"
    environment = "${local.project_name}"
  }
}
EOT
}

remote_state {
  backend = "gcs"
  config = {
    project  = local.project_id
    location = "us"
    bucket   = "tfstate-${local.project_id}"
    prefix   = path_relative_to_include()
  }
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite_terragrunt"
  }
}
''',
}

LEVEL1 = {
    "aws": ("account.hcl", 'locals {{\n  account_name   = "{env}"\n  aws_account_id = get_env("TG_{ENV}_ACCOUNT_ID", "000000000000") # TODO\n}}\n'),
    "azure": ("sub.hcl", 'locals {{\n  subscription_name = "{env}"\n  # TODO: definir TG_{ENV}_SUBSCRIPTION_ID y TG_TENANT_ID o reemplazar por valores fijos\n  subscription_id = get_env("TG_{ENV}_SUBSCRIPTION_ID", "00000000-0000-0000-0000-000000000000")\n  tenant_id       = get_env("TG_TENANT_ID", "00000000-0000-0000-0000-000000000000")\n}}\n'),
    "gcp": ("project.hcl", 'locals {{\n  project_name = "{env}"\n  project_id   = get_env("TG_{ENV}_PROJECT_ID", "todo-{env}") # TODO\n}}\n'),
}
REGION = {
    "aws": 'locals {{\n  aws_region = "{region}"\n}}\n',
    "azure": 'locals {{\n  location = "{region}"\n}}\n',
    "gcp": 'locals {{\n  region = "{region}"\n}}\n',
}
STACK_GENERIC = '''# Stack "{stack}" en {env}. Reemplaza las fuentes por units de tu catálogo.

locals {{
  catalog = "git::git@github.com:TODO-org/infrastructure-catalog.git"
  version = "v0.1.0" # TODO: tag del catálogo
  nombre  = "{stack}-{env}"
}}

unit "base" {{
  source = "${{local.catalog}}//units/TODO-base?ref=${{local.version}}"
  path   = "base"

  values = {{
    version = local.version
    name    = local.nombre
  }}
}}
'''


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def live(a):
    d = a.destino
    envs = [e.strip() for e in a.ambientes.split(",") if e.strip()]
    lv = os.path.join(ASSETS, "live-stacks")
    for f in (".gitignore", ".terragrunt-filters"):
        shutil.copy(os.path.join(lv, f), os.path.join(d, f))
    write(os.path.join(d, "mise.toml"), f'[tools]\nterragrunt = "{TG_VERSION}"\nopentofu   = "{TOFU_VERSION}"\n')
    if a.nube == "aws":
        shutil.copy(os.path.join(lv, "root.hcl"), os.path.join(d, "root.hcl"))
    else:
        write(os.path.join(d, "root.hcl"), ROOT[a.nube])
    fname, tpl = LEVEL1[a.nube]
    for env in envs:
        ENV = env.upper().replace("-", "_")
        write(os.path.join(d, env, fname), f"# Variables de {env}. Leídas por root.hcl.\n" + tpl.format(env=env, ENV=ENV))
        rdir = os.path.join(d, env, a.region)
        write(os.path.join(rdir, "region.hcl"), "# Variables de la región. Leídas por root.hcl.\n" + REGION[a.nube].format(region=a.region))
        if a.nube == "aws":
            src = os.path.join(lv, "non-prod", "us-east-1", "servicio-ejemplo", "terragrunt.stack.hcl")
            txt = open(src, encoding="utf-8").read().replace("non-prod", env)
            write(os.path.join(rdir, a.stack, "terragrunt.stack.hcl"), txt.replace("servicio-ejemplo", a.stack))
        else:
            write(os.path.join(rdir, a.stack, "terragrunt.stack.hcl"), STACK_GENERIC.format(stack=a.stack, env=env))
    wf = os.path.join(ASSETS, "workflows")
    if a.ci == "github":
        for f in ("terragrunt-github-actions.yml", "terragrunt-drift.yml"):
            dst = os.path.join(d, ".github", "workflows", f)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            txt = open(os.path.join(wf, f), encoding="utf-8").read()
            txt = txt.replace("LIVE_DIR: live", "LIVE_DIR: .").replace("working-directory: live", "working-directory: .")
            txt = txt.replace("(./${LIVE_DIR})...", "").replace("./${LIVE_DIR}/", "./")
            txt = txt.replace("[non-prod, prod]", "[" + ", ".join(envs) + "]").replace('"live/**", ', "")
            write(dst, txt)
    elif a.ci == "azure-devops":
        txt = open(os.path.join(wf, "azure-pipelines-terragrunt.yml"), encoding="utf-8").read()
        txt = txt.replace("LIVE_DIR: live", "LIVE_DIR: .").replace("(./$(LIVE_DIR))...", "").replace("./$(LIVE_DIR)/", "./")
        if "non-prod" not in envs:  # la plantilla trae stages non-prod → prod; adapta el primero
            txt = txt.replace("(./non-prod)", f"(./{envs[0]})").replace("environment: non-prod", f"environment: {envs[0]}")
        if "prod" not in envs:
            txt = txt.replace("(./prod)", f"(./{envs[-1]})").replace("environment: prod", f"environment: {envs[-1]}")
        write(os.path.join(d, "azure-pipelines.yml"), txt)
        shutil.copytree(os.path.join(wf, "templates"), os.path.join(d, "templates"), dirs_exist_ok=True)
    write(os.path.join(d, "README.md"),
          f"# infrastructure-live ({a.nube})\n\nGenerado con la skill terragrunt-iac.\n\n```bash\nmise install\n"
          f"cd {envs[0]}/{a.region}/{a.stack}\nterragrunt run --all --non-interactive --backend-bootstrap -- plan\n```\n\n"
          "Completa los valores marcados con `TODO` y registra las decisiones en `Linea_Base_<Proyecto>.md`.\n")


def catalog(a):
    shutil.copytree(os.path.join(ASSETS, "catalog"), a.destino, dirs_exist_ok=True)
    write(os.path.join(a.destino, "README.md"),
          "# infrastructure-catalog\n\n`modules/` (OpenTofu) → `units/` (Terragrunt, leen `values`) → `stacks/` (composición).\n"
          "Publica versiones con tags semver y referencia `?ref=vX.Y.Z` desde live.\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tipo", choices=["live", "catalog"], required=True)
    ap.add_argument("--nube", choices=["aws", "azure", "gcp"], default="aws")
    ap.add_argument("--destino", required=True)
    ap.add_argument("--ambientes", default="non-prod,prod")
    ap.add_argument("--region", default=None)
    ap.add_argument("--stack", default="servicio-ejemplo")
    ap.add_argument("--ci", choices=["github", "azure-devops", "ninguno"], default="github")
    a = ap.parse_args()
    a.region = a.region or {"aws": "us-east-1", "azure": "eastus2", "gcp": "us-east1"}[a.nube]
    if os.path.exists(a.destino) and os.listdir(a.destino):
        sys.exit(f"El destino {a.destino} no está vacío; elige otro para no sobrescribir.")
    os.makedirs(a.destino, exist_ok=True)
    (live if a.tipo == "live" else catalog)(a)
    if shutil.which("terragrunt"):
        import subprocess
        subprocess.run(["terragrunt", "hcl", "fmt", "--log-level", "error", "--working-dir", a.destino], check=False)
    print(f"Esqueleto {a.tipo} generado en {a.destino}")


if __name__ == "__main__":
    main()
