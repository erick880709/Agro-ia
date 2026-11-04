# Verificación GCP por MCP

GCP se usa únicamente en `read_only_verification`. Descubrir MCP, proyecto y región antes de leer;
si no está disponible, registrar `cloud_mcp: missing`.

- Consultar solo identidad, labels, configuración y health necesarios para verificar.
- Prohibir create/update/delete, `terraform apply`, import y mutaciones de state.
- Sanitizar tokens, headers, nombres de cuenta de servicio y valores de variables antes del
  snapshot.
- Releer solo recursos declarados por Bob. Un resultado ambiguo vuelve a `reconcile`.
- Preferir Workload Identity Federation; nunca recibir claves de cuenta de servicio descargadas.

Fuente oficial: [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation).
