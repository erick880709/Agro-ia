# Formato del reporte

El reporte es una superficie de diálogo: el autor (humano o Builder) lo lee,
decide por hallazgo y lo usa para corregir. Debe poder leerse sin la
conversación y procesarse por máquina.

## Ubicación y nombre

1. Si existe expediente del cambio (`docs/changes/<id>/`), escribe
   `docs/changes/<id>/review.md`. En re-revisiones, actualiza el mismo archivo
   y agrega una sección `## Ronda N` (no crees otro).
2. Si no, `docs/reviews/CR-NNN-<slug>.md`: lista `docs/reviews/`, usa el
   siguiente número (CR-001 si no existe la carpeta) y un slug kebab-case de 2–5
   palabras del cambio.
3. Si el proyecto ya tiene otra convención para reportes de revisión, úsala.
4. Si no hay filesystem o el usuario solo pidió una opinión rápida, entrega el
   reporte en la respuesta con la misma estructura.

Escribir el reporte no modifica el código; es el único archivo que crea esta
skill en modo `review`.

## Estructura

Usa [la plantilla](../assets/review-template.md). Secciones, en orden:

1. **Bloque YAML** (`review:`) entre `---`: id, cambio, revisión revisada, base,
   rigor, independencia, veredicto, conteos y lista de hallazgos
   `{id, severidad, confianza, archivo, estado}`. Es lo que Builder lee.
2. **Veredicto** en una línea accionable ("cambios requeridos: B-01 permite
   leer cuentas ajenas").
3. **Resumen** de 2–3 frases: qué cambió y la lectura del revisor.
4. **Gate computacional**: tabla check → resultado → nota.
5. **Cumplimiento de la spec**: tabla AC → estado (✅ ⚠️ ❌ —) → evidencia.
   Omítela si no hay spec y escribe "Intención reconstruida" en su lugar.
6. **Estado rápido**: tabla ID → severidad → `archivo:línea` → estado.
7. **Hallazgos** agrupados por severidad (omite grupos vacíos), cada uno como
   tarjeta.
8. **Preguntas** y **Preexistentes** (si hay).
9. **Fuera de alcance** (solo si hay algo de verdad relevante).
10. **Rondas** (en re-revisión).

## Tarjeta de hallazgo

```markdown
### B-01 · El listado de movimientos no filtra por titular

- **Dónde:** `infrastructure/entry-points/reactive-web/src/main/java/.../Handler.java:42`
- **Severidad / confianza:** bloqueante / alta
- **Por qué:** `accountId` se toma del path y se pasa al use case sin comparar
  con el `sub` del token. Cualquier cliente autenticado puede listar
  movimientos de otra cuenta cambiando el ID (IDOR).
- **Evidencia:** `GET /accounts/999/movements` con token de la cuenta 123
  devuelve 200 en `HandlerTest#otherAccount` (añadido en copia temporal).
- **Arreglo:** pasar el titular del token al use case y filtrar en el gateway
  (`findByAccountIdAndOwner`). Test: caso con cuenta ajena → 403 sin efectos.
- **Decisión:**
  - [ ] aceptar
  - [ ] rechazar
  - [ ] diferir
  - [ ] necesita más información
- **Nota del autor:**
```

Reglas:

- Un hallazgo por problema; el mismo problema en varios sitios va en una
  tarjeta con todas las ubicaciones.
- `Dónde` usa rutas relativas a la raíz del repo y líneas del estado actual.
- `Por qué` explica escenario e impacto; no repitas el título.
- `Arreglo` concreto. Snippet solo si no es de una línea.
- Las decisiones son listas de tareas GFM en líneas propias. Cuando el autor
  ya decidió (en el archivo o en el chat), colapsa a `**Decisión:** aceptar`.
- Opciones a medida cuando hay dos caminos reales ("aceptar A: filtro en
  gateway" / "aceptar B: filtro en handler"); incluye siempre rechazar/diferir.
- Si el autor rechaza con razón técnica válida, marca `— RETIRADO`, deja una
  línea de respuesta y conserva la tarjeta (trazabilidad).

## Vocabulario de estado

`pendiente`, `aceptado`, `rechazado`, `diferido`, `retirado`, `corregido`,
`verificado` (corregido y re-revisado), `reabierto` (la corrección no resolvió
o introdujo regresión).

## Respuesta en el chat

Tras escribir el archivo, responde solo con:

- veredicto en una línea;
- conteo por severidad;
- bloqueantes y mayores en una frase cada uno con su ID;
- ruta del reporte.

No pegues el reporte completo en el chat salvo que no haya archivo.
