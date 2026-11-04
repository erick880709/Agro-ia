# Selección de arquetipos

## Gates no compensables

Rechaza antes de puntuar cuando exista:

- Fuente no autorizada, integridad no verificable o owner ausente.
- Licencia incompatible o procedencia desconocida.
- Estado `retired`, o `deprecated` sin excepción y ruta soportada.
- Runtime mayor, workload o estilo arquitectónico incompatibles.
- Controles obligatorios de seguridad ausentes y no adicionables.
- Generador no reproducible o incompatible con el protocolo.
- DevOps, IaC o empaquetado operacional inseparable.
- Hooks requeridos sin confianza y autorización suficientes.

## Puntuación posterior a gates

Puntúa únicamente candidatos elegibles:

| Dimensión | Peso sugerido |
|---|---:|
| Workload y modelo de ejecución | 25 |
| Lenguaje/runtime/framework | 20 |
| Estilo arquitectónico | 15 |
| Contratos y persistencia | 10 |
| Seguridad y calidad | 15 |
| Capabilities requeridas | 10 |
| Soporte y madurez | 5 |

No uses la puntuación para compensar un gate. Ante empate, prefiere versión soportada, fuente de mayor confianza, menor número de overlays y mejor ruta de upgrade.

## Estrategia resultante

- `reuse`: coincidencia directa; fija versión y digest.
- `compose`: familia más capabilities compatibles.
- `overlay`: adaptación declarativa pequeña que no cambia la estructura esencial.
- `create-archetype`: no hay coincidencia y existe evidencia de reutilización.
- `project-specific`: el caso no es generalizable; no contamines el catálogo.
- `blocked`: arquitectura o compatibilidad insuficiente.

## Versiones

Acepta intención `stable`, `recommended`, `preview` o `exact`, pero resuélvela a un valor exacto antes del dry-run. Registra tanto la intención como la resolución. Nunca uses `latest` ni rangos abiertos como resultado aplicado.

Usa el comando `resolve` para obtener candidatos reproducibles; la decisión final sigue requiriendo revisar restricciones arquitectónicas que el catálogo no pueda representar.

