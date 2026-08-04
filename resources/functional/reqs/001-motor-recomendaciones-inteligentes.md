---
id: 001
slug: motor-recomendaciones-inteligentes
ia_cierre: 14/100
rondas: 4
estado: lista-para-diseno
fecha: 2026-08-03
---

# NECESIDAD DE NEGOCIO REFINADA

Plataforma de diagnóstico agronómico inteligente que, a partir de mediciones de sensores IoT de suelo (18 variables), determina la aptitud del terreno para un cultivo objetivo usando la clasificación UPRA (Alta/Media/Baja/No apta). Cuando el suelo no es apto, el sistema genera recomendaciones correctivas específicas, justificadas y accionables — con nivel de confianza, costo estimado e impacto esperado — combinando un motor de reglas agronómicas (sistema experto) con 5 modelos de ML (Random Forest, XGBoost, LSTM). Toda recomendación con F1-score < 0.80 se muestra con advertencia de "baja confianza" y se escala a un técnico agrónomo para revisión en un plazo máximo de 10 días. Si el técnico no revisa, la recomendación se bloquea hasta que haya revisión. La responsabilidad final de aplicar o no la recomendación es del agricultor.

**Fuente(s) de origen**
- `resources/functional/requests/RF-013-recomendaciones-inteligentes.md`
- `resources/functional/requests/RF-012-motor-predictivo-modelos-ia.md`
- `resources/functional/requests/RF-010-motor-conocimiento-agronomico.md`
- `resources/architecture/definitions/RNF-009-no-alucinacion-ia.md`
- `resources/design/models/RD-003-sistema-hibrido-recomendacion.md`

**Justificación**

En Colombia, los agricultores toman decisiones de fertilización de forma empírica — no basada en datos. Esto genera desperdicio de fertilizantes, baja productividad, enfermedades, baja rentabilidad y contaminación ambiental. Las pérdidas postcosecha pueden alcanzar hasta el 40% en ciertos cultivos (Ministerio de Agricultura / DANE). Más del 70% de los productores son pequeños y medianos con alta vulnerabilidad técnica y económica. No existe una plataforma unificada que combine sensores IoT de campo, datos climáticos oficiales (IDEAM) y conocimiento agronómico verificable (Cenicafé, UPRA, AGROSAVIA) para generar inteligencia accionable.

**Actores**

| Rol | Tipo | Responsabilidad |
|-----|------|-----------------|
| Agricultor | Beneficiario / Ejecutor | Recibe recomendaciones; decide si las aplica; responsable final del resultado en su cultivo |
| Técnico Agrónomo | Validador / Aprobador | Revisa recomendaciones de baja confianza (F1 < 0.80) en ≤10 días; valida reglas agronómicas; anota y corrige predicciones |
| Investigador IES | Ejecutor | Entrena, valida y administra modelos de ML; propone nuevas reglas basadas en evidencia científica |
| Administrador | Aprobador | Gestiona la configuración del motor; monitorea infraestructura y modelos |

**Alcance**

- ✅ IN SCOPE (MVP, 5 modelos):
  - Modelo 1: Clasificación del estado del suelo (metodología UPRA: Alta/Media/Baja/No apta)
  - Modelo 2: Predicción del cultivo ideal (top 5 cultivos con score y confianza)
  - Modelo 3: Detección de deficiencias nutricionales (nutrientes faltantes, cantidad requerida, prioridad)
  - Modelo 4: Recomendación de fertilización (tipo, cantidad en kg/ha, frecuencia, costo estimado)
  - Modelo 5: Predicción de rendimiento (ton/ha, intervalo de confianza, factores limitantes)
  - Motor de reglas agronómicas (sistema experto): relaciones entre nutrientes, bloqueos, compatibilidad de fertilizantes, rotación de cultivos, BPA
  - Orquestador híbrido: combina reglas + ML; discordancia → gana regla (principio de precaución)
  - Pipeline de justificación: variables que influyeron, nivel de confianza, riesgos, beneficios, costo estimado, impacto esperado
  - Cold-start: modelos iniciales con datasets públicos (Kaggle) + reglas Cenicafé/UPRA, calibrados con datos del piloto Quindío

- ✅ IN SCOPE (MVP, reglas de operación):
  - Variables bloqueantes (si falta cualquiera → "datos insuficientes"): pH, Nitrógeno (N), Fósforo (P), Potasio (K)
  - Variable no bloqueante confirmada: Boro (B)
  - Resto de variables: [PENDIENTE DE DEFINIR — impacto: define el circuito de degradación parcial del motor. Asumir criterio conservador: materia orgánica y conductividad eléctrica como bloqueantes hasta validación con agrónomo]
  - F1-score ≥ 0.80: recomendación publicada con confianza normal
  - F1-score < 0.80: recomendación publicada con advertencia "baja confianza" + escalada a técnico agrónomo
  - Técnico no revisa en 10 días → recomendación bloqueada hasta revisión
  - No alucinación: sin evidencia suficiente → "No hay datos suficientes para determinar..."

- ❌ OUT OF SCOPE (MVP):
  - Modelo 6: Predicción de enfermedades/plagas (requiere datos que no existirán hasta avanzado el piloto)
  - Detección de plagas por visión artificial (futuro)
  - Integración con pasarela de pagos (solo preparación arquitectónica)

**Criterios de Aceptación**

```
DADO que un agricultor tiene una finca registrada con datos de sensores IoT
Y ha seleccionado un cultivo objetivo (o solicita sugerencia)
CUANDO solicita un análisis de aptitud del suelo
ENTONCES el sistema compara cada variable del sensor contra los umbrales ideales
  de la ficha técnica del cultivo
Y genera una clasificación de aptitud según UPRA (Alta/Media/Baja/No apta)
Y para cada variable fuera de rango, genera una recomendación correctiva específica
Y cada recomendación incluye: variables que influyeron, nivel de confianza,
  riesgos, beneficios, costo estimado e impacto esperado
Y si el F1-score de la predicción es < 0.80, la recomendación muestra
  advertencia "baja confianza" y se escala al técnico agrónomo
Y las recomendaciones se expresan en lenguaje natural entendible por el agricultor
```

```
DADO que faltan una o más variables bloqueantes (pH, N, P, K)
CUANDO se solicita un análisis
ENTONCES el sistema responde "Datos insuficientes para generar una recomendación.
  Se requiere medir: [lista de variables faltantes]"
Y no genera recomendaciones parciales ni inventa valores
```

```
DADO que el sistema experto (reglas) y el modelo ML generan recomendaciones discordantes
CUANDO el orquestador evalúa ambas salidas
ENTONCES prevalece la recomendación del sistema experto (principio de precaución)
Y la discordancia se escala al técnico agrónomo para revisión en ≤10 días
Y si el técnico no revisa en 10 días, la recomendación se bloquea hasta revisión
```

**Restricciones y Supuestos**

- **Restricciones:**
  - Stack frontend: Angular 21 (vinculante)
  - Stack backend y modelos: Python — FastAPI, scikit-learn, XGBoost, TensorFlow/PyTorch (vinculante)
  - LLM agente conversacional: OpenAI (GPT-4); los datos de agricultores pasan por infraestructura del proveedor
  - No alucinación: tasa de afirmaciones no respaldadas < 1% en evaluaciones de calidad
  - Cumplimiento Ley 1581 de 2012 (habeas data)
  - Clasificación de aptitud: estándar UPRA (Alta/Media/Baja/No apta), no escala propia
  - Piloto validado en café, Quindío, con Comité de Cafeteros

- **Supuestos validados:**
  - Los sensores IoT y la red LoRaWAN son provistos por el aliado tecnológico; la plataforma solo recibe datos
  - Los datasets de Kaggle se usan solo como baseline metodológico, no como fuente de recomendaciones directas
  - El rendimiento de largo plazo (1.2 → 1.8 ton/ha) se medirá en ciclos completos de cosecha post-piloto
  - La responsabilidad legal de aplicar una recomendación es del agricultor

- **Supuestos no validados:**
  - Licencia CC BY-NC-ND de Cenicafé permite uso comercial del corpus en el RAG — [PENDIENTE DE DEFINIR — impacto: requiere validación legal con Cenicafé/FNC antes de producción]
  - Variables bloqueantes completas más allá de pH, N, P, K — [PENDIENTE DE DEFINIR — impacto: afecta el circuito de degradación parcial]

**Métricas de Éxito**

| Métrica | Línea Base | Meta | Plazo |
|---------|-----------|------|-------|
| F1-score de modelos de clasificación (Modelos 1, 2, 3) | N/A (cold-start) | > 0.80 | Fin de piloto (6 meses) |
| Corrección de variables de suelo tras seguir recomendación (ej. pH de 4.8 → 5.5) | Valor inicial del piloto | Variable ajustada dentro del rango ideal del cultivo | 6 meses (piloto) |
| Tasa de alucinación (afirmaciones no respaldadas) | 0% (no existe sistema) | < 1% | Continuo |
| Rendimiento del cultivo (largo plazo, post-piloto) | 1.2 ton/ha (referencia café Quindío) | 1.8 ton/ha (+50%) | Ciclo completo de cosecha (~3 años) |
| Tiempo de respuesta del motor de recomendación | N/A | < 3 segundos (p95) | Producción |

**Prioridad (MoSCoW)**

- **Must Have:** Modelos 1–5 (clasificación, cultivo ideal, deficiencias, fertilización, rendimiento), sistema experto de reglas, orquestador híbrido, no alucinación, pipeline de justificación, modo agricultor (lenguaje natural), F1-score con advertencia < 0.80, clasificación UPRA
- **Should Have:** Cold-start con datasets Kaggle pre-entrenados, modo experto para técnicos, reentrenamiento sin interrumpir servicio
- **Could Have:** Dashboard de monitoreo de drift de modelos, feedback loop automático desde correcciones de técnicos
- **Won't Have (en este alcance):** Modelo 6 (enfermedades/plagas), detección por visión artificial, riego automático, simulación de escenarios

**Dependencias**

- Catálogo de cultivos con fichas técnicas (RF-009) — provee los umbrales ideales contra los que se compara
- Motor de conocimiento agronómico (RF-010) — provee las reglas del sistema experto
- Captura de datos de sensores IoT (RF-007) — provee las variables de entrada
- Integración con APIs externas: IDEAM (clima), IGAC (suelos), GIS (geolocalización) — RF-008
- MLOps (RT-010) — versionado, despliegue y monitoreo de modelos
- Estrategia de datos cold-start (RD-004) — datasets para entrenamiento inicial
- Aislamiento de datos entre clientes (RF-004) — cada agricultor solo ve sus análisis
- Agente conversacional RAG (RF-014) — presenta las recomendaciones en chat

**Brechas pendientes**

| Campo | Información faltante | Impacto en estimación/diseño |
|-------|---------------------|------------------------------|
| Lista completa de variables bloqueantes vs. no bloqueantes | Solo confirmadas: pH, N, P, K (bloqueantes), B (no bloqueante). Materia orgánica, conductividad eléctrica y otras 11 variables sin clasificar | Define el circuito de "recomendación parcial" vs. "datos insuficientes". Asumir criterio conservador (solo B, Na, micronutrientes como no bloqueantes) hasta validación con agrónomo |
| Licencia Cenicafé para uso comercial del RAG | CC BY-NC-ND actual; sin confirmación de FNC para uso en plataforma con membresías | Bloquea el uso del corpus de Cenicafé en producción comercial. Requiere gestión legal antes del lanzamiento |

---

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EVOLUCIÓN DEL ÍNDICE DE AMBIGÜEDAD
 Ronda 0 (inicial): 54/100
 Ronda 1:           35/100
 Ronda 2:           24/100
 Ronda 3:           17/100
 Ronda 4:           14/100  ← CIERRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

✅ **Lista para diseño/estimación**
