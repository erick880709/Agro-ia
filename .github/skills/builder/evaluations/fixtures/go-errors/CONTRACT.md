# Contrato público

`GET /accounts/{id}/balance`

- 200 `{"balance": <int>}` con `Content-Type: application/json`.
- 404 si la cuenta no existe.
- 500 ante cualquier otro error, sin detalles internos en el cuerpo.

Firmas exportadas consumidas por otros paquetes: `NewService(Store) *Service`,
`(*Service).Balance(context.Context, string) (int64, error)`,
`NewHandler(*Service) http.Handler`, `ErrNotFound`, `Store`, `Account`.
