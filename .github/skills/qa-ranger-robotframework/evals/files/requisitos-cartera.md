# HU-310 — Despliegue del modelo de cartera

- CA-1: existen las tablas `cuentas`, `movimientos` y `parametros`.
- CA-2: `cuentas.estado` solo toma ACTIVA, BLOQUEADA o CERRADA.
- CA-3: todo movimiento referencia una cuenta existente (sin huérfanos).
- CA-4: el parámetro `TOPE_DIARIO` vale 5000000.

Ambiente de evaluación: SQLite local creado desde `cartera.sql`. Las pruebas son de solo lectura.
