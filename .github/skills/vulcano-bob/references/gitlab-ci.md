# Adaptador GitLab CI/CD

El renderer crea `.gitlab-ci.yml` y los includes `.gitlab/ci/iac.yml` y `.gitlab/ci/drift.yml`.

- Emitir un `id_token` con audience explícita y canjearlo por identidad Azure o AWS en runtime.
- Mantener variables sensibles limitadas por environment; no persistir tokens en artefactos.
- Conservar el plan siete días y aplicar exactamente `tfplan` desde el job dependiente.
- Declarar environment en cada apply/deploy y proteger producción antes de operar.
- Crear la programación real de drift mediante el operador; `DRIFT_CRON` liga el schedule remoto
  con el contrato renderizado.
- Drift nunca ejecuta `terraform apply`.

Fuentes oficiales: [ID tokens OIDC](https://docs.gitlab.com/ci/secrets/id_token_authentication/),
[sintaxis CI/CD](https://docs.gitlab.com/ci/yaml/) y
[protected environments](https://docs.gitlab.com/ci/environments/protected_environments/).
