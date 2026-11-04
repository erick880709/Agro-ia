# Resumen Ejecutivo — RFP-AGROIA-003: Plataforma confiable de medición de suelo

**Cliente:** AGROINTELIGENTE COLOMBIA (AgroIA)
**Fecha del documento:** 3 de noviembre de 2026
**Documento fuente:** context/RFP-AGROIA-003 — Plataforma confiable de medición de suelo con el sensor JXBS-30.md

## Objetivo y alcance del proyecto
Que cada medición de suelo que llega a un reporte o recomendación tenga **origen trazable, calidad evaluada, incertidumbre explícita y un grado de evidencia** que limite lo que se puede concluir con ella.

**Dentro del alcance:** firmware/trama ESP32, ingesta, modelo de datos, motor de calidad, motor de reglas y orquestador (consumo de incertidumbre), calibración, reportes y pantallas, administración de parámetros, campaña de validación en campo, monitoreo del sensor.

**Fuera del alcance:** reemplazo del sensor, nuevos tipos de sensor, recetas de dosis sin laboratorio, rediseño del asesor conversacional.

**Principios:** (1) el valor crudo se conserva siempre; (2) todo umbral es parámetro administrable; (3) lo no medido se declara "no medido"; (4) sin laboratorio no hay dosis — el sensor sustenta tendencias, alertas y priorización de muestreo.

## Plazos
Fases (persona-días, sujetas a kickoff): F0 Verificación 3–5 · F1 Integridad 12–18 · F2 Incertidumbre 15–22 · F3 Calibración 20–30 más campaña · F4 Reportes/UI 10–15 · F5 Ciclo de vida y ML 10–14. La campaña de laboratorio tiene costo externo adicional.

## Presupuesto / modelo de contratación
No especificado en el RFP.

## Criterios de evaluación de la propuesta
No especificados en el RFP.

## Stakeholders identificados
Equipo agronómico (agrónomo, extensionista), técnicos de campo, administradores de plataforma, científico de datos (ML), cliente (AgroIA).

## Entregables esperados
1. Código y migraciones E1–E9 con pruebas automatizadas. 2. Documento de calibración y protocolo de campo. 3. Informe de resultados de la campaña y metas por variable. 4. Pantalla de administración de parámetros y pantalla de salud de sensores. 5. Reporte actualizado con incertidumbre/calidad/evidencia/variables no medidas. 6. Actualización de DOCUMENTACION-PLATAFORMA y del catálogo funcional.

## Supuestos y restricciones generales
- La variante y alimentación del sensor adquirido deben confirmarse en la fase 0 (H-13).
- Las metas de calibración son propuesta de partida y se ajustan con el equipo agronómico.
- La humedad del sensor es VWC con calibración de fábrica limitada (loess/negro/rojo); no validada para arenosos, salinos ni andisoles.

## Glosario
- **JXBS-3001-NPK-RS**: sensor de suelo 7-en-1 (temperatura, humedad VWC, CE, pH, N, P, K) RS485 Modbus.
- **VWC**: contenido volumétrico de agua (%), distinto de humedad relativa o gravimétrica.
- **CE / CEe**: conductividad eléctrica aparente (sensor) vs. del extracto saturado (laboratorio).
- **Bray II**: método de laboratorio para fósforo disponible.
- **K intercambiable**: potasio en cmol(+)/kg (1 cmol(+)/kg ≈ 391 mg/kg).
- **Andisol**: suelo de ceniza volcánica típico del Eje Cafetero.
- **Grado de evidencia (A/B/C/D)**: laboratorio vigente / sensor calibrado / sensor indicativo / SIG o modelo.
- **MAD**: desviación absoluta mediana, estadístico robusto.
- **RS485 / Modbus RTU**: bus industrial y protocolo de comunicación del sensor.

## Resumen cuantitativo de la extracción
- Requerimientos funcionales extraídos: 36
- Requerimientos no funcionales extraídos: 6
- Requisitos técnicos extraídos: 4
- Información de diseño extraída: 2

## Vacíos y riesgos detectados
1. **NPK no equivalente a laboratorio** (H-02): los umbrales Cenicafé/UPRA están en unidades de laboratorio; la conversión requiere calibración local o la variable queda en grado C.
2. **Exactitud de NPK ±40 mg/kg** (H-01/H-07): del mismo orden que los valores reales; hoy las reglas son deterministas.
3. **Sin validación de contexto de medición** (H-04): sonda en aire, suelo seco o sin contacto generan lecturas espurias que pasan el filtro de rango.
4. **Calibración de fábrica limitada** (H-05): no cubre arenosos, salinos ni andisoles cafeteros.
5. **Preguntas abiertas sin resolver** (sección 13): referencia exacta del sensor, laboratorio/métodos de la campaña, unidades de suelo prioritarias, instalación permanente vs. muestreo puntual, profundidad estándar por cultivo.
