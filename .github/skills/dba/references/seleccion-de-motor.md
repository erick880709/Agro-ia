# Selección de motor y persistencia políglota

Complementa `guia-catalogo-bases-de-datos.md` y `guia-matriz-decision.md` de archi: archi
posee la decisión (`09`/`10`/`20`); `dba` aporta la evaluación técnica.

## Método

1. Reúne patrones de acceso, invariantes transaccionales, volumen/crecimiento, latencia,
   consistencia (CAP/PACELC), retención, regulación y capacidad operativa del equipo.
2. Filtra por **requisitos duros** (ACID multi-entidad, consulta ad hoc, residencia de
   datos, servicio administrado aprobado por el cliente).
3. Compara los candidatos viables en matriz ponderada con `QA-xx` de archi: ajuste al
   patrón de acceso, consistencia, escalabilidad, operación (backups, HA, upgrades),
   ecosistema/skills del equipo, costo (licencia + infraestructura + operación) y lock-in.
4. Recomienda con trade-offs explícitos y el `DA-xxx` propuesto. Si no hay trade-off real,
   dilo: no infles la comparación.

## Reglas prácticas

- **Por defecto, relacional** para el núcleo transaccional bancario (cuentas, pagos,
  contabilidad): invariantes multi-entidad y consultas no anticipadas.
- **NoSQL** cuando el patrón es por clave a gran escala con latencia estricta, o el
  agregado es documento autocontenido, y los invariantes caben en un ítem/partición.
- **Persistencia políglota** solo si cada motor resuelve un patrón real; cada motor
  adicional suma backups, monitoreo, seguridad, skills y consistencia entre fuentes.
  Declara la fuente de verdad y el mecanismo de sincronización (CDC, outbox, eventos).
- Servicio administrado preferido salvo restricción: reduce carga operativa, pero verifica
  límites (extensiones disponibles, versiones, parámetros, tamaño máximo, costo de I/O).
- Oracle → PostgreSQL u otros motores: considera costo de conversión de PL/SQL, paquetes,
  tipos y herramientas antes de prometer ahorros (ver [migración de datos](migracion-de-datos.md)).

## Salida

```markdown
| Criterio (peso) | PostgreSQL (Aurora) | DynamoDB | Oracle (RDS) |
|---|---|---|---|
| Patrón de acceso AP-01..AP-06 (30) | 5 | 3 (AP-04 ad hoc requiere índice/stream) | 5 |
...
**Recomendación:** ... **Trade-offs aceptados:** ... **DA propuesto:** DA-0xx
```
