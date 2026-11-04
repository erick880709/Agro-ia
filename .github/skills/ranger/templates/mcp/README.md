# Plantillas MCP para el tablero de trabajo

- `claude-code.mcp.json` → copiar como `.mcp.json` en la raíz del proyecto. Conserva solo el servidor
  que uses (Azure DevOps o Jira) y cambia `personalsoftsas` por tu organización si es otra.
- `vscode.mcp.json` → copiar como `.vscode/mcp.json` (autenticación interactiva con la cuenta Microsoft).

Las credenciales se exportan como variables de entorno antes de abrir el cliente; los archivos solo
contienen referencias `${VAR}`. Guía completa: `../../references/tablero_de_trabajo_mcp.md`.
