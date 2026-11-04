# Modelado relacional

## Tabla de contenido

1. Del dominio al esquema
2. Claves
3. Tipos de datos
4. Restricciones e integridad
5. Normalización y desnormalización
6. Patrones frecuentes en banca
7. Nombres y documentación
8. Checklist de revisión

## 1. Del dominio al esquema

Conceptual (entidades e invariantes del negocio, del Event Storming/`16`) → lógico
(atributos, cardinalidades, claves, normalización) → físico (tipos del motor, índices,
particiones, almacenamiento). Cada invariante del negocio se pregunta: **¿qué restricción
de la base lo garantiza aunque dos procesos escriban a la vez?** Lo que solo valida la
aplicación se rompe con concurrencia, cargas batch o un segundo servicio.

## 2. Claves

- Toda tabla tiene clave primaria. Clave sustituta (`BIGINT` identity/secuencia o UUID)
  + restricción `UNIQUE` sobre la clave natural del negocio (número de cuenta, documento +
  tipo, referencia de operación). La natural sin `UNIQUE` permite duplicados.
- UUID: en motores con índice clusterizado por PK (SQL Server, MySQL/InnoDB) los UUID
  aleatorios fragmentan; usa secuenciales (UUIDv7, `NEWSEQUENTIALID()`, `BINARY(16)`
  ordenado). En PostgreSQL usa tipo `uuid` nativo; UUIDv7 (`uuidv7()` [PG18+] o generado en
  la app) mejora la localidad del índice.
- Identificadores expuestos a clientes: no secuenciales predecibles si permiten
  enumeración (coordinar con aegis); el control real es la autorización.
- Claves foráneas declaradas, con índice en la columna FK (PostgreSQL y Oracle no lo crean
  solos; sin él, `DELETE` del padre bloquea/escanea y los joins degradan).

## 3. Tipos de datos

| Dato | Correcto | Incorrecto |
|---|---|---|
| Dinero | `NUMERIC(p,s)` / `NUMBER(p,s)` / `DECIMAL`, con moneda explícita | `FLOAT`, `REAL`, `DOUBLE`, `MONEY` (SQL Server, ambiguo con moneda y precisión) |
| Instante | `timestamptz` (PG), `TIMESTAMP WITH TIME ZONE` (Oracle), `DATETIME2` + offset o `DATETIMEOFFSET` (SQL Server), UTC en `DATETIME` (MySQL) | Hora local sin zona, strings |
| Fecha de negocio | `DATE` | `TIMESTAMP` truncado |
| Estado/enum | `CHECK` sobre valores o tabla catálogo con FK | Texto libre; `ENUM` de MySQL si cambia a menudo |
| Booleano | `boolean` (PG), `BIT` (SQL Server), `NUMBER(1)` + `CHECK` (Oracle < 23ai; `BOOLEAN` en 23ai) | `CHAR('S'/'N')` sin `CHECK` |
| Texto | Longitud que exprese una regla real; en PG `text` + `CHECK` si hay límite | `VARCHAR(255)` por costumbre |
| Semiestructurado | `jsonb` (PG), `JSON` nativo (Oracle 21c+, MySQL), con columnas reales para lo consultado/indexado | Todo el agregado en JSON para evitar modelar |

Oracle: `''` es `NULL`; una regla "no vacío" requiere `NOT NULL`, no `<> ''`.

## 4. Restricciones e integridad

- `NOT NULL` por defecto; cada nulo necesita significado de negocio.
- `UNIQUE` para unicidad de negocio, incluidas parciales/filtradas (PG `WHERE`, SQL Server
  filtered index) para "uno activo por cliente".
- `CHECK` para rangos y estados válidos; exclusión (`EXCLUDE USING gist`, PG) para no
  solapamiento de vigencias.
- FK con acción explícita (`ON DELETE RESTRICT` por defecto en datos financieros; nunca
  `CASCADE` sobre historia contable).
- Triggers solo para integridad que no se expresa con restricciones (auditoría,
  historización); nunca lógica de negocio oculta (ver procedimientos).

## 5. Normalización y desnormalización

3FN por defecto en OLTP. Desnormalizar requiere: query concreta que lo justifica,
mecanismo de consistencia (trigger, misma transacción, proyección asíncrona con lag
aceptado) y owner. Proyecciones de lectura (CQRS localizado en `16.xx`) se declaran como
tales, no como fuente de verdad.

## 6. Patrones frecuentes en banca

- **Libro mayor / movimientos:** solo inserción (append-only), importe con signo o
  débito/crédito, saldo derivado o materializado con control de concurrencia; corrección
  por contra-asiento, nunca `UPDATE` del movimiento.
- **Idempotencia:** tabla o columna `UNIQUE` con la clave de idempotencia del request/evento.
- **Auditoría:** `created_at/by`, `updated_at/by`; historia completa con tablas de
  historia o temporal tables (SQL Server system-versioned, Oracle Flashback Data Archive,
  triggers en PG) según retención regulatoria.
- **Borrado lógico:** solo si el negocio lo exige; índices/unique parciales que excluyan
  borrados; vistas para el caso común. El borrado real por retención/habeas data sigue
  siendo necesario.
- **Multi-tenant:** columna `tenant_id` en todas las tablas + en PK/índices/FK compuestas +
  RLS (PG) o VPD (Oracle); o esquema/base por tenant si el aislamiento regulatorio lo exige.
- **Vigencias:** `valid_from`/`valid_to` con rango semiabierto `[desde, hasta)` y
  restricción de no solapamiento.
- **Catálogos/parámetros:** tablas versionadas con vigencia, no constantes en código.

## 7. Nombres y documentación

Convención del proyecto primero (Bancolombia suele usar prefijos/longitudes de Oracle).
Si no hay: `snake_case`, singular o plural consistente, PK `<tabla>_id` o `id`, FK con
nombre de la referencia, índices `ix_<tabla>_<cols>`, unique `uq_`, check `ck_`.
`COMMENT ON` en tablas y columnas no obvias; el diccionario físico de archi (`16.xx`)
debe corresponder.

## 8. Checklist de revisión

- [ ] PK en todas las tablas; unique de negocio; FK indexadas.
- [ ] Dinero exacto; instantes con zona; nulabilidad justificada.
- [ ] Invariantes críticos en restricciones; triggers justificados.
- [ ] Índices para cada operación frecuente de `14.00`.
- [ ] Volumen/crecimiento → partición y retención decididas.
- [ ] Auditoría, historia y borrado conforme a regulación.
- [ ] Multi-tenant aislado en datos e índices.
