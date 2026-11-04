# Estándares de Madurez — Guía para `resources/02-madurez-devsecops.md`

Esta guía define cómo construir el checklist de evaluación del archivo de cierre. La regla de
oro: **si el proyecto ya declaró (o adoptó de hecho) un estándar reconocido, el checklist se
calca a las dimensiones de ese estándar — no se inventan criterios paralelos.** Solo si no hay
ninguno declarado se usa el framework interno de esta skill como fallback.

---

## Paso 1 — Buscar un estándar ya declarado

Antes de preguntar nada, revisa estas fuentes (en orden, léelas por completo si existen):

1. `resources/architecture/**/01-Linea-Base_*.md` — bloque "Seguridad y cumplimiento" de la
   línea base vigente de `archi`: ¿menciona GDPR, PCI-DSS, HIPAA, ISO 27001, SOC 2, o una ley
   local de datos personales? Si no existe, acepta el legacy
   `resources/architecture/definitions/Linea_Base_*.md`.
2. `resources/architecture/**/19.1-Modelo-de-Amenazas-y-Requisitos-de-Seguridad_*.md`,
   `19-Dimensiones-Arquitectonicas.md`, `03-Restricciones.md` y `26-Validacion-y-Aprobacion.md`:
   ¿qué estándares, `SEC-xxx` y condiciones aprobadas debe operacionalizar Vulcano?
3. `devops-strategy/08-security.md` — sección "Cumplimiento": ¿ya lista auditorías o
   certificaciones concretas que el pipeline debe soportar?
4. Respuestas de la Fase 0.4 (`SKILL.md`) — herramientas corporativas obligatorias mencionadas
   (a veces delatan el estándar: ej. "Checkmarx obligatorio" sugiere un programa AppSec formal;
   "debe pasar auditoría SOC2 anual" es explícito).
4. Cualquier documento en `resources/architecture/` que mencione un modelo de madurez ya
   adoptado (CMMI, Google SRE, DORA/Accelerate, un framework propio de la organización).

Si encuentras uno o más, díselo al arquitecto y arma el checklist según la tabla del Paso 2. Si
no encuentras nada, pregunta una sola vez (ver `SKILL.md`, Fase 3 paso 2.b) y, sin respuesta,
usa el framework interno (Paso 3) explícitamente declarado como tal.

---

## Paso 2 — Mapeo de estándares reconocidos a dimensiones de checklist

No repliques el contenido completo de cada estándar (son documentos extensos con licencias
propias) — usa esta tabla como esqueleto de las dimensiones/áreas de control que ese estándar
evalúa, y verifica el grado de cobertura de cada una contra lo que ya documentaron los 26
archivos de la sesión. Si necesitas el detalle exacto de un control, consulta la fuente pública
del estándar en vez de asumir el texto literal.

| Estándar | Ámbito principal | Dimensiones/áreas de control a evaluar |
|---|---|---|
| **OWASP DevSecOps Maturity Model (DSOMM)** | Madurez del ciclo DevSecOps completo | Cultura y organización, gestión de build/deploy, recolección de información de seguridad, pruebas y verificación, implementación de controles |
| **NIST SSDF (Secure Software Development Framework)** | Desarrollo seguro de software | Preparar la organización (PO), proteger el software (PS), producir software bien asegurado (PW), responder a vulnerabilidades (RV) |
| **CIS Benchmarks** | Hardening de infraestructura/nube/contenedores | Configuración específica del proveedor de nube o runtime ya confirmado en `infrastructure-as-code/01-architecture.md` — usa el benchmark correspondiente (CIS AWS/Azure/GCP Foundations, CIS Docker/Kubernetes) |
| **ISO/IEC 27001:2022 (Anexo A)** | Sistema de gestión de seguridad de la información | Controles organizacionales, de personas, físicos y tecnológicos. Determinar controles por tratamiento de riesgo y comparar contra el Anexo A; no tratar los 93 controles como aplicables automáticamente. |
| **SOC 2 (Trust Service Criteria)** | Controles de servicio para proveedores | Seguridad, disponibilidad, integridad de procesamiento, confidencialidad, privacidad |
| **PCI-DSS** | Datos de tarjetas de pago | Red segura, protección de datos de titulares, gestión de vulnerabilidades, control de acceso, monitoreo/pruebas, política de seguridad — de los 12 requisitos, prioriza los que tocan el pipeline y la infraestructura (gestión de vulnerabilidades, monitoreo, control de acceso) |
| **CMMI (para procesos)** | Madurez de procesos organizacionales | Nivel 1 Inicial → 2 Gestionado → 3 Definido → 4 Gestionado cuantitativamente → 5 Optimizado — mapea cada nivel a la sofisticación de `06-ci-cd.md`, `03-task-management.md` y `10-incident-management.md` |
| **Google SRE / DORA** | Madurez de entrega y operación | Las cinco métricas vigentes: deployment frequency, change lead time, failed deployment recovery time, change fail rate y deployment rework rate. Los benchmarks deben citar fuente y año. |

Si el proyecto declaró más de uno (frecuente: SOC2 + DORA, o ISO27001 + CIS Benchmarks),
evalúa contra todos los declarados — no seleccione solo uno arbitrariamente.

---

## Paso 3 — Framework interno (fallback si no hay estándar declarado)

Cuando no hay ningún estándar formal declarado, evalúa cada pilar con esta rúbrica interna,
reutilizando exactamente los mismos niveles y criterios ya usados en el resto de la sesión
(`references/orden-y-dependencias.md`, sección "Progresión por madurez") para que el
vocabulario sea consistente en todo `resources/`:

| Nivel | DevSecOps | Infraestructura como Código | Observabilidad |
|---|---|---|---|
| **Básico** | CI manual o inexistente; inspección limitada a lint/reporte; sin gates de seguridad ni pruebas automatizadas; despliegue rolling sin análisis, `decisions.deployment_model: push_pipeline` | Recursos creados manualmente o IaC parcial sin módulos ni estado remoto gestionado; sin policy as code | Solo logs crudos, sin dashboards ni alertas |
| **Intermedio** | CI/CD con gates de calidad sobre código nuevo, deuda con owner y pruebas unitarias + algo de integración; despliegue rolling o blue-green con verificación manual post-deploy; métricas DORA con `dora_collection_method: manual` | IaC completa con módulos, estado remoto con locking, sin políticas de no-drift; policy as code informativo si existe | Dashboards y alertas básicas, sin SLOs ni tracing |
| **Avanzado** | Gates basados en riesgo, ratchet de calidad, deuda/excepciones gobernadas, supply-chain verificable, artefactos inmutables; despliegue canary/blue-green con análisis y rollback automático por métrica (`decisions.deployment_strategy` ≠ rolling), `dora_collection_method: automated` sobre las cinco métricas DORA | Módulos versionados/probados, policy as code bloqueante (`decisions.policy_engine` ≠ none), no-drift, costo y lifecycle controlados | SLOs/error budget, telemetría gobernada, runbooks probados y páginas por burn rate/síntomas |

No infles "Avanzado" en DevSecOps solo por tener CI/CD maduro con gates de calidad: si el
despliegue sigue siendo rolling sin análisis automático y sin `decisions.deployment_model`
resuelto a `gitops` cuando el target lo justifica (ej. Kubernetes), el pilar de despliegue continuo
se califica por separado como Intermedio aunque el resto del pipeline sea Avanzado — ver la regla
de evidencia "no promediar ni redondear hacia arriba" más abajo.

Deja explícito en el documento generado: *"No se encontró un estándar formal declarado por el
proyecto; esta evaluación usa el framework interno de madurez de `vulcano` (Básico/Intermedio/
Avanzado + métricas DORA) como checklist genérico, no una certificación oficial."*

---

## Reglas de evidencia (aplican en ambos casos)

- **Nunca califiques sin cita.** Cada fila de la tabla de madurez del documento final debe
  señalar el archivo/sección real que sustenta esa calificación (ej. "Avanzado — ver
  `devops-strategy/06-ci-cd.md` §Quality Gates, todos los gates son bloqueantes con umbral
  definido"). Una calificación sin cita es una opinión, no una evaluación.
- **No infles el nivel para quedar bien.** Si un pilar tiene evidencia mixta (ej. CI/CD avanzado
  pero observabilidad básica), califica cada pilar por separado — no promedies ni redondees
  hacia arriba.
- **Completitud ≠ madurez.** Que los 26 archivos existan no significa que el nivel de madurez
  sea alto — un archivo puede estar completo y documentar honestamente un estado Básico. Separa
  ambas cosas en el documento (sección de completitud documental vs. sección de madurez real).
