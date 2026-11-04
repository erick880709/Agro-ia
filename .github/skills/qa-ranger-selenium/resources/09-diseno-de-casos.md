# 09 — Diseño de casos de prueba (antes de automatizar)

## 1. Entrada → análisis
Antes de escribir casos, inventaría lo recibido: HU y criterios de aceptación, reglas de negocio, mockups/URL, permisos por rol, integraciones. Lista **supuestos** y **preguntas** cuando algo falte; no inventes requisitos.

## 2. Técnicas
| Técnica | Aplica a | Ejemplo |
|---|---|---|
| Partición de equivalencia | Campos con clases de valores | Monto: válido, cero, negativo, no numérico |
| Valores límite | Rangos y longitudes | mín−1, mín, máx, máx+1; longitud 40 y 41 |
| Tabla de decisión | Reglas con varias condiciones | Saldo suficiente × tope diario × cuenta inscrita |
| Transición de estados | Entidades con ciclo de vida | Pendiente → Aprobada → Aplicada → Reversada (y transiciones inválidas) |
| Casos de uso / flujos | Recorridos completos | Login → transferir → comprobante → historial |
| Error guessing | Riesgos conocidos | Doble clic en Confirmar, recargar en la confirmación, volver atrás |

Cobertura mínima por funcionalidad: camino feliz, validaciones de campos, reglas de negocio, permisos/roles, errores del sistema (backend caído, timeout), estados vacíos, navegación (atrás, recarga, sesión expirada), y accesibilidad básica (teclado, mensajes asociados a campos).

## 3. Deduplicación
- Un caso por **comportamiento distinto**; si dos casos solo cambian el dato dentro de la misma clase de equivalencia, se unen (o se vuelven filas de un caso parametrizado).
- Las validaciones de formato repetidas en varias pantallas que usan el mismo componente se prueban una vez a fondo y se verifican superficialmente en las demás.

## 4. Plantilla
| ID | HU/CA | Título | Precondiciones | Pasos | Datos | Resultado esperado | Prioridad | Tipo | ¿Automatizable? |
|---|---|---|---|---|---|---|---|---|---|
| TC-001 | HU-245/CA-1 | Transferir con saldo suficiente | Usuario autenticado con saldo ≥ monto | 1. Abrir Transferencias 2. Diligenciar 3. Continuar 4. Confirmar | cuenta 00998877665, monto 150000 | Mensaje "Transferencia exitosa" con referencia; saldo descontado | Alta | Funcional | Sí — UI (smoke) |

## 5. Qué automatizar y en qué capa
- **UI (Selenium)**: flujos críticos de punta a punta y comportamiento propio de la interfaz.
- **API** (Karate/RestAssured): reglas de negocio, validaciones de datos y combinatoria; es más rápido y estable. Un caso de 30 combinaciones de validación pertenece a API, con 1–2 representantes en UI.
- **Manual/exploratorio**: usabilidad, cambios visuales puntuales, casos de una sola vez.
- Prioriza por riesgo (impacto × probabilidad): pagos, transferencias y autenticación primero.

## 6. Del caso al test
El ID del caso viaja al nombre del test (`[HU-245][CA-1]`) para que la matriz de trazabilidad (08 §5) cierre el ciclo: requisito → caso → test automatizado → resultado.
