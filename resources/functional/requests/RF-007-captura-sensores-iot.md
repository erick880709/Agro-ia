# RF-007: Captura de Información de Sensores IoT

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.5; RFP-inicial.md — Sección 3 (Captura de información)
**Prioridad:** Alta

## Descripción
El sistema debe recibir, almacenar y procesar información proveniente de sensores IoT instalados en campo. Las variables mínimas que deben capturarse desde los sensores incluyen:

**Macronutrientes y propiedades físicas:**
- Humedad del suelo
- Temperatura del suelo / ambiental
- pH
- Nitrógeno (N), Fósforo (P), Potasio (K)
- Conductividad eléctrica
- Materia orgánica
- Capacidad de intercambio catiónico (CIC)

**Nutrientes secundarios y micronutrientes:**
- Calcio (Ca), Magnesio (Mg), Azufre (S)
- Sodio (Na)
- Hierro (Fe), Zinc (Zn), Cobre (Cu), Manganeso (Mn), Boro (B)

**Otros indicadores:**
- Salinidad

La arquitectura debe ser extensible para permitir la incorporación de nuevos tipos de sensores y variables en el futuro sin requerir un rediseño mayor de la plataforma.

## Actores involucrados
- Sensores IoT (sistema externo)
- Administrador (configura y monitorea los sensores)
- Cliente (visualiza los datos capturados en su dashboard)

## Criterios de aceptación
- Los datos de sensores se reciben y almacenan correctamente con marca de tiempo.
- La frecuencia de captura es configurable (referencia: cada 15–30 minutos).
- El sistema soporta la adición de nuevas variables de sensor sin cambios en el esquema de datos ni en el pipeline de ingesta.
- No especificados en el RFP — definir: formato del payload de los sensores, mecanismo de autenticación de dispositivos IoT, tolerancia a datos faltantes o erróneos.

## Dependencias / relacionados
- RT-009: Arquitectura IoT — LoRaWAN
- RT-011: Mensajería/streaming para IoT
- RF-012: Motor predictivo (consume estos datos)

## Notas del analista
- El RFP referencia el protocolo LoRaWAN como adecuado para zonas rurales con baja conectividad, y autonomía energética >12 meses mediante paneles solares. Esto implica que el backend debe soportar ingesta de datos potencialmente intermitente (offline/disconnected scenarios).
- No se especifica el fabricante ni modelo de sensores. Se recomienda diseñar una capa de abstracción (adaptador) que normalice los datos independientemente del hardware específico.
- Las variables listadas en el RFP consolidado (Sección 5.5) son más extensas que las del RFP inicial (que solo listaba 10 variables). Se toma como referencia la lista ampliada del documento consolidado.
