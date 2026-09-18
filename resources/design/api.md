# Convenciones de API REST — AgroIA

> Generado por `genesis` a partir de `Documento_Arquitectura_AgroIA.md`.
> `builder` agregará endpoints incrementalmente. No regenerar desde cero.

## Formato de respuesta

### Éxito (200/201)
```json
{
  "data": { ... }
}
```

### Lista paginada
```json
{
  "data": [ ... ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

### Error
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Descripción del error"
  }
}
```

## Códigos de error estándar

| Código | HTTP | Significado |
|--------|-----|-------------|
| NOT_FOUND | 404 | Recurso no existe |
| VALIDATION_ERROR | 422 | Datos de entrada inválidos |
| UNAUTHORIZED | 401 | Token faltante o inválido |
| FORBIDDEN | 403 | Sin permisos (RBAC) |
| CONFLICT | 409 | Conflicto de estado |
| INSUFFICIENT_DATA | 422 | Datos insuficientes (motor ML) |
| INTERNAL_ERROR | 500 | Error interno del servidor |

## Autenticación

- **Tipo:** Bearer JWT (RS256)
- **Header:** `Authorization: Bearer <token>`
- **Expiración:** 60 min (access), 7 días (refresh)
- **Roles:** Admin, Cliente, Técnico, Investigador

## Prefijo de rutas

- **API REST:** `/api/v1/...`
- **Health:** `/api/v1/health`
- **Docs (dev):** `/docs` (Swagger UI)

## Paginación

- Parámetros: `?page=1&page_size=20`
- Máximo: 100 items por página
- Ordenamiento: `?sort=created_at&order=desc`

## Historial de cambios del contrato

- v0.3.0 (2026-09-18): módulo AGC-COST completo (F2-F7) — agregados: CRUD admin de
  `/costeo/conjuntos` (+ validar, publicar con doble control, archivar, clonar con
  reajuste, reajuste-previo, exportar/importar JSON) y CRUD de servicios, componentes,
  tramos, factores/opciones, densidad, zonas, impuestos, política y descuentos;
  `GET|PUT /costeo/identidad`, `POST /costeo/identidad/logo`, `GET|PUT /costeo/cobro-config`;
  `/estimaciones` (crear, listar, editar, emitir, aceptar, rechazar, recalcular con
  snapshot, convertir-comision, export HTML/PDF, sugerencia-puntos y sugerencia-km,
  tablero); `/cobros` (crear, emitir, pagos, anular, enviar, PDF, export HTML).
  Nueva etapa «estimación» en la lista de trabajos. Códigos de negocio nuevos:
  `APROBADOR_ES_EDITOR`, `SIMULACION_REQUERIDA`, `CONJUNTO_INVALIDO`, `CONJUNTO_NO_EDITABLE`,
  `IMPORT_VALIDACION_FALLIDA`, `ESTIMACION_NO_EDITABLE`, `ESTIMACION_VENCIDA`,
  `ESTIMACION_NO_ACEPTADA`, `ESTIMACION_NO_ACEPTABLE`, `SNAPSHOT_INCONSISTENTE`,
  `SNAPSHOT_AUSENTE`, `COMISION_YA_CREADA`, `COBRO_SIN_CONFIGURACION`, `COBRO_YA_EXISTE`,
  `COBRO_YA_EMITIDO`, `NUMERACION_AGOTADA`, `RESOLUCION_VENCIDA`, `PAGO_EXCEDE_SALDO`,
  `MOTIVO_ANULACION_REQUERIDO`, `COBRO_NO_PAGABLE`, `COBRO_NO_ANULABLE` — aditivo.
- v0.2.0 (2026-09-18): módulo AGC-COST F1 — agregados `GET /costeo/parametros/vigentes` y
  `POST /costeo/simular` (roles Admin/Agrónomo) — aditivo. Códigos de negocio:
  `CONJUNTO_SIN_VIGENCIA`, `TRAMOS_INCONSISTENTES`, `DESCUENTO_EXCEDE_TOPE`,
  `BAJO_PISO_RENTABILIDAD` (advertencia), `SERVICIO_NO_ENCONTRADO`, `CONJUNTO_NO_PUBLICADO`,
  `TRAMOS_INSUFICIENTES`, `CONJUNTO_NOT_FOUND`, `CONJUNTO_INVALIDO`.
