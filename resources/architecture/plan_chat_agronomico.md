# Plan de Implementación — Asistente Agronómico Inteligente (Chat Experto)

> Evolución del chat de AgroIA: de conversación simple a **capa conversacional
> agronómica especializada** conectada al conocimiento real de la plataforma.

## 1. Análisis de la arquitectura actual (qué se reutilizó)

| Componente existente | Ubicación | Reutilización en el chat |
|---|---|---|
| Motor de recomendaciones (UC1/UC2) | `services/orchestrator.py` | El chat ejecuta `analyze()` para obtener clasificación, recomendaciones y ranking de cultivos |
| Reglas agronómicas | `reglas_agronomicas` + `services/rules_engine.py` | Rangos ideales y acciones correctivas como grounding |
| Datos de sensores | `sensor_readings` (18 variables + pos_x/pos_y) | Lectura más reciente + mapa de calor como contexto |
| Fincas y catálogo | `fincas`, `cultivos`, `fichas_tecnicas` | Ubicación, altitud, umbrales y fuentes del cultivo |
| Control de acceso | `services/acceso.py` | El chat solo ve fincas del rol (admin/agrónomo/cliente) |
| RAG base (pgvector) | `apps/rag` | Reservado para corpus documental; el chat usa la base estructurada local |
| Clima | `settings.ideam_api_key` | Solo época del año + sensores ambientales (sin inventar pronósticos) |

**Principio:** no se duplicó el modelo agrícola; el chat CONSULTA el mismo motor.

## 2. Arquitectura implementada

```
Usuario → Chat (frontend reportes) → POST /api/v1/chat/consultar
   → Orquestador Agronómico (`services/agronomo_chat.py::respuesta_orquestada`)
        ├─ Intención: cálculos (cal/fertilizante/riego) → Herramientas (`agronomo_kb.py`)
        ├─ Clima/época → contexto_climatico (fecha, región, sensores; sin pronóstico inventado)
        ├─ Diagnóstico diferencial → diagnostico_diferencial (varias causas + datos que faltan)
        ├─ "¿Por qué este cultivo?" → explicación con los resultados reales del motor
        └─ Conversacional general → motor local detallado por rol
   → Contexto para LLM (si OPENAI_API_KEY): finca + lectura + reglas + ficha +
     análisis + clima + base de conocimiento con fuentes → LLM (razonamiento)
   → Memoria de finca: tabla `chat_memoria` (pregunta/respuesta/fuentes/confianza)
```

## 3. Modelo de contexto (siempre con los datos reales disponibles)

`{finca, lectura, cultivo, reglas, analisis(uc1/uc2), clima, rol}`
Ningún campo se asume: si falta, se declara explícitamente ("Me falta X para responder").

## 4. Base de conocimiento agronómica (`services/agronomo_kb.py`)

Estructurada por temas con fuentes trazables (Cenicafé, Agrosavia, UPRA, ICA, IDEAM, FAO):
- **Suelos**: pH, materia orgánica, compactación, salinidad.
- **Encalado**: cal agrícola/dolomita, cuándo aplicar, riesgo de sobreencalado.
- **Riego**: frecuencia por textura, horarios, evapotranspiración práctica.
- **Fertilización**: N/P/K, orgánica vs química, foliar.
- **Diagnóstico diferencial**: hojas amarillas, no crece, pierde hojas, suelo duro.
- **Clima**: calendario de lluvias por región (IDEAM) para época seca/lluviosa.
- Ruta futura: indexar documentos (Agrosavia/ICA/IDEAM) en `rag_chunks` (pgvector) y
  que el orquestador consulte RAG cuando el corpus exista.

## 5. Herramientas del agente (cálculos, no los hace el LLM)

| Herramienta | Entradas requeridas | Salida |
|---|---|---|
| `calcular_encalado` | pH, textura, materia orgánica, cultivo | t/ha de cal + fórmula + limitaciones |
| `calcular_fertilizante` | recomendaciones (rango ideal), lectura | kg/ha de N/P/K a corregir |
| `recomendar_riego` | textura (humedad ideal opcional) | frecuencia + forma de riego |

Si falta un insumo, la herramienta devuelve la lista de lo que falta (anti-alucinación).

## 6. Memoria de finca

- Tabla `chat_memoria` (migración 007): finca, usuario, rol, pregunta, respuesta,
  fuentes, confianza, fecha.
- `GET /api/v1/chat/memoria/{finca_id}` devuelve las últimas 20 interacciones:
  el usuario puede volver después y continuar la conversación.

## 7. Seguridad y control de alucinaciones

1. Grounding estricto: la respuesta solo usa datos reales de la finca + base de conocimiento con fuente.
2. Diferenciación explícita: conocimiento general vs datos de la finca vs inferencia vs recomendación.
3. Cálculos solo vía herramientas deterministas; el LLM nunca calcula dosis.
4. Clima: sin fuente externa no se inventa pronóstico; se declara qué falta (IDEAM_API_KEY).
5. Confianza por respuesta (Alta/Media/Baja) y lista de "lo que falta" para ser más preciso.
6. Diagnóstico diferencial: nunca una sola causa sin evidencia.

## 8. Perfiles de usuario

- `cliente` → productor: lenguaje sencillo, sin unidades técnicas.
- `tecnico/investigador` → técnico: números y rangos.
- `agronomo/admin` → experto: terminología profesional y fuentes.

## 9. Estrategia de evaluación

| Criterio (SDD §26) | Cómo se verifica |
|---|---|
| Contexto de finca/reporte/cultivo/sensores | Casos de prueba contra Demo Integral (pH 6.1, MO 11.5%, humedad 34%) |
| Cálculos | "¿Cuánta cal necesito?" → dosis o lista de faltantes |
| Clima | "¿Puedo fertilizar esta semana?" → época + consejo, sin pronóstico inventado |
| Diagnóstico | "Hojas amarillas" → lista diferencial + datos que piden |
| Anti-alucinación | Preguntas con datos faltantes → respuesta declara lo que falta |
| Memoria | `GET /chat/memoria/{finca}` tras consultas |
| Adaptación por rol | Misma pregunta como Cliente vs Agrónomo (lenguaje distinto) |

## 10. Plan de implementación (estado)

- [x] 1. Análisis de arquitectura y componentes reutilizables
- [x] 2. Base de conocimiento estructurada con fuentes
- [x] 3. Herramientas de cálculo (cal, fertilizante, riego)
- [x] 4. Clima disponible sin inventar (época + sensores)
- [x] 5. Diagnóstico diferencial de problemas
- [x] 6. Explicación de la recomendación del cultivo ("¿por qué café?")
- [x] 7. Respuestas fundamentadas (qué/por qué/datos/fuentes/falta/confianza)
- [x] 8. Memoria de finca (tabla + endpoint)
- [x] 9. Orquestador con detección de intención sobre el motor existente
- [x] 10. Contexto enriquecido para el LLM (cuando haya API key)
- [ ] 11. Carga de documentos (Agrosavia/ICA/IDEAM) en RAG pgvector
- [ ] 12. Integración del pronóstico real de IDEAM (IDEAM_API_KEY)
- [ ] 13. Visión artificial: diagnóstico con fotografías (futuro)
