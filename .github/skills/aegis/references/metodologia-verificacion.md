# Metodología de verificación y severidad

Basada en las prácticas de verificación de Trail of Bits (`fp-check`,
`differential-review`, `insecure-defaults`) y en la calibración de severidad de
`briiirussell/cybersecurity-skills`, adaptadas a la escala de code-review.

## Tabla de contenido

1. Racionalizaciones a rechazar
2. Compuerta frontera + resultado
3. Verificación de un candidato
4. Veredictos
5. Severidad
6. Exclusiones fijas
7. Modo `verify` (falso positivo)
8. Cobertura

## 1. Racionalizaciones a rechazar

| Si piensas… | Por qué es un error | Acción |
|---|---|---|
| "Es un PR pequeño, revisión rápida" | Heartbleed fueron dos líneas | Clasifica por riesgo, no por tamaño |
| "El patrón se ve peligroso, es vulnerable" | Reconocer un patrón no es analizar | Traza fuente → sumidero completa |
| "Seguro hay validación antes" | Suponer la defensa es tan malo como suponer el bug | Encuentra la defensa o no la cuentes |
| "Es solo un refactor" | Los refactors rompen invariantes de seguridad | Trátalo como ALTO hasta probar lo contrario |
| "Está documentado / el dev debería saberlo" | Nadie lee docs bajo presión | Si el default es inseguro, es hallazgo de diseño |
| "Es configuración, no código" | La configuración se despliega a producción | Evalúa el valor que corre sin configurar |
| "Es crítico, se nota" | Los LLM sobreestiman severidad | Califica solo el impacto demostrado |
| "No hay tests, no es mi problema" | Sin tests, sin evidencia de defensa | Sube el riesgo y propone el test negativo |
| "La herramienta no reportó nada" | Ausencia de alerta ≠ ausencia de bug | Declara qué cubrió la herramienta |
| "Lo encontré igual en otro archivo" | Cada contexto tiene sus defensas | Verifica cada instancia; agrupa al reportar |

## 2. Compuerta frontera + resultado

Antes de que un candidato sea hallazgo, escribe los seis elementos en concreto:

| # | Elemento | Ejemplo |
|---|---|---|
| 1 | Principal de menor confianza | Cliente autenticado cualquiera del canal móvil |
| 2 | Entrada que controla y dónde entra | `accountId` del path en `GET /accounts/{accountId}/movements` |
| 3 | Control previsto | Filtro por titular que sí aplica `GET /accounts/{id}` |
| 4 | Frontera cruzada | Cliente A → datos de cliente B |
| 5 | Afectado | Movimientos de otra cuenta (PII financiera) |
| 6 | Resultado concreto | El handler pasa `accountId` al use case sin comparar con `sub` |

- Sin frontera cruzada o la "víctima" es el propio atacante → nota de hardening o nada.
- Sin control previsto que el resultado derrote → nota de hardening (una desviación de
  checklist no es vulnerabilidad por sí sola).
- El resultado depende de un hecho fuera del código (WAF, API Gateway, IdP, flag) →
  `needs_validation` con ese hecho como bloqueo.
- Sin resultado concreto, solo "podría ser peligroso" → sigue trazando o descarta.

## 3. Verificación de un candidato

1. **Reformula** la afirmación en una frase precisa: clase de bug, causa raíz,
   disparador, impacto. La mitad de los falsos positivos colapsa aquí.
2. **Alcanzabilidad**: ¿el código se despliega? ¿la ruta está montada/registrada en el
   entrypoint real (router, `RouterFunction`, `@RestController`, módulo Angular, handler Go)?
3. **Traza** entrada → propagación → sumidero con `archivo:línea` de cada salto.
4. **Busca la defensa** en cada salto: validación, tipo, filtro de seguridad, política
   del framework, constraint de BD, configuración por defecto segura, middleware, gateway.
5. **Abogado del diablo**: escribe por qué podría ser falso y verifica ese argumento.
6. **Demuestra barato** si puedes: test negativo en copia aislada, mutación, comando.
   Registra resultado. Un test que pasa contra el código vulnerable no prueba nada.
7. **Cadenas**: al terminar, revisa si hallazgos individualmente bajos se combinan
   (open redirect + OAuth `redirect_uri` laxo = robo de código de autorización).

Usa verificación profunda (fase por fase, con subagentes si existen) cuando: la ruta
cruza 3+ módulos o servicios, hay concurrencia/TOCTOU, es lógica de negocio sin spec,
o la verificación estándar quedó inconclusa.

## 4. Veredictos

| Veredicto | Significa | Campos requeridos |
|---|---|---|
| `confirmed` | Traza completa con impacto, o test que lo demuestra | severidad, traza ≥ 2 pasos, evidencia, contraevidencia |
| `needs_validation` | El código lo sustenta pero un hecho decisivo está fuera | bloqueos (no vacío) y plan de validación ejecutable por el owner |
| `rejected` | Un control nombrado en una ubicación nombrada corre siempre antes del sumidero, o no es alcanzable | `ruled_out_by` {control, ubicación} |

`needs_validation` no es un estacionamiento para corazonadas: sin bloqueo nombrado y
prueba que lo resuelva, es `rejected` o todavía no está listo para registrarse.

Confianza: `high` solo con demostración (`reproduced: true`); traza estática completa
sin ejecución topa en `medium`.

## 5. Severidad

Califica **probabilidad** e **impacto** por separado, cada uno con una razón de una
línea. **`overall` nunca supera el impacto.**

| Nivel | Ancla | Forma típica |
|---|---|---|
| critical | Derrota total de un control central, consecuencia amplia, casi sin precondición | RCE sin autenticación; bypass de autenticación a cualquier cuenta; lectura/escritura cross-tenant de todo; secreto productivo con permiso de escritura expuesto |
| high | Derrota total de un control explícito con consecuencia real | IDOR/BOLA sobre datos de otro cliente; escalada a admin; SSRF a metadata cloud; inyección SQL alcanzable; JWT sin verificar firma |
| medium | Debilita un control sin derrotarlo, o lo derrota con consecuencia limitada | Rate limit evadible parcialmente; fuga de campos no sensibles; CSRF en cambio de bajo valor |
| low | Cruce real con consecuencia menor o precondiciones improbables | Enumeración de usuarios sin seguimiento; hostnames internos en errores |

Suelen sobrecalificarse (no son high sin consecuencia trazada): self-XSS, cabeceras
faltantes, open redirect aislado, banners de versión, falta de rate limiting sin abuso
con costo real, cualquier cosa que ya exige admin/shell.

**Contexto bancario:** exposición de PAN, credenciales, tokens o PII financiera de
terceros eleva el impacto un nivel respecto al mismo bug sobre datos no sensibles.
Indica la razón en `impact.reason`.

**Señales de explotación (dependencias):** consulta CISA KEV y EPSS cuando haya red;
cambian probabilidad y orden de trabajo, nunca el impacto. Sin red: `no verificado`,
jamás inferido de memoria.

## 6. Exclusiones fijas (antes de verificar)

Descarta por ubicación, igual en cada ejecución: tests (`src/test`, `*_test.go`,
`*.spec.ts`), fixtures/mocks, código generado (corrige la fuente), vendored sin
modificar (pasa a supply chain), docs/ejemplos. **Excepciones:** un secreto que parece
vivo es hallazgo donde esté; los workflows de CI corren con tokens reales; una ruta de
debug es alcance si el build desplegado la sirve; un fixture cargado en producción es
código productivo. Cuenta lo excluido por regla en el reporte.

## 7. Modo `verify`

Para "¿es real este hallazgo?" (de Sonar, Snyk, Checkmarx, un pentest o code-review):
pasos 1–6 de la sección 3, un candidato por vez, sin cazar bugs nuevos. Salida:
`VERDADERO POSITIVO` / `FALSO POSITIVO` / `NECESITA VALIDACIÓN` con la evidencia, y
para falsos positivos el control y ubicación que lo descartan (útil para marcar la
supresión en la herramienta con justificación auditable).

## 8. Cobertura

Todo reporte declara: categorías evaluadas, categorías no aplicables con motivo,
unidades no cubiertas (servicios, módulos, archivos) y herramientas ejecutadas con
versión o `not_run`. Una categoría del alcance sin evaluar impide el veredicto `seguro`.
