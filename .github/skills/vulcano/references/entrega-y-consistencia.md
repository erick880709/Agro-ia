# Entrega y consistencia transversal

Leer antes de generar un archivo dependiente y antes del cierre.

## Contratos cruzados

- CI/CD coincide con branching, ambientes, testing, seguridad, inspección/deuda y release
  management.
- `devops-strategy/05-environments.md` e `infrastructure-as-code/02-environments.md` usan nombres y orden de promoción idénticos, expresados en tablas
  verificables por el validador.
- Secrets management y security usan el mismo mecanismo e identidad.
- `08-security.md` conserva los IDs/criterios `SEC-xxx` de Archi y cada requisito aplicable se
  mapea a control, owner, evidencia, frecuencia y estado según `contrato-handoff-archi.md`.
- Naming se aplica a estructura, módulos, estado y networking.
- State management separa ambientes y cubre locking, backup, restore y drift.
- Monitoring mide releases según CI/CD y release management; dashboards solo consumen señales
  definidas; SLOs no contradicen RNFs.
- Paging por impacto usa síntomas/SLO/burn rate. Alertas preventivas justifican límite/riesgo y
  acción. Toda alerta alta/crítica tiene runbook.
- Incident management y runbooks comparten severidad/escalamiento; DR respeta RTO/RPO.
- Si hay contradicción con un archivo existente, informar y pedir confirmación antes de editarlo.

## Diagramas

Usar Mermaid para branching, pipeline y telemetría. Para red cloud preferir `.drawio` con
iconografía oficial siguiendo las referencias de `archi`; Mermaid es fallback. Validar sintaxis.

## Salidas

Los 26 objetivos y su orden están en `orden-y-dependencias.md`. Las plantillas están en
`plantillas-archivos.md`. Además mantener:

- `resources/.vulcano/manifest.yaml`
- `resources/01-devops-index.md`
- `resources/02-madurez-devsecops.md`

Adaptar `04-terraform-structure.md` al nombre/conceptos de la herramienta confirmada sin
quitar el prefijo `04-`. No asumir
Terraform, GitHub Actions ni un backend de observabilidad por el nombre del archivo.

## Gate por archivo

- Frontmatter completo, fuente trazable, modo correcto y decisiones con justificación.
- Sin placeholders no aceptados ni secretos; supuestos y owners visibles.
- AS-IS describe evidencia real; greenfield no simula AS-IS; TO-BE contiene gap y fases
  validables sin big bang injustificado.
- Consistencia con arquitectura, manifiesto y documentos hermanos.
- Controles proporcionales al riesgo y madurez; exclusiones justificadas.
- Si el archivo es `06-ci-cd.md`, inspección continua registra métricas completas, baseline/ratchet,
  tratamiento del legado, feedback en PR, deuda con owner/SLA y excepciones con vencimiento.
- Si el archivo es `08-security.md`, registra las fuentes Archi con versión/estado y no
  renumera, debilita ni redefine `SEC-xxx`; `Parcial`, `Pendiente`, `No requiere automatización`
  y `Excepción` tienen motivo, riesgo, owner y salida aplicables.

## Gate de cierre

- Cinco métricas DORA por aplicación/servicio, con definición, fuente, ventana, baseline/calidad,
  meta y equipo accountable/participantes; benchmark con año/fuente y ownership compartido.
- Supply chain: identidad efímera, pinning, SBOM, firma/provenance y verificación cuando aplican.
- Handoff de seguridad: todos los `SEC-xxx` aplicables están cubiertos o tienen disposición
  explícita; contradicciones/cambios de riesgo regresan a `19.1`, `20` o `21` de Archi.
- Inspección continua: calidad del código nuevo gobernada sin convertir la deuda histórica en un
  bloqueo permanente; deuda y excepciones tienen owner, salida y revisión.
- IaC: versionado, tests, policy, costo, lifecycle, drift, destroy protection y recovery.
- Observabilidad: ownership, cardinalidad, PII, costo y salud de telemetría.
- Incident/DR: roles, comunicaciones, postmortem, acciones y ejercicios/restores probados.
- Manifiesto e índice actualizados; ejecutar `scripts/validate-vulcano.mjs --strict-completeness`
  sin errores y registrar warnings aceptados.
