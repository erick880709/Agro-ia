# Registro de avance en las demás skills

Contrato que siguen las skills del kit para dejar un nodo en la memoria del proyecto al terminar
su tarea. Está pensado para ser **fire-and-forget**: la skill escribe el payload y el hook de Stop
hace el resto.

## Payload mínimo

```json
{
  "skill": "builder",
  "type": "avance",
  "title": "Implementar login",
  "summary": "Flujo de login con JWT y refresh token, con pruebas."
}
```

Solo `skill`, `type`, `title` y `summary` son obligatorios. Añade lo que aporte valor:

- `status`: `completado` por defecto; usa `pendiente` para dejar tareas, `activo` para trabajo en
  curso, `archivado` no se usa al registrar.
- `files`: rutas relativas de los artefactos producidos.
- `links`: ids de nodos previos con los que este avance se conecta (p. ej. la HU de `specter`, el
  hito de `archi`, el avance de `builder` que revisaste).

## Dos vías equivalentes

### A. Dejar el payload en `.memoria/pending/`

```bash
# la skill escribe un archivo JSON por nodo
mkdir -p .memoria/pending
cat > .memoria/pending/$(date +%s).json <<'JSON'
{ "skill": "builder", "type": "avance", "title": "Implementar login",
  "summary": "Flujo de login con JWT." }
JSON
```

El hook de Stop (`.claude/settings.json`) lo consolida en `.memoria/graph.json` al cerrar el turno.
Es la vía recomendada para no bloquear la tarea con la gestión de memoria.

### B. Llamar al CLI directamente

```bash
node .claude/skills/memoria/scripts/memoria.mjs record \
  --skill builder --type avance --title "Implementar login" \
  --summary "Flujo de login con JWT y refresh token." \
  --file src/auth.ts --link <id-del-nodo-previo>
```

Úsala cuando quieras confirmar el nodo en el momento (p. ej. al final de un cambio reforzado).

## Reglas

1. **No duplicar.** Si la misma tarea ya tiene nodo (mismo `skill` + `title`), el CLI lo actualiza.
   Antes de registrar, revisa con `query --skill <skill>` si ya existe un nodo equivalente.
2. **Enlazar, no aislar.** Si este avance continúa un nodo anterior (HU, decisión, hito), pásalo en
   `links` para que el grafo conserve el flujo.
3. **Resumen de alto valor.** El `summary` debe permitir retomar el contexto en la próxima sesión:
   qué se hizo y qué quedó, no el detalle que ya vive en los artefactos.
4. **Nada de secretos.** No registrar tokens, credenciales ni datos sensibles.
5. **Un nodo por unidad de avance.** No uno por comando; sí uno por HU implementada, decisión tomada,
   revisión cerrada o hito alcanzado.

## Sección estándar

Las skills del kit incluyen al final de su `SKILL.md` una sección "Registro de avance en memoria"
con esta instrucción. Si una skill no la tiene, aplica igualmente el contrato de esta referencia.
