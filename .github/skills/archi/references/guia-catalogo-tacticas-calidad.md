# Guía: Catálogo de Tácticas y Matriz de Relación de Atributos de Calidad

Complementa `05-Atributos-de-Calidad.md`, `07-Resultado-QAW.md` y `18-Tacticas-y-Patrones.md`. Es un catálogo de partida — no una lista cerrada — para acelerar la identificación de **tácticas arquitectónicas** y anticipar conflictos entre atributos sin partir de cero en cada proyecto. No clasifica patrones arquitectónicos, de diseño, cloud o IA; para esos tipos usa `references/guia-catalogo-patrones.md`.

## Cómo usarlo

1. En `07` (QAW), usa la matriz de relación para explicar por qué dos atributos priorizados entran en tensión y forzar una conversación explícita de trade-off con los stakeholders, en vez de dejarlo implícito.
2. En `05`/`18`, para cada `QA-xx` priorizado, revisa el catálogo del atributo correspondiente y selecciona las tácticas realmente aplicables al proyecto — no copies la lista completa como si todas aplicaran. Registra cada táctica elegida como `TP-xxx` con tipo `Táctica arquitectónica` en `18-Tacticas-y-Patrones.md`, cita el `QA-xx` que resuelve y desarrolla su ficha según `references/guia-tacticas-patrones.md`. Si el mecanismo nombrado es en realidad un patrón arquitectónico, de diseño, cloud o IA, reclasifícalo con `references/guia-catalogo-patrones.md`.
3. Si el proyecto prioriza un atributo que no está en este catálogo (ej. observabilidad, escalabilidad como atributo independiente), documenta sus tácticas igual en `18`, citando la fuente si aplica (ej. Bass/Clements/Kazman, *Software Architecture in Practice*).

## Matriz de relación entre atributos de calidad

La cobertura base contiene 13 atributos e incluye Seguridad de manera explícita. Conflicto (`-`), complemento (`+`) o sin relación fuerte predefinida (celda vacía). Úsala como punto de partida — ajusta las celdas si la evidencia del proyecto muestra otra cosa.

| | Disponibilidad | Rendimiento | Flexibilidad | Integridad | Seguridad | Interoperabilidad | Mantenibilidad | Portabilidad | Confiabilidad | Reusabilidad | Robustez | Cap. de Prueba | Usabilidad |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Disponibilidad | | | | | | | | | + | | + | | |
| Rendimiento | | | - | | - | - | - | - | - | | - | - | - |
| Flexibilidad | | - | | - | - | | + | + | + | | | + | |
| Integridad | | - | | | + | - | | | | - | | - | - |
| Seguridad | | - | - | + | | - | + | | + | - | + | + | - |
| Interoperabilidad | | - | + | - | - | | | + | | | | | |
| Mantenibilidad | + | - | + | | + | | | | + | | | + | |
| Portabilidad | | - | + | | | + | - | | | + | | + | - |
| Confiabilidad | + | - | + | | + | | + | | | | + | + | + |
| Reusabilidad | | - | + | - | - | + | + | + | - | | | + | |
| Robustez | + | - | | | + | | | | + | | | | + |
| Cap. de Prueba | + | - | + | | + | | + | | + | | | | + |
| Usabilidad | | - | | | - | | | | | | + | - | |

Lectura rápida: rendimiento entra en conflicto con casi todo lo demás (agregar controles, capas o redundancia casi siempre cuesta tiempo de respuesta); disponibilidad, confiabilidad y capacidad de prueba se refuerzan entre sí con frecuencia.

## Catálogo de tácticas por atributo

### Desempeño (rendimiento)
- Administrar demanda: límites de tasa, backpressure, muestreo o degradación de trabajo no crítico.
- Administrar recursos: concurrencia, particionamiento, escalado y pools con límites explícitos.
- Reducir sobrecarga: caché, batching, compresión selectiva y disminución de saltos remotos.
- Mejorar eficiencia computacional: algoritmos, índices, formatos y rutas críticas optimizadas con evidencia.
- Arbitrar recursos: prioridades, colas y scheduling según criticidad.

### Disponibilidad
- Detectar fallos: health checks, heartbeat, watchdog y monitoreo de dependencias.
- Recuperar: redundancia activa/pasiva, failover, reinicio controlado y restauración de estado.
- Prevenir: eliminación de punto único de fallo, renovación preventiva y despliegue seguro con rollback.
- Reparar y reintegrar: resincronización, replay y retorno controlado del nodo recuperado.

### Flexibilidad
- Localizar cambios mediante límites modulares y responsabilidades cohesivas.
- Introducir abstracciones, puertos/adaptadores y dependency inversion para aislar variaciones.
- Diferir binding con configuración, feature flags o selección de estrategia en runtime.
- Versionar y extender contratos sin romper consumidores existentes.
- Encapsular variaciones detrás de un punto explícito de sustitución cuando exista más de una implementación real. Si se materializa con Strategy, Plugin u otro patrón de diseño, clasifica ese patrón por separado con `references/guia-catalogo-patrones.md`.

### Integridad
- Validar invariantes y datos en los límites de confianza.
- Usar atomicidad y límites transaccionales explícitos.
- Controlar concurrencia mediante versionado, bloqueo o compare-and-swap.
- Aplicar idempotencia y deduplicación a comandos/eventos repetibles.
- Detectar divergencias con conciliación, checksums y auditoría inmutable.

### Seguridad
- Identificar y autenticar sujetos con mecanismos acordes al riesgo.
- Autorizar del lado servidor con mínimo privilegio, segregación y denegación por defecto.
- Limitar exposición mediante segmentación, reducción de superficie y manejo seguro de secretos.
- Proteger datos con cifrado moderno en tránsito/reposo, integridad y rotación de claves.
- Validar y sanitizar entradas; codificar salidas según contexto.
- Detectar y responder mediante auditoría, alertas, correlación y contención.
- Mantener cadena de suministro y componentes actualizados, firmados y con soporte.
- Aplicar protocolos y encabezados seguros donde corresponda.

### Interoperabilidad
- Descubrir servicios/capacidades y negociar versiones cuando aplique.
- Gestionar interfaces mediante contratos explícitos, versionados y compatibles.
- Traducir sintaxis y semántica con adaptadores o capa anticorrupción.
- Coordinar con orquestación o coreografía según ownership y acoplamiento deseado.
- Verificar compatibilidad con contract testing y esquemas gobernados.

### Mantenibilidad
- Maximizar cohesión y minimizar acoplamiento entre módulos.
- Separar políticas de mecanismos y aislar dependencias volátiles.
- Externalizar configuración sin ocultar decisiones relevantes.
- Automatizar análisis estático, actualización de dependencias y controles de calidad.
- Mantener contratos, ownership y documentación ejecutable cerca de la implementación.

### Portabilidad
- Aislar servicios específicos del proveedor mediante puertos y adaptadores cuando exista driver real.
- Externalizar configuración, secretos y parámetros de entorno.
- Usar formatos, protocolos y APIs estándar en límites que requieran migración.
- Empaquetar reproduciblemente con contenedores/IaC sin asumir que ello garantiza portabilidad total.
- Probar despliegue y operación en los ambientes objetivo; documentar excepciones y lock-in aceptado.

### Confiabilidad
- Detectar y clasificar fallos antes de decidir retry o recuperación.
- Contener propagación con bulkheads, límites y aislamiento de recursos.
- Reintentar solo operaciones seguras/idempotentes con timeout, backoff, jitter y presupuesto.
- Abrir circuitos y degradar funcionalidad cuando una dependencia supera umbrales.
- Recuperar mediante checkpoint, replay, reconciliación o restauración verificable.

### Reusabilidad
- Separar capacidad estable de reglas específicas del contexto consumidor.
- Parametrizar variaciones comprobadas sin crear abstracciones especulativas.
- Publicar contratos estables, versionados y con compatibilidad definida.
- Empaquetar componentes con documentación, ejemplos y pruebas de contrato.
- Mantener adaptadores específicos fuera del núcleo reutilizable.

### Robustez
- Validar entradas, límites, tamaños y formatos antes de procesar.
- Aplicar timeout y consumo acotado de CPU, memoria, conexiones y colas.
- Usar backpressure, load shedding y cuotas ante saturación.
- Aislar fallos con circuit breaker, bulkhead y colas de cuarentena/DLQ.
- Proveer fallback o degradación segura sin ocultar errores críticos.

### Capacidad de prueba
- Observar estado y efectos mediante interfaces, eventos, logs y correlación controlada.
- Controlar dependencias, tiempo y aleatoriedad con inyección y dobles de prueba.
- Aislar datos y ambientes; crear fixtures reproducibles y limpiables.
- Verificar límites con pruebas de contrato y compatibilidad.
- Inyectar fallos y ejecutar pruebas de resiliencia para rutas degradadas.

### Usabilidad
- Informar estado, progreso y resultado de las acciones en tiempo de ejecución.
- Prevenir errores con restricciones, valores predeterminados y validación temprana.
- Permitir recuperación mediante cancelar, deshacer, reintentar o corregir contexto.
- Mantener interacción, navegación y terminología consistentes.
- Incorporar accesibilidad y ayudas contextuales verificables desde el diseño.

## Fuente

Catálogo derivado de la plantilla histórica `GRCpl101_AtributosCalidad` y de Bass, Clements, Kazman — *Software Architecture in Practice* (4th ed., 2021). Amplíalo con tácticas propias del dominio cuando el catálogo genérico no alcance.
