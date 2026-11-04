# 10 — Testing y calidad

Contenido: pirámide de pruebas para catálogo y live, Terratest, pre-commit, linters, convenciones de código.

## 1. Niveles

| Nivel | Qué | Dónde | Herramienta |
|---|---|---|---|
| Estático | formato, sintaxis, patrones prohibidos | catálogo y live | `terragrunt hcl fmt --check`, `tofu fmt -check`, `terragrunt hcl validate`, `tflint`, `scripts/tg_lint.py`, `trivy config`/`checkov` |
| Contrato | inputs vs variables | live | `terragrunt hcl validate --inputs` |
| Plan | qué cambiaría | live (PR) | `run --all -- plan` filtrado |
| Integración | despliega, verifica, destruye | catálogo (`examples/`) | Terratest (Go) |
| Unitario de módulo | lógica de variables/outputs sin nube | módulos | `tofu test` (`*.tftest.hcl`) con `mock_provider` |
| Drift | realidad vs código | live (cron) | `plan -detailed-exitcode` |

## 2. Terratest en el catálogo (patrón Gruntwork)

```go
// test/terragrunt/units/lambda_service_test.go
func TestLambdaServiceUnit(t *testing.T) {
    t.Parallel()
    dir := test_structure.CopyTerraformFolderToTemp(t, "../../..", "examples/terragrunt/units/lambda-service")
    opts := &terraform.Options{
        TerraformDir:    dir,
        TerraformBinary: "terragrunt",
        Vars:            map[string]interface{}{},
        EnvVars:         map[string]string{"TG_NON_INTERACTIVE": "true"},
    }
    defer terraform.Destroy(t, opts)
    terraform.InitAndApply(t, opts)
    url := terraform.Output(t, opts, "url")
    http_helper.HttpGetWithRetry(t, url, nil, 200, "Hello", 10, 5*time.Second)
}
```

- Un test por módulo (`examples/tofu/<m>`), por unit (`examples/terragrunt/units/<u>`) y por stack (`examples/terragrunt/stacks/<s>`).
- Nombres únicos por ejecución (`random.UniqueId()` → prefijos) para correr en paralelo; cuenta sandbox dedicada; `cloud-nuke` periódico.
- En CI del catálogo: tests en PR para lo modificado; release (tag) solo si pasan.

## 3. pre-commit

```yaml
repos:
  - repo: https://github.com/gruntwork-io/pre-commit
    rev: v0.1.30      # pinear
    hooks:
      - id: terragrunt-hcl-fmt
      - id: tofu-fmt
      - id: tflint
  - repo: local
    hooks:
      - id: tg-lint
        name: tg-lint
        entry: python scripts/tg_lint.py
        language: system
        pass_filenames: false
```

## 4. Convenciones de código

- Nombres de carpetas en kebab-case; nombres de units = recurso lógico (`vpc`, `rds-pagos`), no tecnología + ambiente.
- Etiquetas de bloques en snake_case (`dependency "vpc_core"`).
- Comentarios en cabecera de `root.hcl` y de cada stack: propósito, dueño, enlaces.
- `inputs` solo con lo que cambia; defaults en el módulo.
- `try(values.x, default)` para opcionales en units de catálogo; obligatorios sin `try` (fallan temprano).
- Tags/labels comunes en `root.hcl` (`default_tags` del provider): `owner`, `cost_center`, `environment`, `managed_by = "terragrunt"`, `repo`.
- README por módulo con inputs/outputs (`terraform-docs`).
