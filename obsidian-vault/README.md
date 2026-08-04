# Obsidian Vault — AgroIA Knowledge Graph

Este vault es generado automáticamente desde `graphify-out/graph.json` mediante el script `scripts/graphify2obsidian.py`.

## 🚀 Cómo usar

1. Abre [Obsidian](https://obsidian.md)
2. Haz clic en **"Open folder as vault"**
3. Selecciona esta carpeta (`obsidian-vault/`)
4. Activa **Graph View** (`Ctrl+G` o `Cmd+G`) para ver el grafo de contexto del proyecto
5. Navega por las notas usando los wikilinks `[[doble corchete]]`

## 📊 Qué muestra el grafo

- **Nodos:** Comunidades del knowledge graph (grupos de archivos, funciones, clases, documentos relacionados)
- **Aristas:** Conexiones entre comunidades (imports, referencias, dependencias)
- **Tamaño del nodo:** Proporcional al número de símbolos en esa comunidad
- **Colores:** Por tipo de archivo (código, documentación, specs, arquitectura)

## 🔄 Actualizar el vault

```bash
# Reconstruir el grafo de Graphify
python -m graphify update . --force

# Regenerar el vault de Obsidian
python scripts/graphify2obsidian.py
```

## ⚙️ Configuración

- `.obsidian/app.json` — Configuración de la app
- `.obsidian/graph.json` — Configuración de la vista de grafo (pre-optimizada)
- `.obsidian/core-plugins.json` — Plugins base activados

---

**Generado:** 2026-08-03 | **Fuente:** `graphify-out/graph.json` | **Script:** `scripts/graphify2obsidian.py`
