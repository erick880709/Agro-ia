# Instalación y workflows

Cómo se activa la memoria en un proyecto y qué automatizaciones la acompañan.

## Instalación en un proyecto destino

1. Copia el kit al proyecto (ver la sección de instalación del README del kit).
2. Inicializa la memoria desde la raíz del proyecto destino:

   ```bash
   node .claude/skills/memoria/scripts/memoria.mjs init
   ```

3. `init` hace tres cosas:
   - crea `.memoria/` (`graph.json`, `index.md`, `pending/`, `config.json`);
   - añade el hook de Stop a `.claude/settings.json` (consolida los pendientes al cerrar cada
     turno; conserva los hooks que ya existan);
   - copia `templates/github-memoria.yml` a `.github/workflows/memoria.yml` si no existe.

4. Añade `.memoria/` al control de versiones: la memoria **se rastrea en git** para que el historial
   y el contexto viajen con el proyecto. No la ignores salvo que el proyecto lo exija.

## Hook de Stop (Claude)

El hook ejecuta `node .claude/skills/memoria/scripts/memoria.mjs hook-stop` al terminar cada turno:

- lee `.memoria/pending/*.json` y los consolida en `graph.json`;
- desduplica por `skill` + `title`;
- regenera `index.md`;
- mueve los pendientes mal formados a `pending/invalid/` (no los pierde);
- **nunca bloquea** el cierre: ante un error propio solo escribe a stderr.

Las skills dejan su avance en `pending/` (fire-and-forget); el hook hace el resto.

## Workflow de GitHub

`init` instala `.github/workflows/memoria.yml` en el proyecto destino. Se ejecuta en push a
`main`/`master`/`develop` y en PR cuando cambia `.memoria/**`, y:

1. valida la integridad de `.memoria/graph.json` (`memoria.mjs validate`);
2. regenera y confirma el índice humano (`memoria.mjs report`).

El kit también lleva su propio workflow `.github/workflows/memoria.yml` que valida la skill y el
grafo de ejemplo del kit.

## Comando de Claude (`/memoria`)

`.claude/commands/memoria.md` ofrece las operaciones en lenguaje natural: `/memoria init`,
`/memoria record ...`, `/memoria query ...`, `/memoria report`, `/memoria merge`,
`/memoria validate`.
