---
veredicto: aprobado-con-observaciones
bloqueantes: 0
mayores: 0
menores: 3
nits: 1
autor_independiente: false
---

# CR-001 — Épicas E1–E9 de RFP-AGROIA-003 (plataforma confiable de medición de suelo)

**Revisor:** sesión del agente (autor del código — se declara independencia limitada).
**Alcance:** commits `5b3805e..6511a2d` (E1→E9): decodificación Modbus, motor de calidad,
incertidumbre, calibración, muestreo/contexto, grados de evidencia, reportes/salud/parámetros,
ciclo de vida y ML.

## Gate computacional
- `pytest` E1–E9 (135 pruebas unitarias) → **135 passed**.
- `ruff check` sobre todos los archivos → **All checks passed**.
- Integración (`tests/integration_test.py`) → **8/8**.
- 4 tests pre-existentes dependientes de Postgres local fallan por `ConnectionRefusedError`
  (BD local apagada) — no relacionados con este cambio.

## Hallazgos

### [SEGURIDAD · Mayor · CORREGIDO] Autorización insuficiente en endpoints administrativos de /iot
- **Dónde:** `apps/backend/agroia_backend/api/iot.py` — `POST /calibracion/pares`,
  `POST /muestreo/sesiones`, `PUT /parametros-calidad/{clave}`,
  `POST /dispositivos/{id}/mantenimiento`.
- **Problema:** el middleware global JWT solo valida autenticación, no rol. Estos endpoints
  nuevos no leían `X-User-Role` ni aplicaban `exigir_no_cliente`/verificación de rol, por lo
  que cualquier usuario autenticado (incluido rol `cliente`) podía modificar umbrales del
  motor de calidad, inyectar pares de calibración o registrar mantenimiento.
- **Impacto:** alteración de clasificaciones y recomendaciones de todos los usuarios.
- **Corrección aplicada:** se añadió `X-User-Role` + `exigir_no_cliente` a los endpoints de
  escritura de calibración/muestreo/mantenimiento, y verificación estricta de rol `admin` en
  `PUT /parametros-calidad/{clave}`.

### [INTEGRACIÓN · Menor · CORREGIDO] `/iot/sensor/raw` no era ruta pública
- **Dónde:** `apps/backend/agroia_backend/services/jwt_auth.py`.
- **Problema:** el firmware (TT-02) publica registros crudos sin token, pero el endpoint no
  estaba en `RUTAS_PUBLICAS` (a diferencia de `/iot/sensor` y `/iot/ingest`).
- **Corrección:** añadido `/api/v1/iot/sensor/raw` a `RUTAS_PUBLICAS`.

### [CORRECCIÓN · Menor] `clasificar_lectura` retorna `sonda_fuera_de_suelo` antes de evaluar saturación
- **Dónde:** `apps/backend/agroia_backend/services/motor_calidad.py`.
- **Problema:** con humedad≈0 y CE≈0 se retorna `sonda_fuera_de_suelo` sin evaluar si el pH
  está saturado (≥9,0), perdiendo esa señal.
- **Impacto:** menor — la lectura sigue excluida del análisis; se pierde solo el motivo fino.
- **Recomendación:** acumular motivos en lugar de retorno temprano.

### [DATOS · Menor] Migración 051 renombra estados pero no reclasifica el histórico
- **Dónde:** `apps/backend/alembic/versions/051_motor_calidad.py`.
- **Problema:** las filas históricas marcadas `invalidada` con la regla binaria anterior
  conservan ese estado; la reclasificación con el motor nuevo es TT-16 (pendiente).
- **Impacto:** al desplegar, esas filas no reflejan la nueva granularidad (bajo límite /
  saturada). No se pierde ningún dato.
- **Recomendación:** proceso por lotes (TT-16) por finca.

### [MANTENIBILIDAD · Nit] Comparación de UUID con `str` en consultas de salud
- **Dónde:** `apps/backend/agroia_backend/api/iot.py` — `GET /sensores/{finca_id}/salud`.
- **Problema:** `DispositivoIoT.finca_id == finca_id` (str) sin convertir a UUID. Patrón ya
  usado en endpoints pre-existentes del repo (funciona con asyncpg), pero conviene normalizar.

## Veredicto
`aprobado-con-observaciones` — el hallazgo mayor de autorización fue corregido; quedan
observaciones menores y nits que no bloquean el despliegue.
