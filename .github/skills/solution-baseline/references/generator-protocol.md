# Protocolo de generadores

## Operaciones

| Operación | Efecto | Salida mínima |
|---|---|---|
| `metadata` | Lectura | Identidad, versión, capabilities, compatibilidad y permisos |
| `inspect` | Lectura | Stack, receipt, archivos y drift preliminar |
| `plan` | Lectura | Versiones exactas, cambios, riesgos, conflictos y autorizaciones |
| `render` | Escritura temporal | Árbol candidato y hashes |
| `diff` | Lectura | Añadidos, modificados, eliminados y conflictos por ownership |
| `validate` | Lectura salvo artefactos temporales | Evidencia de comandos y gates |
| `upgrade` | Escritura aprobada | Migración aplicada y nuevo receipt |

La entrada y salida deben ser JSON/YAML validados. Devuelve siempre un generator result conforme al schema, incluso al fallar.

## Flujo seguro

1. Verifica versión, digest y confianza del adaptador/arquetipo.
2. Ejecuta `metadata` e `inspect` sin escritura.
3. Produce `plan` con idempotency key y lista exacta de efectos.
4. Renderiza en un directorio temporal fuera del destino.
5. Valida el render con herramientas del stack.
6. Calcula diff y clasifica cada ruta por ownership.
7. Obtén review/aprobación aplicable.
8. Aplica cambios mínimos y de forma atómica cuando sea posible.
9. Valida el destino real.
10. Escribe receipt y resultado; conserva evidencia.

## Selección del motor

Prefiere el motor idiomático que ofrezca schemas, dry-run o árbol virtual y migraciones semánticas. Ejemplos: Nx para workspaces JS/TS, Copier para plantillas con actualización, `dotnet new` para .NET y Spring Initializr/generadores del ecosistema Java. No fuerces una herramienta cuando el proyecto ya use otra compatible.

Un adaptador traduce el protocolo a comandos del motor y define detectores, validadores, permisos y restricciones. No codifiques reglas tecnológicas en el orquestador.

## Aplicación y rollback

`apply` lo habilita el orquestador, no el generador por iniciativa propia. Antes de aplicar, conserva la evidencia necesaria para revertir solo los cambios propios. No declares rollback si no fue probado. En multi-repo usa compensación por paso; no prometas atomicidad global.

## Resultado estructurado

Incluye `status`, `artifacts`, `decisions`, `warnings`, `next_steps`, `agent_context`, `evidence`, hashes y `compensation`. La combinación `repository_id + operation + idempotency_key + input_hash` identifica un intento lógico.

