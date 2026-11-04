# Cadena de suministro y secretos

## Tabla de contenido

1. Dependencias: método
2. Por ecosistema
3. SBOM y procedencia
4. Secretos: encontrar
5. Secretos: responder
6. Secretos: postura

## 1. Dependencias: método

1. Inventaria manifiestos y **lockfiles**; sin lockfile, la versión evaluada es una
   suposición: decláralo.
2. Ejecuta el escáner del ecosistema (abajo) y OSV-Scanner como transversal.
3. Para cada advisory: ¿la dependencia llega al runtime (no solo build/test)? ¿la función
   vulnerable es alcanzable desde el código? (govulncheck lo calcula; en Java/JS traza
   manualmente el uso). Sin alcanzabilidad: `needs_validation` o hardening, no high.
4. Señales de explotación: CISA KEV y EPSS cuando haya red; si no, `no verificado`.
5. Ruta de remedio: ¿parche, menor o mayor? ¿hay versión corregida? Si es transitiva,
   override/constraint (`dependencyManagement`, `resolutionStrategy`, `overrides` de npm).
6. Riesgo no-CVE: paquetes abandonados/archivados, nombres parecidos (typosquatting),
   repositorios Maven/npm no oficiales, versiones dinámicas, scripts de instalación.

Reglas de lectura (Trail of Bits): **dato no disponible no es evidencia de riesgo; una
medición ausente no es un veredicto limpio.** Cita las cifras de la herramienta tal cual.

## 2. Por ecosistema

| Ecosistema | Escáner | Notas |
|---|---|---|
| Java (Maven/Gradle) | OWASP Dependency-Check, `osv-scanner`, Snyk/Dependabot si existen | Revisa `repositories {}` no oficiales y versiones `+`/`latest.release` |
| Go | `govulncheck ./...` | Alcanzabilidad incluida; `GOFLAGS=-mod=mod` cambia lo resuelto |
| npm (Angular) | `npm audit --omit=dev`, `osv-scanner -L package-lock.json` | `npm ci --ignore-scripts` si el build lo permite |
| Contenedores | `trivy image`, `grype` | Imagen base y paquetes del SO |
| Terraform | `tofu providers lock`, `.terraform.lock.hcl` versionado | Módulos por tag/SHA |

## 3. SBOM y procedencia

- SBOM CycloneDX o SPDX por artefacto (Syft, `cyclonedx-gradle-plugin`,
  `@cyclonedx/cyclonedx-npm`); el formato y la etapa los decide Vulcano si existe.
- Firma y procedencia (Sigstore/cosign, attestations SLSA) para imágenes y artefactos de
  release; verificación en el despliegue, no solo firma en el build.

## 4. Secretos: encontrar

- Barrido de alta confianza por prefijos de proveedor (AWS `AKIA/ASIA`, GitHub `ghp_`/
  `github_pat_`, Slack `xox`, Google `AIza`, Stripe `sk_live_`, Anthropic `sk-ant-`,
  llaves privadas `-----BEGIN ... PRIVATE KEY-----`, connection strings con `Password=`).
  `scripts/sec_triage.py` lo hace con valores **enmascarados**.
- Historial: `gitleaks git` / `trufflehog git` sobre todo el historial; un secreto borrado
  en el último commit sigue expuesto.
- Fuera del código: imágenes de contenedor (capas), artefactos de build, logs de CI,
  estado de Terraform, notebooks, `.env` de ejemplo, wikis y tickets.
- Nunca imprimas el valor: lista archivos (`-l`) o enmascara primeros/últimos 4.

## 5. Secretos: responder

Un secreto real expuesto es **rotación obligatoria** aunque se borre del repo:
1. Rotar/revocar en el proveedor (primero; borrar del historial no revoca nada).
2. Revisar uso indebido en logs del proveedor desde la fecha del commit.
3. Mover a gestor (Secrets Manager, Key Vault, Vault, Secret Manager) y referenciar en
   runtime (Scaffold: adapter `secrets`).
4. Limpiar historial solo si la política lo exige (`git filter-repo`) y coordinar con el
   equipo; no sustituye la rotación.
5. Añadir prevención: pre-commit (gitleaks), push protection del proveedor, regla en CI.

Severidad: secreto productivo con permisos de escritura → critical; de solo lectura de
datos sensibles → high; de entorno aislado sin datos reales → medium/low con razón.

## 6. Secretos: postura

- ¿Existe un único mecanismo por tipo de secreto o cada servicio inventó el suyo?
- ¿Identidades de carga de trabajo (OIDC, managed identity, IRSA/Workload Identity) en
  lugar de llaves de larga duración?
- ¿Rotación automática y alcance mínimo de cada credencial?
- ¿Los secretos llegan como variables de entorno visibles en consolas/logs, o se leen
  bajo demanda?
