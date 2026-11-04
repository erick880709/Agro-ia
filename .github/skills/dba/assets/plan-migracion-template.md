# Plan de migración — <título>

| Campo | Valor |
|---|---|
| Tipo | esquema (expand/contract) · datos entre motores · upgrade |
| Motor origen → destino | <…> |
| Objetos afectados y volumen | <tabla: filas, tamaño> |
| Ventana / tolerancia a bloqueo | <…> |
| Respaldo previo | <snapshot/PITR verificado: id y hora> |
| Punto de no retorno | <fase/paso> |

## Precondiciones
- [ ] Versión de la app compatible con el esquema de cada fase
- [ ] Prueba en copia con volumen representativo (tiempos medidos)
- [ ] `lock_timeout`/`statement_timeout` (o equivalente) definidos
- [ ] Monitoreo listo (bloqueos, lag, errores, latencia)

## Fases
| Fase | Acción (DDL/DML/job) | Lock esperado | Duración medida | Verificación | Rollback |
|---|---|---|---|---|---|
| 1 Expand | | | | | |
| 2 Migrate/backfill (lotes de N) | | | | | |
| 3 Cambio de lectura en la app | | | | | |
| 4 Contract (release posterior) | | | | | |

## Validación
- Conteos y checksums: <consultas>
- Pruebas funcionales/equivalencia: <…>

## Corte (migración de datos)
| Paso | Responsable | Tiempo | Criterio de avance | Rollback |
|---|---|---|---|---|

## Post
- [ ] Estadísticas actualizadas · [ ] Planes revisados · [ ] Retiro del origen/columna vieja planificado
