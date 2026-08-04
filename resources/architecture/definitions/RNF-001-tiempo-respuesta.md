# RNF-001: Tiempo de Respuesta

**Tipo:** Requerimiento no funcional
**Categoría:** Rendimiento
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 6.1

## Descripción
La plataforma debe cumplir con los siguientes tiempos de respuesta máximos:

- **Consultas normales (dashboard, listados, CRUD):** menor a 3 segundos.
- **Respuesta del chat IA (agente conversacional):** menor a 10 segundos.
- **Generación de reportes PDF:** menor a 10 segundos.

Estos tiempos se miden desde que el usuario realiza la acción hasta que la interfaz muestra el resultado completo (incluyendo procesamiento en backend, inferencia de modelos y renderizado en frontend).

## Criterio medible / restricción concreta
- Tiempo de respuesta < 3s para el percentil 95 de las consultas normales.
- Tiempo de respuesta del chat IA < 10s para el percentil 95.
- Mediciones realizadas con carga de usuarios concurrentes representativa.

## Impacto en la arquitectura
- Requiere optimización de consultas a base de datos (índices, caché).
- El chat IA (<10s) condiciona la elección del LLM (modelos más pequeños o autoalojados pueden ser más rápidos que APIs comerciales).
- La generación de PDFs puede requerir procesamiento asíncrono (cola de trabajos) para no bloquear al usuario.
- Necesidad de CDN y caché en frontend (Angular) para carga inicial rápida.

## Notas del analista
- El RFP no especifica bajo qué condiciones de carga se miden estos tiempos (número de usuarios concurrentes). Se recomienda definir: "con hasta 500 usuarios concurrentes" como baseline inicial.
- La latencia del chat IA depende fuertemente del modelo LLM elegido y de si se usa una API externa (latencia de red) o un modelo autoalojado.
