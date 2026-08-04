# RD-003: Sistema Híbrido de Recomendación — Reglas + ML

**Tipo:** Información de diseño
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 5.9, 5.10; contextAgro.md (Visión)

## Descripción
El motor de recomendaciones de AgroIA debe implementar una arquitectura híbrida que combina dos enfoques complementarios:

### 1. Sistema Experto basado en Reglas
- **Fuente:** reglas agronómicas extraídas de fuentes oficiales (Cenicafé, UPRA, AGROSAVIA, FAO).
- **Tipo de reglas:**
  - Umbrales: "si pH < 5.5 para café → suelo demasiado ácido".
  - Compatibilidades: "no mezclar fertilizante X con Y porque se bloquean".
  - Relaciones: "exceso de K bloquea absorción de Mg".
- **Implementación:** reglas almacenadas en base de datos, evaluadas por un motor de reglas ligero (Python, sin necesidad de un BRMS pesado como Drools).
- **Propósito:** garantizar que las recomendaciones nunca violen principios agronómicos básicos. Actúa como "guarda rieles" del sistema.

### 2. Modelos de Machine Learning
- **Modelos:** Random Forest, XGBoost, LSTM (descritos en RF-012).
- **Propósito:** capturar patrones complejos y no lineales que las reglas simples no pueden modelar (ej. interacción entre 5+ variables simultáneamente).
- **Salida:** predicciones con nivel de confianza (probabilidad, score).

### 3. Orquestador de Recomendaciones
- Recibe las salidas de ambos componentes (reglas + ML).
- **Si concordancia:** la recomendación se publica con confianza alta.
- **Si discordancia:** se eleva para revisión por un técnico agrónomo. En el MVP, gana la regla del sistema experto (principio de precaución agronómica).
- Genera la justificación combinando: variables que influyeron, regla aplicada, confianza del modelo, riesgos y beneficios.

## Elementos de referencia
- Diagrama de flujo: sensores → preprocessing → [ML models // Rules engine] → orchestrator → recommendation output.
- El orquestador también consulta el catálogo de cultivos (RF-009) para obtener los umbrales ideales de comparación.

## Notas del analista
- Este diseño híbrido es una fortaleza del proyecto: combina la transparencia y seguridad de las reglas (explicabilidad total) con la capacidad predictiva del ML (patrones complejos).
- El principio de "en caso de duda, gana la regla" es conservador pero seguro. Conforme el sistema acumule más datos y validación en campo, se puede ajustar el peso relativo de cada componente.
- La regla "no alucinar" (RNF-009) se implementa en el orquestador: si ni las reglas ni los modelos tienen suficiente evidencia, el sistema responde "No hay datos suficientes para determinar...".
