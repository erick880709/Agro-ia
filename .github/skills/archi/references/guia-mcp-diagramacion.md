# Guía: MCP de diagramación (Excalidraw / draw.io)

Antes de generar **cualquier** diagrama en cualquiera de los tres casos (C4, secuencia, ER, despliegue), valida si tienes acceso a herramientas MCP de diagramación. Usarlas en vez de escribir Mermaid/`.drawio` a mano reduce el riesgo de sintaxis inválida que el usuario solo descubre al abrir el archivo, y en el caso de despliegue permite crear/editar el diagrama con iconografía real de forma interactiva.

## Paso 1 — Verifica disponibilidad

Usa `ToolSearch` con consultas como `"excalidraw"` y `"drawio"` / `"draw.io"` para ver si hay herramientas ya conectadas de estos servidores MCP en la sesión actual.

- **Si aparecen herramientas de `drawio-remoto`:** cárgalas y úsalas para crear/editar el diagrama de despliegue con iconografía oficial (el estilo de cada ícono sale siempre de `assets/iconos/catalogo_iconos_curado.json`, nunca de la paleta que proponga el MCP; `references/drawio-iconos-nube.md` describe el flujo).
- **Si aparecen herramientas de `excalidraw-remoto`:** úsalas como generador complementario para diagramas más conceptuales/libres (C4, secuencia, ER) cuando el usuario prefiera un artefacto visual editable además del Mermaid embebido. El Mermaid dentro del `.md` **no se elimina** aunque uses Excalidraw — sigue siendo la versión portable/versionable que cualquiera puede abrir sin el MCP.
- Antes del primer uso de cualquiera de las dos, revisa su schema completo (los parámetros exactos se conocen recién al cargarlas) y adáptate a lo que pidan como entrada.

## Paso 2 — Si NO hay ninguna disponible: configúralas

1. Busca el archivo de configuración de usuario de MCP del cliente activo. El más común en Windows con VS Code es:
   ```
   %APPDATA%\Code\User\mcp.json
   ```
   (se abre también desde la paleta de comandos con "MCP: Open User Configuration"). Si el cliente es distinto, busca el equivalente (p. ej. `.mcp.json` en la raíz del proyecto para configuración a nivel de proyecto).
2. Si encuentras el archivo, **pide autorización explícita al usuario antes de modificarlo**: es su configuración personal y agrega servidores remotos de terceros a su cliente. Solo con su confirmación, **agrega** (sin sobrescribir servidores ya configurados) las entradas que falten:
   ```json
   {
     "servers": {
       "excalidraw-remoto": { "url": "https://mcp.excalidraw.com/mcp" },
       "drawio-remoto": { "url": "https://mcp.draw.io/mcp" }
     }
   }
   ```
   Si el archivo ya tiene otros servidores, fusiona las claves dentro de `servers` — nunca reemplaces el archivo completo.
3. Si no encuentras el archivo, o no hay certeza de cuál es el correcto para el cliente del usuario, **no adivines ni escribas a ciegas**: muéstrale el bloque de configuración de arriba y pídele que lo pegue él mismo en "MCP: Open User Configuration" (o el archivo que corresponda).
4. **Importante:** editar el archivo de configuración no hace que las herramientas aparezcan en la sesión en curso — la mayoría de los clientes MCP las cargan solo al iniciar o al recargar. Avísale explícitamente al usuario: *"Con tu autorización configuré el MCP de diagramación; necesitas recargar la ventana / reiniciar la sesión para que las herramientas queden disponibles."*
5. Mientras tanto, **no bloquees la entrega**: continúa generando los diagramas con el método ya soportado (Mermaid embebido para C4/secuencia/ER, `.drawio` manual siguiendo `references/drawio-iconos-nube.md` para despliegue en AWS/Azure/GCP), y deja una nota en el documento indicando que pueden regenerarse con el MCP en una sesión futura si el usuario lo desea.

## Control del resultado de draw.io

El MCP es un medio de edición, no una fuente de decisiones arquitectónicas ni una excepción al gobierno visual. Para diagramas `17.1`-`17.3`:

1. Define primero la topología desde C4, `10.1`, `17`, decisiones e IaC; no permitas que el MCP proponga servicios solo para completar el dibujo.
2. Lee `references/drawio-iconos-nube.md`, `assets/iconos/catalogo_iconos_curado.json` y `assets/iconos/aliases_iconos.json` antes de invocarlo.
3. Solicita XML sin compresión, una página por proveedor y un atributo `archiIconId` válido en cada recurso cloud.
4. Si el MCP no permite agregar atributos personalizados, exporta el XML y complétalos antes de aprobar el artefacto.
5. Ejecuta `scripts/validate_drawio_catalog.py --drawio <archivo> --provider <azure|aws|gcp> --strict` y `scripts/validate_drawio_layout.py --drawio <archivo> --strict`. Corrige el archivo; no omitas la validación por haber usado el MCP: el layout automático de un MCP no garantiza conectores sin cruces ni contenedores correctos.
6. Registra en `17-Vista-de-Despliegue.md` que el artefacto fue asistido por MCP, junto con catálogo, hash, fecha, resultado y excepciones.

La referencia `assets/drawio/referencia-despliegue-azure.drawio` puede adjuntarse como guía de composición. Su contenido `[CT-*]` nunca debe sobrevivir en el entregable ni utilizarse para inferir la solución.

## Reglas

- Esta validación se hace **una vez por sesión de trabajo del skill**, no antes de cada diagrama individual — si ya confirmaste disponibilidad (o su ausencia) al principio, no repitas el `ToolSearch` por cada diagrama subsiguiente del mismo documento.
- No dependas de que el MCP esté disponible para poder generar el documento de arquitectura — es una mejora de calidad/interactividad, no un bloqueante. El fallback a Mermaid/`.drawio` manual siempre debe producir un documento completo y correcto.
- Para escenas Excalidraw sigue `references/guia-excalidraw.md` (paleta, vinculaciones, construcción por secciones) y valida con `scripts/validate_excalidraw.py`; para despliegue `.drawio` sigue `references/drawio-iconos-nube.md`. Todo resultado del MCP se mira con `scripts/render_preview.py` o el export real antes de entregar.
- Excalidraw no reemplaza ni relaja las reglas: todo diagrama, generado a mano o por MCP, cumple `references/guia-calidad-visual-diagramas.md`.
- Si el usuario pide explícitamente un tipo de artefacto (p. ej. "quiero el diagrama editable en Excalidraw"), prioriza esa preferencia sobre la elección por defecto de esta guía.
