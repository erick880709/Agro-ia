# Herramientas por capa

Las herramientas generan candidatos; la verificación es manual (ver metodología). Usa lo
que el proyecto ya tenga (Sonar, Snyk, Checkmarx, Fortify, Prisma, Defender, Advanced
Security) antes de proponer algo nuevo. Ejecuta solo sobre código y sistemas propios o
autorizados, y guarda salidas fuera del repositorio analizado salvo que se pida otra cosa.

| Capa | Herramienta | Comando base | Observaciones |
|---|---|---|---|
| SAST multi-lenguaje | Semgrep | `semgrep scan --config p/security-audit --config p/secrets --config p/owasp-top-ten --sarif -o semgrep.sarif` | Añade `p/java`, `p/spring`, `p/golang`, `p/typescript`, `p/angular` según stack |
| SAST profundo | CodeQL | `codeql database create db --language=java` + `codeql database analyze db codeql/java-queries:codeql-suites/java-security-extended.qls --format=sarif-latest -o codeql.sarif` | Requiere build para Java/Go; mejor taint tracking |
| Java | SpotBugs + FindSecBugs | Plugin Gradle/Maven | Complementa a Semgrep |
| Go | gosec, govulncheck | `gosec -fmt sarif -out gosec.sarif ./...`; `govulncheck ./...` | govulncheck calcula alcanzabilidad |
| Secretos | Gitleaks, TruffleHog | `gitleaks git --redact -r gitleaks.json`; `trufflehog git file://. --only-verified` | `--redact` siempre; `--only-verified` contacta proveedores: confirma autorización |
| Dependencias | OSV-Scanner, OWASP Dependency-Check, npm audit | `osv-scanner scan -r .` | KEV/EPSS para priorizar |
| IaC | Checkov, Trivy | `checkov -d . --framework terraform --output sarif`; `trivy config .` | Analiza también el plan JSON |
| CI/CD | zizmor, actionlint | `zizmor --format sarif .github/workflows` | `--offline` si no hay red |
| Contenedores | Trivy, Grype, Hadolint | `trivy image <img>`; `hadolint Dockerfile` | |
| Kubernetes | kubesec, Trivy, Checkov | `trivy config k8s/` | |
| DAST (solo entornos propios) | OWASP ZAP baseline | `zap-baseline.py -t https://<entorno-de-prueba>` | Nunca contra producción ni terceros sin autorización escrita |
| SBOM | Syft | `syft dir:. -o cyclonedx-json` | |
| LLM (solo propios) | promptfoo, garak | Configs de red teaming del proyecto | Entornos de prueba |

`scripts/sec_triage.py` detecta stacks y emite el plan con los comandos aplicables y si
cada binario está instalado. Reporta como `not_run` lo que no se ejecutó.
