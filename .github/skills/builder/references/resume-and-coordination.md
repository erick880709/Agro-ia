# Reanudación y coordinación

## Reanudar desde evidencia

Localiza la spec y plan existentes y lee decisiones, tareas, resultados y bloqueos.
Compara fuentes, contratos y código actuales con la revisión registrada. Conserva
aprobaciones vigentes; marca obsoleta solo la evidencia cuyo insumo cambió.

Verifica efectos reales antes de repetir: registro de rutas, clases, migraciones,
modelo de datos y código implementado. Una casilla incompleta no demuestra ausencia
de implementación. No vuelvas a aplicar una migración por estado del plan; consulta
el mecanismo de migraciones en el entorno aislado autorizado. Una casilla completa
no demuestra que un cambio sobreviva a ediciones posteriores.

Si existe `review.md`, lee el veredicto y el estado de cada hallazgo: los
`aceptado` y `reabierto` son trabajo pendiente; un veredicto emitido sobre una
revisión anterior a cambios posteriores está vencido.

Reconcilia el plan con el repositorio y continúa los criterios pendientes. Preserva
éxitos parciales y registra el siguiente punto útil si hay bloqueo. No simules
atomicidad eliminando trabajo. Compensa solo efectos propios y reversibles cuando
sea necesario y seguro; no descartes cambios ajenos ni hagas operaciones remotas
para alinear un manifest local.

Cuando el trabajo deba continuar en otra sesión, deja un bloque de continuidad en
el expediente que ya usa el proyecto. Incluye únicamente: objetivo y modo original,
revisión o hashes observados, decisiones vigentes, criterios satisfechos y
pendientes, evidencia invalidada con su causa, bloqueo real y siguiente acción
reproducible. Enlaza artefactos voluminosos en lugar de copiarlos. Al reanudar,
verifica ese bloque contra el árbol actual; es una ayuda de descubrimiento, no una
fuente superior al código, contratos o decisiones posteriores.

## Delegación opcional

Delegar requiere herramientas disponibles, autorización y tareas que sean realmente
independientes. Si no se cumplen, ejecuta secuencialmente. No dependas del nombre
`Agent` de un proveedor ni exijas dos subagentes por tener frontend y backend.

Antes de delegar identifica dependencias y asigna un writer por archivo/zona.
Incluye tipos compartidos, lockfiles, manifiestos, contratos y documentación: una
separación nominal por capa no elimina colisiones. Usa worktrees/workspaces aislados
para escritores concurrentes y comprueba que corresponden al encargo; si no puedes
aislarlos de forma fiable, trabaja secuencialmente. Respeta los límites del runtime.

Cada encargo lleva:

- Alcance, criterios y restricciones pertinentes, sin reinterpretar el contrato.
- Workspace, ownership explícito y archivos compartidos que no puede modificar.
- Contrato canónico y revisión, fuentes y decisiones necesarias.
- Comandos de validación conocidos y resultado esperado de la tarea.
- Instrucción de preservar trabajo ajeno y reportar conflictos.

El coordinador mantiene el expediente compartido; cada worker devuelve cambios,
criterios cubiertos, comprobaciones ejecutadas y pendientes. Si un contrato necesita
cambio material, pausa sus consumidores dependientes y resuelve la revisión antes
de seguir; no permitas variantes incompatibles por worker.

Al integrar, compara con el estado actual, conserva cambios ajenos y valida el
comportamiento entre componentes aunque cada worker tenga tests verdes. En varios
repositorios registra las revisiones compatibles y el orden requerido; entrega
resultados por repositorio sin afirmar atomicidad de merge o despliegue.
