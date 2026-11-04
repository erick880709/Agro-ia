# ACC-07 · Rechazar identificadores de cuenta vacíos

- Modo: extend · Rigor: estándar

## Criterios de aceptación

- **AC-01:** Si `accountId` es nulo o en blanco, el caso de uso devuelve un error `InvalidAccountIdException` sin consultar el repositorio.
- **AC-02:** El comportamiento existente (titular ve su cuenta, otro usuario no la ve) se preserva.
