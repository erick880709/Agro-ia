# MOV-01 · Consultar movimientos de una cuenta

- Modo: feature · Rigor: reforzado (datos financieros, autorización)

## Comportamiento deseado

Un cliente autenticado consulta los movimientos de una de sus cuentas mediante
`GET /api/accounts/{id}/movements`.

## Criterios de aceptación

- **AC-01:** Devuelve los movimientos de la cuenta ordenados por fecha descendente, máximo 50.
- **AC-02:** Solo el titular de la cuenta (claim `sub` del token = `ownerId`) puede listarlos. Otro usuario recibe 403 y ningún dato.
- **AC-03:** Si la cuenta no existe, responde 404.

## Restricciones

- Proyecto reactivo del Scaffold Clean Architecture: respetar reglas de dependencia y ArchUnit.
- No registrar datos personales (documento, número de cuenta) en logs.
