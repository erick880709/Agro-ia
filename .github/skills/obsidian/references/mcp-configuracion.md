# Configuración del MCP de Obsidian

Esta es la guía canónica que la skill aplica siempre antes de operar sobre un vault. Hay tres vías,
en orden de preferencia: **MCP con `uvx`** (recomendada), **MCP con `npx`** (alternativa rica) y
**Obsidian CLI** (sin MCP, requiere Obsidian abierto).

## Prerrequisito común: plugin Local REST API

Las rutas MCP usan el plugin comunitario **Local REST API**
(`coddingtonbear/obsidian-local-rest-api`):

1. En Obsidian: Ajustes → Plugins de la comunidad → Explorar → buscar **Local REST API** → Instalar y activar.
2. En los ajustes del plugin, copia la **API key**.
3. Deja host `127.0.0.1` y puerto `27124` (valores por defecto) salvo que el usuario los cambie.

Pide al usuario **solo la API key** (host/puerto tienen defecto); nunca inventes ni guardes
credenciales en el repositorio. La API key se inyecta como variable de entorno del servidor MCP,
no en un archivo versionado.

## Vía 1 (recomendada): `mcp-obsidian` con `uvx`

Servidor `mcp-obsidian` (MarkusPfundstein) vía Python `uvx`. Requiere Python 3.11+ y `uv`.

### Registrar el servidor

```bash
claude mcp add obsidian -- uvx mcp-obsidian
```

Si el CLI de `claude` no está disponible, añade el bloque al `.mcp.json` del proyecto (o al
config global de MCP):

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "uvx",
      "args": ["mcp-obsidian"],
      "env": {
        "OBSIDIAN_API_KEY": "<API_KEY>",
        "OBSIDIAN_HOST": "127.0.0.1",
        "OBSIDIAN_PORT": "27124"
      }
    }
  }
}
```

> Si `uvx` no se resuelve, usa su ruta completa (`which uvx` / `where uvx`).

### Herramientas que expone

`list_files_in_vault`, `list_files_in_dir`, `get_file_contents`, `search`,
`patch_content`, `append_content`, `delete_file`.

## Vía 2 (alternativa): `@cyanheads/obsidian-mcp-server` con `npx`

Servidor más rico (14 herramientas, STDIO o HTTP). Requiere Node 18+.

```json
{
  "mcpServers": {
    "obsidian": {
      "command": "npx",
      "args": ["-y", "@cyanheads/obsidian-mcp-server"],
      "env": {
        "OBSIDIAN_API_KEY": "<API_KEY>",
        "OBSIDIAN_HOST": "127.0.0.1",
        "OBSIDIAN_PORT": "27124"
      }
    }
  }
}
```

Consulta su README para el esquema completo de variables (`OBSIDIAN_API_KEY`, `OBSIDIAN_HOST`,
`OBSIDIAN_PORT`, y opcionales como `OBSIDIAN_VAULT_NAME`, `OBSIDIAN_SSL`).

## Vía 3 (sin MCP): Obsidian CLI

Si el usuario no quiere MCP, usa el CLI oficial (`obsidian`), que requiere Obsidian abierto.
Derivado de `kepano/obsidian-skills`:

```bash
obsidian read file="Nota"                       # leer nota activa o por nombre
obsidian create name="Nueva Nota" content="# Hola" silent
obsidian append file="Nota" content="Línea nueva"
obsidian search query="término" limit=10
obsidian property:set name="status" value="done" file="Nota"
obsidian daily:append content="- [ ] Tarea"
obsidian backlinks file="Nota"
```

Reglas del CLI:

- Parámetros con `=`: `name="Mi Nota"`. Banderas sin valor: `silent`, `overwrite`, `total`.
- `file=<nombre>` resuelve como wikilink; `path=<ruta>` es la ruta exacta desde la raíz del vault.
- `vault=<nombre>` como primer parámetro selecciona vault; por defecto usa el vault más reciente.
- `--copy` copia la salida al portapapeles; `silent` evita abrir archivos.
- Para desarrollo de plugins/temas: `obsidian plugin:reload id=<id>`, `obsidian dev:errors`,
  `obsidian dev:screenshot`, `obsidian eval code="..."`.

## Verificación posterior

Tras configurar, confirma que el MCP responde (lista archivos del vault) antes de continuar.
Si el usuario acaba de añadir el MCP, avísale de que puede requerir recargar/reiniciar el cliente
para que las herramientas aparezcan (mismo patrón que `archi` con los MCP de diagramación).
