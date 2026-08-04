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
|--------|------|-------------|
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
