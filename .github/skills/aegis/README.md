# Aegis — especialista de ciberseguridad del ecosistema de skills

Skill defensiva de seguridad de aplicaciones (AppSec/DevSecOps) que conoce el trabajo de
**archi**, **builder**, **code-review** y **terragrunt-iac** y emite recomendaciones y
hallazgos verificados sobre el código, la IaC, los pipelines y los componentes de IA que
esas skills producen.

## Qué hace

| Modo | Para qué |
|---|---|
| `advise` | Antes de implementar: controles y AC negativos para la spec de builder |
| `audit` / `gate` | Revisión de seguridad de diff, PR, repo o cierre reforzado de builder |
| `iac` / `pipeline` | Terragrunt/Terraform, IAM, OIDC, estado remoto, GitHub Actions, Azure DevOps |
| `supply-chain` | Dependencias, CVE (con KEV/EPSS), SBOM, secretos |
| `agentic` | LLM, agentes, MCP, RAG y auditoría de skills/plugins (incluidas las propias) |
| `container` | Dockerfile, imágenes, Kubernetes |
| `verify` | ¿Es real este hallazgo de Sonar/Snyk/pentest? |
| `fix` | Correcciones de hallazgos aceptados (vía builder) |
| `ir-playbook` | Playbooks de respuesta a incidentes (NIST SP 800-61r3 / PICERL) |

## Estructura

```
aegis/
├── SKILL.md                         # flujo, invariantes, modos, veredicto
├── README.md
├── agents/openai.yaml
├── references/
│   ├── ecosistema-skills.md         # contratos con archi, builder, code-review, terragrunt-iac, Vulcano, QA
│   ├── metodologia-verificacion.md  # frontera+resultado, veredictos, severidad, falsos positivos
│   ├── catalogo-owasp-cwe.md        # OWASP 2025, API 2023, LLM 2025, Agentic 2026, CWE
│   ├── stacks/java-spring.md        # Spring Security, WebFlux, Scaffold Bancolombia, MCP del Scaffold
│   ├── stacks/go.md
│   ├── stacks/angular.md
│   ├── iac-terragrunt-nube.md
│   ├── cicd-pipelines.md
│   ├── cadena-suministro-y-secretos.md
│   ├── ia-agentes-mcp.md
│   ├── contenedores-kubernetes.md
│   ├── contexto-regulatorio-banca.md
│   ├── herramientas.md
│   ├── playbook-respuesta-incidentes.md
│   ├── formato-reporte.md
│   └── evaluacion-conductual.md
├── scripts/
│   ├── sec_triage.py                # stacks + señales candidatas (secretos enmascarados) + plan de herramientas
│   ├── validate_findings.py         # contrato aegis-findings/1
│   └── to_sarif.py                  # SARIF 2.1.0 para code scanning
├── assets/
│   ├── security-report-template.md
│   ├── Linea_Base_Seguridad_template.md
│   └── ir-playbook-template.md
├── evals/evals.json
└── tests/test_aegis_scripts.py
```

## Instalación

Copia la carpeta `aegis/` junto a las demás skills (`~/.claude/skills/` o
`.claude/skills/` del proyecto) o importa `aegis.skill`. Invocación:

- Claude Code: `/aegis revisa la seguridad del cambio PROJ-482`
- Codex: `$aegis audita .github/workflows`
- claude.ai: se activa por descripción ("¿es seguro este endpoint?", "revisa el OIDC").

Verificación local (Python 3.10+, sin dependencias):

```bash
python -m unittest discover -s tests -v
python scripts/sec_triage.py <repo> --base origin/main --json /tmp/candidatos.json
```

## Integración con las otras skills (aplicada)

Aegis funciona sin modificar las demás; estas versiones ya incluyen los puntos de
invocación (todos opcionales y no bloqueantes si aegis no está instalada):

- **builder** (`SKILL.md`, pasos 5 y 6): "Si la skill `aegis` está disponible y el cambio es
  reforzado o toca autenticación, autorización, dinero, PII, secretos o IaC de identidad,
  solicita su modo `gate` además de code-review; en reforzado no declares `completed` con
  hallazgos `confirmed` medium o superiores abiertos."
- **code-review** (`SKILL.md` tabla de modos, pasada D y cierre; `references/security.md` §0): "Si `diff_triage.py` marca
  auth/cripto/secretos/IaC o la pasada D deja candidatos sin confirmar, escala a `aegis`
  y adopta su mapeo de severidad (`critical/high → bloqueante`, `medium → mayor`)."
- **terragrunt-iac** (paso 4, punto 3): "Para pipelines con OIDC o cambios de IAM/red, solicita a
  `aegis` el modo `iac`/`pipeline` antes de entregar."
- **archi** (`SKILL.md` paso 11 del Caso A y guía de `19.1` §10 "Retroalimentación desde código"): "Las amenazas observadas por `aegis` en código
  llegan como `THR-propuesta-NN`; se incorporan aquí con ID definitivo."

## Fuentes que inspiraron la skill

- Trail of Bits `skills`: `insecure-defaults`, `sharp-edges`, `fp-check`,
  `differential-review`, `static-analysis` (Semgrep/CodeQL/SARIF),
  `supply-chain-risk-auditor`, `agentic-actions-auditor`.
- briiirussell `cybersecurity-skills`: calibración de severidad (frontera + resultado),
  `findings.json` con veredictos, verificación por candidato, `cicd-security`,
  `prompt-injection`, `agent-supply-chain-audit`, `secrets-audit`.
- mukul975 `Anthropic-Cybersecurity-Skills`: `building-incident-response-playbook`,
  auditoría de Terraform, mapeos a marcos (ATT&CK, NIST CSF 2.0, D3FEND).
- Masriyan `Claude-Code-CyberSecurity-Skill`: organización por dominios y puertas de
  autorización para trabajo ofensivo.
- GitHub Secure Code Game (temporada de agentes de IA) y OWASP Top 10 LLM/Agentic.

Alcance deliberadamente **defensivo**: no incluye explotación, recon de terceros, C2 ni
análisis de malware; esos dominios requieren autorización y skills dedicadas.
