# Multi-repositorio y orquestación

## DAG

Modela nodos para contratos, archetype-builds, repositorios, validaciones e integración. Una dependencia debe expresar una barrera real. Orden típico:

```text
discovery(read-only)
  → decisiones globales y contratos congelados
  → archetype-build/approve/publish cuando aplique
  → render/apply por repositorio
  → validación local
  → integración cross-repo
  → consolidación y handoff
```

## Paralelismo permitido

- Lectura e inventario de repositorios.
- Resolución de stacks y drift preliminar.
- Instanciación en repositorios independientes después de congelar contratos y versiones.
- Validación local y revisiones de solo lectura.

Antes de abrir una ola, valida un contrato `assignments` con `check-concurrency`. La política canónica limita a cuatro subagentes activos, cuatro readers, dos writers, un writer por repositorio y un writer de catálogo. El runtime puede reducir estos valores. Consulta [agent-operations.md](./agent-operations.md) para instalación y verificación ejecutable.

## Barreras secuenciales

- Resolver contradicciones arquitectónicas.
- Congelar OpenAPI, AsyncAPI, schemas y eventos.
- Publicar un arquetipo nuevo.
- Modificar archivos compartidos.
- Integrar y cerrar el run.

## Ownership y leases

Asigna un writer por repositorio o zona disjunta. Usa lease con owner, run ID, recurso, inicio y expiración. Renovar requiere conservar el mismo owner; recuperar uno vencido debe quedar auditado. El catálogo permanece de solo lectura durante la instanciación.

Los workers no escriben el run manifest. Entregan generator results; el orquestador valida esquema, idempotencia y hashes antes de consolidar mediante escritura atómica.

## Saga y fallos parciales

Cada paso declara efecto, idempotency key y compensación segura. Ante fallo:

1. Detén dependientes del nodo fallido.
2. Conserva resultados independientes válidos.
3. Compensa solo operaciones explícitamente reversibles.
4. Marca estado `partial` o `blocked` con siguiente acción.
5. En `resume`, verifica hashes antes de reutilizar checkpoints.

No borres repositorios ni reviertas trabajo ajeno para fingir atomicidad distribuida.

## Repositorios remotos

Generar contenido local y crear Git local son operaciones diferentes de crear/publicar un remoto. La extensión `repository-provider` requiere autorización explícita y nunca agrega pipelines o infraestructura.
