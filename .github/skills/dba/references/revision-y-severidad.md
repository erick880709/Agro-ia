# Revisión, severidad y formato de observaciones

## Tabla de contenido

1. Severidad
2. Confianza y verificación
3. Categorías
4. `db-findings.json`
5. Tarjeta de observación
6. Re-revisión

## 1. Severidad (escala de code-review)

| Severidad | Significa en datos | Ejemplos |
|---|---|---|
| `bloqueante` | No se aplica/fusiona/aprueba así | Pérdida o corrupción de datos posible; migración que bloquea producción sin plan; dinero en `FLOAT`; invariante crítico sin restricción con concurrencia real; patrón de acceso NoSQL sin servir que obliga a scan en ruta de usuario; RPO/RTO incumplible; edición de migración aplicada; `DROP` sin respaldo |
| `mayor` | Debe corregirse antes de cerrar | Índice faltante para operación frecuente sobre tabla grande; N+1 en ruta de usuario; paginación `OFFSET` profunda; aislamiento incorrecto con riesgo de lost update; pool sobredimensionado contra `max_connections`; partición caliente probable |
| `menor` | Corregir cuando convenga | Tipo sobredimensionado, nombre inconsistente, índice redundante, comentario de columna faltante |
| `nit` | Opcional | Estilo SQL, orden de columnas sin impacto |
| `pregunta` | Falta un dato para decidir | "¿Cuántas filas tiene `movimientos` en prod?" con la consulta que lo responde |

Escala `mayor` → `bloqueante` cuando el impacto alcanza dinero, datos personales,
disponibilidad de producción o integridad regulatoria. Baja a `menor` si verificaste una
defensa real (tabla pequeña y acotada por diseño, ventana aprobada, índice en otra
migración del mismo cambio).

## 2. Confianza y verificación

- **alta:** leíste el artefacto actual, construiste el escenario y lo demostraste (EXPLAIN
  en copia, test con base efímera, conteo real).
- **media:** escenario plausible sin demostración, o depende de volumen no confirmado.
- **baja:** no se reporta como defecto: conviértela en `pregunta` o descártala.

Un `bloqueante` exige confianza alta, o media con impacto de pérdida de datos o caída de
producción, explicando qué falta para confirmarlo.

Filtro de falsos positivos: descarta si el problema ya no existe en el estado actual, si
otra migración del mismo cambio lo resuelve, si el motor/versión lo hace seguro (p. ej.
`ADD COLUMN ... DEFAULT <constante>` es metadata-only en PG 11+ y `INSTANT` en MySQL
8.0.12+ para casos soportados), o si es una convención explícita del proyecto.

## 3. Categorías

`modelo-integridad`, `consulta-indice`, `transaccion-concurrencia`, `migracion`,
`operacion-disponibilidad`, `seguridad-datos`, `costo-capacidad`, `nosql-acceso`,
`procedimiento`.

## 4. `db-findings.json`

```json
{
  "schema": "dba-findings/1",
  "target": {"type": "change|architecture|repo", "id": "PROJ-123", "base": "origin/main", "head": "a1b2c3d"},
  "mode": "gate",
  "engines": [{"engine": "postgresql", "version": "16", "managed": "aurora"}],
  "assumptions": ["movimientos ~80 M filas en prod (fuente: 16.03)"],
  "findings": [
    {
      "id": "DB-001",
      "fingerprint": "migration:movimientos:index-not-concurrent",
      "category": "migracion",
      "severity": "bloqueante",
      "confidence": "media",
      "title": "CREATE INDEX sin CONCURRENTLY sobre movimientos",
      "location": {"file": "db/migration/V42__idx_mov.sql", "line": 1},
      "refs": ["DATA-007", "API-003-OP-002"],
      "scenario": "80 M filas; el índice bloquea INSERT/UPDATE durante la creación",
      "evidence": "migration_lint MIG-PG-001; tamaño según 16.03",
      "remediation": "CREATE INDEX CONCURRENTLY ... en migración no transaccional (Flyway: executeInTransaction=false)",
      "verification": "Aplicar en copia con volumen; pg_stat_activity sin esperas de lock en escrituras",
      "status": "abierto",
      "disposition": null
    }
  ],
  "verdict": "cambios-requeridos"
}
```

Reglas (`scripts/validate_findings.py`):
- `id` `DB-NNN`; `fingerprint` estable sin números de línea; únicos.
- `severity` ∈ escala; `pregunta` requiere `resolution_query` (cómo obtener el dato).
- `bloqueante`/`mayor` requieren `scenario`, `evidence`, `remediation` y `verification`.
- `confidence` ∈ `alta|media|baja`; `baja` no puede ser `bloqueante`/`mayor`.
- `status` ∈ `abierto, corregido, verificado, reabierto, retirado`; `disposition` (solo
  archi) ∈ `pendiente, incorporada, rechazada-justificada, riesgo-aceptado, diferida`;
  `rechazada-justificada` y `riesgo-aceptado` exigen `disposition_note`.
- `verdict` ∈ `aprobado, aprobado-con-observaciones, cambios-requeridos, no-concluyente`,
  coherente con lo abierto.
- Sin credenciales en el documento (connection strings con contraseña, llaves).

## 5. Tarjeta de observación

```markdown
### DB-001 · CREATE INDEX sin CONCURRENTLY sobre `movimientos`

- **Dónde:** `db/migration/V42__idx_mov.sql:1` · DATA-007
- **Severidad / confianza:** bloqueante / media
- **Escenario:** ~80 M filas (16.03); el `CREATE INDEX` toma `SHARE` lock y bloquea
  escrituras durante minutos en horario transaccional.
- **Evidencia:** `migration_lint` MIG-PG-001; volumen declarado en 16.03.
- **Remedio:** `CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_mov_cuenta_fecha ON movimientos (cuenta_id, fecha DESC);`
  en migración separada sin transacción (Flyway `executeInTransaction=false`).
- **Verificación:** aplicar en copia con volumen; validar `indisvalid` y ausencia de
  esperas de bloqueo en escrituras.
- **Decisión:** [ ] aceptar [ ] rechazar (razón) [ ] diferir [ ] más información
```

## 6. Re-revisión

Verifica cada `corregido` (→ `verificado` o `reabierto`), revisa solo el diff incremental
con todos los ejes y agrega `## Ronda N`. Si un mismo `DB-NNN` se reabre dos veces, el
problema es de diseño: escala a archi.
