# RFP — AgroInteligente Colombia
## Plataforma de Agricultura de Precisión basada en IA, IoT y Analítica Climática para el Diagnóstico y Optimización de Cultivos

**Versión:** 1.0 — Documento consolidado
**Fecha:** Agosto 2026

---

## 1. Introducción

### 1.1 Nombre del proyecto

**AgroInteligente Colombia** (también referido como *AgroIA*) — Plataforma Inteligente para Diagnóstico y Optimización de Cultivos.

### 1.2 Objetivo del proyecto

Construir una plataforma inteligente, basada en Inteligencia Artificial, IoT y datos geográficos/meteorológicos, que analice el estado real de un terreno agrícola y determine **si las condiciones del suelo son adecuadas para obtener una excelente cosecha**. Cuando el terreno no cumpla las condiciones ideales, la plataforma debe generar **recomendaciones accionables y justificadas** para corregir las deficiencias antes o durante la siembra.

En síntesis, la IA debe comportarse como un **ingeniero agrónomo virtual / "Agrónomo Digital"**, capaz de responder:

- ¿Este suelo está apto para sembrar el cultivo previsto?
- Si no lo está, ¿qué se debe corregir y cómo?
- ¿Qué cultivo es el más recomendable para este terreno?
- ¿Qué fertilizantes, nutrientes y cantidades hacen falta?
- ¿Qué problemas presenta el suelo (deficiencias, excesos, riesgos)?
- ¿Cómo maximizar la productividad y reducir costos e impacto ambiental?

### 1.3 Mercado objetivo

La plataforma estará dirigida inicialmente al mercado agrícola colombiano, con un piloto de validación científica en cultivos de café en la región del Quindío (Eje Cafetero), en alianza con el Comité de Cafeteros del Quindío, una IES y una empresa de base tecnológica.

---

## 2. Contexto y justificación del problema

- Los agricultores generalmente conocen muy poco sobre el estado real de su suelo y toman decisiones de fertilización de forma **empírica**, no basada en datos.
- Esto genera: desperdicio de fertilizantes, baja productividad, enfermedades, baja rentabilidad y contaminación ambiental.
- En Colombia coexisten modelos de agricultura tecnificada con una base mayoritaria (+70%) de pequeños y medianos productores con alta vulnerabilidad técnica y económica.
- Las pérdidas postcosecha y durante el ciclo productivo pueden alcanzar hasta el **40%** en ciertos cultivos (Ministerio de Agricultura / DANE).
- Existen fuentes de datos oficiales (IDEAM para clima, IGAC para datos edáficos, imágenes satelitales tipo Sentinel/Copernicus) pero **operan de manera desarticulada**: no hay una plataforma unificada que las combine con sensores IoT de campo para generar inteligencia accionable.
- Brechas identificadas:
  - **Brecha de monitoreo**: sensores IoT aislados y no escalables.
  - **Brecha de integración de datos**: IDEAM, IGAC e imágenes satelitales sin articular.
  - **Brecha de automatización analítica**: los datos no se transforman en conocimiento predictivo/prescriptivo.
  - **Brecha de sostenibilidad**: uso ineficiente de insumos (agua, fertilizantes), con sobrecostos de hasta 30% y externalidades ambientales (salinización de suelos, contaminación hídrica).

---

## 3. Objetivos del negocio

- Determinar de forma automática si un terreno es apto para un cultivo específico, y en caso contrario, indicar cómo corregirlo.
- Incrementar la productividad de los cultivos y el rendimiento por hectárea.
- Reducir pérdidas por malas decisiones de siembra y fertilización.
- Optimizar el uso de fertilizantes, agua y demás insumos.
- Generar recomendaciones agronómicas personalizadas, explicables y basadas en evidencia.
- Reducir el impacto ambiental de la actividad agrícola.
- Comercializar el servicio mediante un modelo de membresías.
- Servir como base de un proyecto de investigación aplicada (piloto validado en campo, con potencial de financiación pública/ColombIA Inteligente y publicaciones científicas).

---

## 4. Actores del sistema (según diagrama de contexto C4 provisto)

| Actor | Rol |
|---|---|
| **Agricultor** | Consulta alertas y recomendaciones sobre sus fincas y cultivos. |
| **Técnico Agrónomo** | Analiza los modelos y valida las predicciones/recomendaciones generadas por la IA. |
| **Investigador IES** | Administra modelos y experimentos de Machine Learning; soporta el componente de investigación. |
| **Administrador** | Monitorea la infraestructura, usuarios, membresías y configuración general de la plataforma. |

**Sistemas externos con los que interactúa la plataforma:**

- **Sensores IoT** (de campo) — de los cuales la plataforma *depende* para obtener las variables de medición del terreno.
- **IDEAM** — datos climáticos (pronóstico, lluvias, temperatura, humedad ambiental, viento, radiación solar).
- **IGAC** — datos edafológicos (información de suelos a nivel nacional).
- **Copernicus / Sentinel / Landsat** — imágenes satelitales e índices de vegetación (NDVI).
- **WhatsApp / SMS** — canal de notificaciones y alertas al agricultor.
- **Google Maps / proveedor GIS** — geolocalización, latitud, longitud, altitud.

---

## 5. Alcance del MVP

### 5.1 Portal Web

- Sitio responsive, compatible con Desktop, Tablet y Celulares.
- Compatible con los navegadores: Chrome, Safari, Edge, Firefox.

### 5.2 Gestión de usuarios

- Registro, inicio de sesión, recuperación y cambio de contraseña, perfil de usuario.
- Roles: **Administrador** y **Cliente** (y, según el modelo de actores ampliado, Técnico Agrónomo e Investigador IES).
- Aislamiento estricto de datos: cada cliente únicamente visualiza información de sus propias fincas; nunca puede ver información de otros clientes.

### 5.3 Gestión de membresías

- Tipos de membresía: Mensual, Semestral, Anual.
- Cada membresía define: número máximo de fincas, número máximo de análisis, acceso al agente IA, historial de reportes.
- Integración futura con pasarela de pagos (dejar preparada la arquitectura en el MVP).

### 5.4 Gestión de fincas

Cada cliente puede registrar una finca con: nombre, departamento, municipio, área, tipo de cultivo, ubicación GPS (latitud/longitud), fotografía.

### 5.5 Captura de información (sensores IoT)

Variables mínimas a recibir desde sensores:

- Humedad del suelo
- Temperatura del suelo / ambiental
- pH
- Nitrógeno (N), Fósforo (P), Potasio (K)
- Calcio, Magnesio, Azufre
- Sodio
- Conductividad eléctrica
- Micronutrientes: Hierro, Zinc, Cobre, Manganeso, Boro
- Capacidad de intercambio catiónico
- Salinidad
- Materia orgánica

La arquitectura debe permitir **agregar nuevos sensores en el futuro** sin rediseño mayor. Frecuencia de captura configurable (referencia: cada 30 minutos; redes LoRaWAN con autonomía energética superior a 12 meses mediante paneles solares para zonas rurales de baja conectividad).

### 5.6 Variables adicionales de entrada

**Ubicación:** latitud, longitud, altitud, departamento, municipio, país, tipo de terreno, pendiente, orientación solar.

**Variables ambientales (IDEAM):** temperatura ambiente, humedad relativa, radiación solar, velocidad del viento, precipitación, evapotranspiración, presión atmosférica, índice UV. Históricos de al menos 5 años.

**Variables históricas de la finca:** últimos cultivos, fecha de siembra, fecha de cosecha, producción, fertilizaciones aplicadas, plaguicidas, riego, enfermedades y plagas registradas.

**Variables económicas:** precio del cultivo, costo de fertilizantes, costo de transporte, costo de mano de obra, rentabilidad estimada, demanda del mercado.

**Imágenes satelitales:** resolución temporal de referencia cada 5 días (NDVI / índice de vegetación).

### 5.7 Catálogo de cultivos

Ficha técnica por cultivo, con: nombre, nombre científico, familia, temperatura ideal, humedad ideal, pH ideal, requerimientos de N-P-K y calcio, altitud recomendada, tipo de suelo, tiempo de cosecha, enfermedades y plagas frecuentes, producción esperada, mercados objetivo, rentabilidad.

### 5.8 Motor de conocimiento agronómico

La plataforma debe modelar: relación e interacción entre nutrientes, bloqueo de nutrientes, compatibilidad entre fertilizantes, compatibilidad y rotación/asociación de cultivos, enfermedades, plagas, hongos, malezas y buenas prácticas agrícolas.

### 5.9 Motor predictivo / Modelos de IA

La plataforma debe ejecutar modelos especializados:

1. **Clasificación del estado del suelo** → salida: Excelente / Bueno / Regular / Malo / Crítico.
2. **Predicción del cultivo ideal** → entrada: variables de suelo, clima y geografía; salida: top 5 cultivos recomendados con score y nivel de confianza.
3. **Detección de deficiencias nutricionales** → entrada: sensores; salida: lista de nutrientes faltantes, cantidad requerida y prioridad.
4. **Recomendación de fertilización** → salida: tipo de fertilizante, cantidad, frecuencia, costo estimado.
5. **Predicción de rendimiento** → salida: toneladas por hectárea, intervalo de confianza, factores limitantes.
6. **Predicción de enfermedades/plagas** → entrada: clima, humedad, cultivo; salida: nivel de riesgo y recomendaciones.

**Técnicas y validación:** Random Forest, XGBoost y LSTM (para series temporales climáticas); validación cruzada (cross-validation); métricas RMSE (regresión) y F1-score (clasificación); manejo explícito de overfitting y monitoreo de drift del modelo en producción.

**Sistema híbrido de recomendación:** reglas agronómicas basadas en umbrales (sistema experto) + modelos de Machine Learning, de forma que la plataforma nunca dependa únicamente de reglas simples y razone considerando múltiples variables simultáneamente.

### 5.10 Recomendaciones inteligentes — condición de aptitud del suelo

Este es el núcleo del negocio: dado un conjunto de mediciones de sensores para un terreno y un cultivo objetivo (o el motor sugiriendo el cultivo más apto), el sistema debe:

- Determinar si el suelo **cumple** las condiciones ideales para una excelente cosecha del cultivo evaluado.
- Si **no cumple**, identificar cada variable fuera de rango (ej. pH, nutriente, humedad) y su severidad/prioridad.
- Generar una **recomendación correctiva específica** por cada desviación (ej. "El terreno requiere incrementar el nivel de Potasio", "No se recomienda sembrar café debido al nivel de acidez").
- Toda recomendación debe estar **justificada**, indicando: variables que influyeron, nivel de confianza, riesgos, beneficios, costo estimado e impacto esperado.
- El sistema nunca debe inventar información (no alucinar); si no hay evidencia suficiente, debe indicarlo explícitamente.

### 5.11 Dashboard

Cada usuario visualiza: estado general del terreno, mapa de sus fincas, historial, alertas, indicadores, gráficos, reportes, nivel de fertilidad, predicción climática e historial de mediciones.

### 5.12 Reportes

Generación de reportes en PDF con: estado del suelo, resumen ejecutivo, variables medidas, gráficas, recomendaciones, cultivos sugeridos y plan de acción.

### 5.13 Agente conversacional (asistente IA)

- Entrenado únicamente sobre agronomía, agricultura, fertilizantes, buenas prácticas agrícolas, manuales especializados y la base documental del proyecto (arquitectura **RAG**).
- No navega libremente por Internet; responde solo con: información del reporte generado, datos históricos del cliente y la base de conocimiento agrícola.
- Capacidades: interpretar sensores, mapas e imágenes satelitales; explicar conceptos agrícolas en lenguaje sencillo o técnico (modo experto para agrónomos); generar y priorizar recomendaciones; mostrar nivel de confianza; explicar el porqué de cada recomendación; nunca inventar información.
- Ejemplos de preguntas que debe responder: "¿Qué puedo sembrar aquí?", "¿Por qué mi suelo tiene bajo rendimiento?", "¿Qué fertilizante debo aplicar y cuánto?", "¿Cuándo debo sembrar/cosechar/regar?", "¿Qué significa tener un pH de 5.2?", "¿Qué debo hacer primero?".

### 5.14 Integración con APIs externas

- **IDEAM**: pronóstico y datos climáticos históricos.
- **IGAC**: datos edafológicos.
- **Copernicus/Sentinel/Landsat**: imágenes satelitales, NDVI.
- **Google Maps / GIS**: latitud, longitud, altitud, geolocalización.
- **WhatsApp/SMS**: envío de alertas y notificaciones.

### 5.15 Administración

El administrador debe poder: administrar usuarios, membresías, cultivos, reglas agronómicas, sensores y modelos de IA; visualizar estadísticas generales de la plataforma.

### 5.16 Experiencia de usuario

- La aplicación debe ser sencilla; el agricultor no requiere conocimientos técnicos.
- Toda recomendación debe explicarse en lenguaje natural.
- Debe existir un **modo experto** para ingenieros agrónomos y técnicos.

---

## 6. Requerimientos no funcionales

### 6.1 Rendimiento

- Tiempo de respuesta menor a 3 segundos para consultas normales.
- Respuesta del chat IA menor a 10 segundos.
- Disponibilidad objetivo del 99.9%.

### 6.2 Escalabilidad

- Arquitectura cloud-native, escalable horizontalmente.
- Preparada para soportar miles de usuarios concurrentes.
- Escalado automático de los servicios de inferencia en función de la carga.

### 6.3 Seguridad

- Autenticación y autorización (JWT, OAuth2).
- Comunicación cifrada mediante HTTPS/TLS.
- Cifrado de información sensible en reposo.
- Redes privadas virtuales (VPC) para aislar componentes críticos.
- Gestión segura de credenciales y secretos.
- Cumplimiento de OWASP Top 10.
- Aislamiento total de datos entre clientes: cada cliente solo accede a sus propios análisis, reportes, fincas y conversaciones con el agente IA.
- Registro y auditoría de accesos y operaciones relevantes.

### 6.4 Observabilidad

- Logs centralizados, métricas de rendimiento técnico (latencia, throughput, uso de recursos) y métricas del modelo (precisión, tasa de falsos positivos, detección de drift).
- Trazabilidad y monitoreo continuo, con alertas.

### 6.5 Portabilidad y mantenibilidad

- Contenedores Docker para empaquetar cada componente/microservicio.
- Orquestación con Kubernetes: escalado automático, alta disponibilidad mediante réplicas, despliegues controlados (rolling updates), aislamiento de recursos y políticas de CPU/memoria.
- Prácticas de CI/CD y MLOps para operación continua.

---

## 7. Arquitectura de referencia recomendada

### 7.1 Enfoque general

Arquitectura **cloud-native**, basada en **microservicios** y **orientada a eventos**, organizada en capas:

1. **Capa de ingesta de datos** — recepción de datos de sensores (humedad del suelo, pH, NPK, clima).
2. **Capa de servicios de inferencia** — ejecución de los modelos de IA sobre las variables recibidas.
3. **Capa de gestión y monitorización** — control del rendimiento del sistema y de los modelos.
4. **Capa de persistencia** — almacenamiento de resultados, métricas y logs.
5. **Capa de seguridad y gobierno** — transversal a toda la plataforma.

### 7.2 Stack tecnológico propuesto

- **Frontend:** React o Next.js (responsive).
- **Backend:** microservicios en .NET 8 (o frameworks de API como FastAPI/Flask para exponer los modelos como servicio REST).
- **API Gateway** para exposición segura de servicios.
- **Base de datos transaccional:** PostgreSQL.
- **Base de datos geoespacial:** PostgreSQL + PostGIS.
- **Motor de IA predictiva:** modelos de ML entrenados con datos agronómicos y climáticos (Random Forest, XGBoost, LSTM).
- **Agente conversacional:** arquitectura RAG con LLM + base de datos vectorial sobre bibliografía y manuales agrícolas, sin acceso libre a Internet.
- **Almacenamiento de objetos:** para datasets, modelos entrenados, reportes y base documental.
- **Mensajería/streaming:** para la ingesta desacoplada de datos de sensores IoT (colas de mensajes).
- **Contenedores y orquestación:** Docker + Kubernetes.
- **Nube:** AWS (EC2, S3, EKS, SageMaker, IoT Core) — elegida por elasticidad, alta disponibilidad y modelo de pago por uso; Azure/GCP son alternativas viables.
- **Observabilidad:** stack centralizado de logs, métricas y trazas.

### 7.3 MLOps — ciclo de vida del modelo

- **Registro y versionado:** cada versión del modelo se almacena en un repositorio de modelos junto con metadatos y métricas.
- **Despliegue:** integración del modelo en el servicio de inferencia vía contenedores, sin interrumpir el servicio.
- **Monitorización:** métricas técnicas (latencia, throughput, recursos) y métricas de modelo (precisión, falsos positivos, drift).
- **Reentrenamiento:** posibilidad de reentrenar ante degradación de desempeño, con automatización parcial del pipeline en entornos controlados.

### 7.4 Redes de sensores IoT

- Protocolo de referencia: **LoRaWAN**, adecuado para zonas rurales con conectividad limitada.
- Transmisión de datos de referencia: cada 15–30 minutos.
- Autonomía energética mediante paneles solares (>12 meses).
- Arquitectura preparada para incorporar nuevos tipos de sensores sin rediseño mayor.

---

## 8. Fuentes de conocimiento IA (RAG) y estrategia de datos

La base de conocimiento del agente debe alimentarse de:

- Libros y manuales de agronomía.
- Investigaciones y publicaciones científicas (ej. estudios de Cenicafé sobre variables agronómicas del café: humedad de suelo óptima 60–80% de capacidad de campo, pH ideal 5.5–6.5).
- Normativas y buenas prácticas agrícolas.
- Fichas técnicas de cultivos.
- Documentación técnica del proyecto.

El conocimiento debe poder **actualizarse sin reentrenar el modelo** (mediante actualización del índice vectorial del RAG).

### 8.1 Fuentes de datos identificadas y estrategia de cold-start (ambigüedad resuelta)

Se identificaron fuentes concretas, abiertas y oficiales, que resuelven dos de los vacíos críticos señalados originalmente en este RFP — el detalle completo está en el **Anexo — Fuentes de Datos y Datasets para Entrenamiento de Modelos**:

- **Umbrales agronómicos por cultivo:** la **UPRA** (Unidad de Planificación Rural Agropecuaria) ya cuenta con una metodología oficial colombiana de evaluación de tierras que clasifica la aptitud en **Alta / Media / Baja / No apta**, con zonificaciones ya publicadas para varios cultivos (café incluido). Se recomienda adoptar esta clasificación como estándar del Modelo 1, en vez de una escala propia sin respaldo institucional. Para café específicamente, **Cenicafé** es la fuente primaria (biblioteca técnica de libre consulta).
- **Cold start del dataset de IA:** el sistema no debe esperar a acumular datos propios del piloto para lanzar el MVP. La estrategia recomendada combina, desde el día 1, reglas agronómicas de fuentes oficiales (UPRA, Cenicafé, FAO/IIASA GAEZ) con datasets públicos internacionales (Kaggle Crop Recommendation, SoilGrids de ISRIC) para un primer modelo de ML, que luego se calibra y reentrena con datos reales conforme avanza el piloto de campo (AGROSAVIA, IDEAM, sensores propios).
- Otras fuentes colombianas con **API o datos abiertos ya disponibles**: IDEAM (clima, vía API Socrata/SODA), IGAC (edafología, shapefiles CC-BY-SA), DANE-SIPSA/EVA (precios y rendimientos históricos por cultivo/municipio).

Estas fuentes deben tenerse en cuenta al dimensionar el esfuerzo de la Fase 2/3 de la metodología (procesamiento y modelado IA) y al definir los conectores de ingesta de datos externos del backend.

---

## 9. Principios de las recomendaciones

- Toda recomendación debe estar **justificada** y basada en evidencia.
- Debe indicar: nivel de confianza, variables que influyeron, riesgos, beneficios, costo estimado e impacto esperado.
- El sistema nunca debe inventar información.

---

## 10. Funcionalidades futuras (fuera del MVP)

- Predicción mediante imágenes de drones y fotografías del cultivo.
- Integración de sensores IoT en tiempo real a mayor escala.
- Alertas automáticas de sequías e inundaciones.
- Detección de plagas mediante visión artificial.
- Optimización automática del riego.
- Simulación de escenarios agrícolas.
- Recomendaciones financieras para el productor.
- Integración completa con pasarela de pagos para membresías.

---

## 11. Entregables esperados

- Código fuente.
- Arquitectura de la solución y diagramas C4 (contexto, contenedores, componentes).
- Infraestructura como código.
- API REST documentada.
- Modelo de datos.
- Manual técnico y manual de usuario.
- Casos de prueba y pruebas de seguridad.
- Despliegue en ambiente productivo.
- (Componente investigativo, si aplica) Sistematización de resultados, guías de réplica y publicaciones científicas.

---

## 12. Criterios de éxito

- Diagnóstico agronómico preciso, explicable y basado en datos reales del terreno.
- Determinación correcta de aptitud/no aptitud del suelo frente al cultivo evaluado, con recomendaciones correctivas accionables cuando no se cumplan las condiciones.
- Recomendaciones fundamentadas en variables de suelo y clima, con nivel de confianza declarado.
- Aislamiento completo de la información entre clientes.
- Comercialización viable mediante membresías.
- Plataforma preparada para incorporar nuevos cultivos, sensores y modelos predictivos sin rediseños mayores.
- (Componente piloto) Reducción medible de pérdidas productivas y de consumo de insumos (agua, fertilizantes) en la parcela piloto frente al manejo tradicional; adopción tecnológica medida mediante uso y satisfacción de los agricultores participantes.

---

## 13. Preguntas abiertas / a definir con el proveedor

- Proveedor cloud definitivo (AWS confirmado como preferido; validar Azure/GCP como alternativa según el ecosistema del proveedor).
- Modelo específico de LLM a utilizar para el agente conversacional (comercial vs. open-source autoalojado, dado el requisito de no exponer datos sensibles a Internet).
- Estrategia de conectividad para sensores en zonas rurales sin cobertura celular (LoRaWAN vs. NB-IoT vs. satelital).
- Pasarela de pagos a integrar para el módulo de membresías.
- Alcance exacto del piloto de campo (número de fincas, cultivos, duración) para la fase de validación.
- Condiciones de uso comercial de la biblioteca técnica de Cenicafé en el RAG (ver Anexo de Datasets, sección 9) — a validar formalmente con Cenicafé/FNC dado el modelo de membresías.
- Multi-tenancy a nivel de base de datos: mecanismo concreto para el aislamiento entre clientes (row-level security vs. esquema por cliente).
- Gobernanza y propiedad de los datos capturados por los sensores del agricultor (aplicación de la Ley 1581 de 2012 de habeas data), especialmente relevante si se publican datasets bajo principios FAIR como plantea el componente investigativo.

> Nota: los vacíos sobre **umbrales agronómicos por cultivo** y **estrategia de cold-start del dataset de IA**, identificados inicialmente en este RFP, ya cuentan con una propuesta de solución concreta — ver el **Anexo — Fuentes de Datos y Datasets para Entrenamiento de Modelos**.
