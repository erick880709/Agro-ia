# Adaptador GitHub Actions

El renderer crea tres workflows independientes en `.github/workflows/`: IaC, drift y aplicación.

- Ejecutar con `contents: read` e `id-token: write`; no usar PAT ni secretos cloud de larga vida.
- Autenticar Azure o AWS por OIDC usando variables de environment no sensibles.
- Separar `plan` de `apply`, publicar `tfplan-<environment>` y aplicar exactamente el plan descargado.
- Asociar despliegues a environments `dev`, `qa` y `prod`; sus protecciones se configuran con
  `vulcano-operador`.
- Drift solo usa `plan -detailed-exitcode`; nunca aplica.
- Prohibir `pull_request_target` en workflows que obtienen identidad cloud.
- Generar `scripts/ci-build.sh` y `scripts/ci-deploy.sh` desde la definición; no inventar comandos.

```powershell
node .claude/skills/vulcano-bob/scripts/render-bob-pipelines.mjs `
  --drift-cron "0 5 * * *" --terraform-version "1.14.3"
```

Fuentes oficiales: [OIDC en GitHub Actions](https://docs.github.com/en/actions/reference/security/oidc)
y [deployments y environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).
