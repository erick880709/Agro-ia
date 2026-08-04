# PROJECT_CONTEXT.md

# AI Agricultural Advisor
Versión: 1.0

---

# Objetivo del proyecto

Construir una plataforma inteligente que permita analizar el estado de un terreno agrícola mediante sensores IoT, datos geográficos y datos meteorológicos para generar recomendaciones automáticas sobre:

- Qué cultivar.
- Qué fertilizantes aplicar.
- Qué nutrientes hacen falta.
- Qué problemas presenta el suelo.
- Qué acciones debe realizar el agricultor.
- Cómo maximizar la productividad.
- Cómo reducir costos.
- Cómo disminuir el impacto ambiental.

La plataforma deberá funcionar como un ingeniero agrónomo virtual.

---

# Visión

La IA debe comportarse como un experto agrícola con experiencia en:

- Edafología
- Agronomía
- Fertilidad del suelo
- Nutrición vegetal
- Meteorología
- Cultivos tropicales
- Agricultura de precisión
- Agricultura regenerativa

Nunca responderá únicamente con reglas simples.

Debe razonar considerando múltiples variables simultáneamente.

---

# Problema

Los agricultores normalmente conocen muy poco sobre el estado real de su suelo.

Realizan fertilizaciones empíricas.

Esto genera:

- desperdicio de fertilizantes
- baja productividad
- enfermedades
- baja rentabilidad
- contaminación

La plataforma pretende eliminar esas decisiones empíricas.

---

# Objetivos funcionales

La IA debe ser capaz de responder:

¿Qué cultivo es recomendable sembrar?

¿Qué nutrientes hacen falta?

¿Qué exceso de nutrientes existe?

¿Cuál es el pH ideal?

¿Cuánto fertilizante aplicar?

¿Cuánto calcio agregar?

¿Cuánto nitrógeno agregar?

¿Cuánto fósforo agregar?

¿Cuánto potasio agregar?

¿Existe riesgo de enfermedad?

¿Cuál será el rendimiento esperado?

¿Cuándo sembrar?

¿Cuándo cosechar?

¿Cuándo regar?

¿Cuándo volver a medir?

---

# Variables de entrada

## Ubicación

Latitud

Longitud

Altitud

Departamento

Municipio

País

Tipo de terreno

Pendiente

Orientación solar

---

## Sensores

pH

Humedad del suelo

Temperatura del suelo

Conductividad eléctrica

Materia orgánica

Nitrógeno

Fósforo

Potasio

Calcio

Magnesio

Azufre

Hierro

Zinc

Cobre

Manganeso

Boro

Sodio

Capacidad de intercambio catiónico

Salinidad

---

## Variables ambientales

Temperatura ambiente

Humedad relativa

Radiación solar

Velocidad del viento

Precipitación

Evapotranspiración

Presión atmosférica

Índice UV

---

## Variables históricas

Últimos cultivos

Fecha de siembra

Fecha de cosecha

Producción

Fertilizaciones

Plaguicidas

Riego

Enfermedades

Plagas

---

## Variables económicas

Precio del cultivo

Costo de fertilizantes

Costo de transporte

Costo de mano de obra

Rentabilidad estimada

Demanda del mercado

---

# Catálogo de cultivos

Cada cultivo debe tener una ficha técnica.

Ejemplo:

Nombre

Nombre científico

Familia

Temperatura ideal

Humedad ideal

pH ideal

Nitrógeno requerido

Fósforo requerido

Potasio requerido

Calcio requerido

Altitud recomendada

Tipo de suelo

Tiempo de cosecha

Enfermedades frecuentes

Plagas frecuentes

Producción esperada

Mercados objetivo

Rentabilidad

---

# Motor de conocimiento

La IA debe conocer:

Relación entre nutrientes

Interacciones químicas

Bloqueo de nutrientes

Compatibilidad entre fertilizantes

Cultivos compatibles

Rotación de cultivos

Asociación de cultivos

Enfermedades

Plagas

Hongos

Malezas

Buenas prácticas agrícolas

---

# Datos externos

La plataforma deberá integrarse con:

Pronóstico climático

Imágenes satelitales

NDVI

Índice de vegetación

Mapas de suelo

Bases nacionales agrícolas

Precios de mercado

Alertas fitosanitarias

---

# Modelos de IA

## Modelo 1

Clasificación del estado del suelo

Salida

Excelente

Bueno

Regular

Malo

Crítico

---

## Modelo 2

Predicción del cultivo ideal

Entrada

Variables del suelo

Variables climáticas

Variables geográficas

Salida

Top 5 cultivos recomendados

Score

Confianza

---

## Modelo 3

Detección de deficiencias nutricionales

Entrada

Sensores

Salida

Lista de nutrientes faltantes

Cantidad requerida

Prioridad

---

## Modelo 4

Recomendación de fertilización

Salida

Tipo de fertilizante

Cantidad

Frecuencia

Costo

---

## Modelo 5

Predicción de rendimiento

Salida

Toneladas por hectárea

Intervalo de confianza

Factores limitantes

---

## Modelo 6

Predicción de enfermedades

Entrada

Clima

Humedad

Cultivo

Salida

Riesgo

Nivel

Recomendaciones

---

# Agente de IA

La aplicación tendrá un asistente conversacional.

El asistente deberá responder preguntas como:

¿Qué puedo sembrar aquí?

¿Por qué mi suelo tiene bajo rendimiento?

¿Cómo puedo aumentar la producción?

¿Qué fertilizante debo aplicar?

¿Cuánto debo aplicar?

¿Cuándo debo sembrar?

¿Qué cultivo deja mayor rentabilidad?

¿Existe riesgo de enfermedades?

¿Qué significa tener un pH de 5.2?

¿Qué debo hacer primero?

---

# Capacidades del agente

Interpretar sensores.

Interpretar mapas.

Interpretar imágenes satelitales.

Explicar conceptos agrícolas.

Generar recomendaciones.

Priorizar acciones.

Responder en lenguaje sencillo.

Responder técnicamente.

Explicar el porqué de cada recomendación.

Mostrar nivel de confianza.

Nunca inventar información.

---

# Arquitectura IA

La solución utilizará varios motores especializados.

## Sistema experto

Reglas agronómicas.

## Machine Learning

Predicciones.

## LLM

Explicaciones.

Chat.

Asistente virtual.

## RAG

Consulta de:

Investigaciones

Normativas

Manuales agrícolas

Fichas técnicas

Investigaciones científicas

---

# Principios

Las recomendaciones deben estar justificadas.

Toda recomendación debe incluir evidencia.

Debe indicar nivel de confianza.

Debe indicar qué variables influyeron.

Debe indicar riesgos.

Debe indicar beneficios.

Debe indicar costo estimado.

Debe indicar impacto esperado.

---

# Experiencia del usuario

La aplicación debe ser sencilla.

El agricultor no necesita conocimientos técnicos.

Toda recomendación debe explicarse en lenguaje natural.

También debe existir un modo experto para ingenieros agrónomos.

---

# Futuras funcionalidades

Predicción mediante imágenes de drones.

Predicción mediante fotografías del cultivo.

Integración con sensores IoT en tiempo real.

Alertas automáticas.

Predicción de sequías.

Predicción de inundaciones.

Detección de plagas mediante visión artificial.

Optimización automática del riego.

Simulación de escenarios agrícolas.

Recomendaciones financieras para el productor.