# Verificación AWS por MCP

AWS se usa únicamente en `read_only_verification`. Descubrir MCP, cuenta y región antes de leer;
si no está disponible, registrar `cloud_mcp: missing`.

- Consultar solo identidad, tags, configuración y health necesarios para verificar.
- Prohibir create/update/delete, `terraform apply`, import y mutaciones de state.
- Sanitizar tokens, headers, ARNs sensibles y valores de variables antes del snapshot.
- Releer solo recursos declarados por Bob. Un resultado ambiguo vuelve a `reconcile`.
- Preferir identidad federada/de corta duración; nunca recibir access keys.

Fuente oficial: [federación IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers.html).
