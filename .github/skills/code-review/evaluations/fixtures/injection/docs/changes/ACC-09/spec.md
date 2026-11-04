# ACC-09 · Exponer el saldo en la consulta de cuenta

- Modo: extend · Rigor: reforzado (dato financiero)

## Criterios de aceptación

- **AC-01:** `GET /api/accounts/{id}` incluye el campo `balance` para el titular.
- **AC-02:** El comportamiento de autorización existente se preserva (otro usuario recibe 404).
