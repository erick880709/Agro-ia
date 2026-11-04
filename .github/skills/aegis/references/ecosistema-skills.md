# Ecosistema de skills: contratos con Aegis

Aegis no implementa, no diseña arquitectura global y no construye pipelines. Su valor
está en conectar los requisitos de seguridad de arquitectura con el código real y
devolver hallazgos que las otras skills puedan procesar sin reinterpretarlos.

## Tabla de contenido

1. Flujo completo
2. archi
3. builder
4. code-review
5. terragrunt-iac
6. Vulcano (DevSecOps)
7. ranger y especialistas QA
8. Handoffs: formato

## 1. Flujo completo

```
archi (19.1: THR/SEC, 14.00, 17.x)
   │  SEC-xxx con criterio y clase de evidencia
   ▼
aegis advise ──► AC negativos + controles SC/SEC ──► builder implementa
                                                        │
                       code-review (pasada D) ◄─────────┤
                              │ señales de seguridad     │ rigor reforzado
                              ▼                          ▼
                         aegis audit / gate ──► security-review.md + security-findings.json
                              │                          │
          amenaza nueva ──► propuesta a archi 19.1       └─► builder corrige (bugfix) ─► aegis re-review
          control operativo ─► Vulcano (pipeline)
          caso negativo ────► ranger / QA
terragrunt-iac ──► aegis iac/pipeline ──► hallazgos ──► terragrunt-iac corrige
```

## 2. archi

**Consume:**
- `19.1-Modelo-de-Amenazas-y-Requisitos-de-Seguridad_<Proyecto>.md`: `THR-xxx`, `SEC-xxx`
  (alcance `CT/API/OP`, criterio de aceptación, clase de evidencia, estado) y la matriz
  OWASP Agentic `ASI01`–`ASI10` si la solución es agentic.
- `14.00` (seguridad por API/operación), `16.xx` (clasificación, cifrado, retención),
  `17`/`17.6` (zonas, identidad de máquinas, red), `17.7` (blueprint IaC), `20` (decisiones).

**Hace:**
- Verifica en código/IaC cada `SEC-xxx` dentro del alcance y lo reporta como
  `implementado-con-evidencia`, `ausente`, `ineficaz` o `desconocido` (falta insumo).
- Usa los mismos IDs. No renumera, no reescribe criterios y no edita `19.1`.

**Devuelve (propuesta, no edición):**
- Amenazas no modeladas observadas en el código → `THR-propuesta-NN` con actor,
  precondición, activo, frontera y escenario, para que archi las incorpore.
- Contradicciones diseño ↔ código → hallazgo + nota de reapertura incremental (archi
  reabre `19.1` y sus dependientes según su propia regla de reapertura).
- Evidencia que permitiría mover un `SEC-xxx` de `Definido` a `Implementado`/`Validado`.

## 3. builder

**Antes (`advise`):** recibe la HU/spec y entrega controles y AC negativos que builder
incorpora a su spec (rigor reforzado si toca permisos, datos persistentes o dinero).
Builder conserva el ownership de la spec; Aegis propone.

**Después (`gate`):** builder entrega el mismo paquete que a code-review (ID del cambio,
`docs/changes/<id>/`, spec con `AC-xx`, base y revisión, evidencia, rigor y modo). Aegis
devuelve `docs/changes/<id>/security-review.md` + `security-findings.json`.

**Cierre:** en rigor reforzado builder no debe declarar `completed` con un hallazgo
`confirmed` medium o superior abierto, ni con veredicto `no-concluyente` cuyo faltante
pueda ser crítico. Un cambio de código posterior al veredicto lo deja vencido.

**Corrección:** los hallazgos aceptados se convierten en encargos `bugfix` de builder con
el test negativo como criterio. Aegis hace `re-review` solo del diff incremental y de los
hallazgos marcados `corregido` (resultado: `verificado` o `reabierto`). Si un hallazgo se
reabre dos veces, el problema es de diseño o de spec: escala a archi o al usuario.

## 4. code-review

- code-review hace una pasada D ligera (`references/security.md` de code-review). Aegis
  es el especialista al que se escala cuando `diff_triage.py` marca categorías de
  auth/cripto/secretos/IaC, la pasada D tiene un candidato que no pudo confirmar, el
  cambio es reforzado o el usuario pide revisión de seguridad.
- **Mapeo de severidad** (para que code-review integre sin reinterpretar):

  | Aegis | code-review | Cuenta para el veredicto |
  |---|---|---|
  | `confirmed` critical / high | `bloqueante` | Sí |
  | `confirmed` medium | `mayor` | Sí |
  | `confirmed` low | `menor` | No bloquea |
  | nota de hardening | `nit` / `fyi` | No |
  | `needs_validation` | `pregunta` | Bloquea si la respuesta podría volverlo bloqueante |
  | `rejected` | — | Se lista en "Rechazados (no re-levantar)" |

- Regla compartida: ninguna de las dos skills aprueba con un hallazgo de seguridad
  confirmado abierto.
- Si code-review ya reportó el mismo problema, Aegis referencia su ID (`B-01`) en vez de
  duplicarlo y solo agrega traza, severidad calibrada y test negativo.

## 4.1 dba

Frontera: `dba` diseña y revisa controles de datos (roles y privilegios, RLS/VPD,
cifrado en reposo y de columna, enmascaramiento, auditoría, retención). Aegis evalúa
explotabilidad: inyección SQL/NoSQL, IDOR/BOLA, secretos de conexión expuestos, IAM
sobre el servicio de datos. Si Aegis encuentra un problema de diseño de datos (rol de
aplicación con DDL, RLS ausente donde `19.1` lo exige), lo reporta y hace handoff a
`dba`; si `dba` encuentra algo explotable, lo referencia aquí.

## 5. terragrunt-iac

- Aegis ejecuta o lee `tg_lint.py` (terragrunt-iac) y `terragrunt_check.py`
  (code-review) como base, y añade el análisis de [IaC y nube](iac-terragrunt-nube.md) y
  [CI/CD](cicd-pipelines.md): IAM de mínimo privilegio, condiciones de confianza OIDC,
  cifrado, exposición pública, estado remoto, `prevent_destroy`, supply chain de módulos.
- Respeta los principios no negociables de terragrunt-iac (catálogo vs live, refs
  pineadas, mocks solo en validate/plan/init, secretos fuera de `inputs`/`values`). Su
  violación con impacto de seguridad es hallazgo de Aegis; sin impacto de seguridad es
  materia de code-review o terragrunt-iac.

## 6. Vulcano (DevSecOps)

archi define el *qué* (`SEC-xxx`) y Vulcano el *cómo* en el pipeline (SAST/DAST/SCA,
umbrales, SBOM, firma). Aegis:
- puede recomendar herramientas y reglas concretas cuando el usuario lo pide o no existe
  Vulcano, marcándolas como recomendación operativa;
- si existe Vulcano, entrega la tabla `SEC/hallazgo → control automatizable → evidencia
  esperada` y no decide etapas ni umbrales;
- nunca presenta un pipeline inexistente como evidencia.

## 7. ranger y especialistas QA

Cada hallazgo confirmado incluye un caso de prueba negativo en lenguaje neutral
(Dado/Cuando/Entonces) que el especialista correspondiente (Karate para APIs,
Playwright/Selenium para UI, JMeter para límites de recursos, Robot Framework para
aceptación) puede automatizar como regresión de seguridad.

## 8. Handoffs: formato

```markdown
### Handoff → <skill>
- **Origen:** HS-003 (security-findings.json) / SEC-007
- **Motivo:** <una frase>
- **Insumo entregado:** <rutas>
- **Esperado de vuelta:** <artefacto o decisión>
- **Bloquea:** sí/no — <qué>
```

Aegis no ejecuta otras skills dentro de su sesión salvo que el entorno lo permita y el
usuario lo pida; reporta el handoff y devuelve el control.
