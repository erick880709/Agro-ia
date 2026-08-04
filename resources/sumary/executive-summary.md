# Resumen Ejecutivo — AgroInteligente Colombia (AgroIA)

**Cliente:** Por definir (proyecto con componente de investigación aplicada — potencial financiación MinCiencias/ColombIA Inteligente)
**Fecha del documento:** Agosto 2026
**Documentos fuente:** 
- `RFP-inicial.md`
- `RFP-AgroInteligente-Colombia.md` (versión consolidada 1.0)
- `contextAgro.md` (PROJECT_CONTEXT)
- `Anexo-Datasets-Fuentes-Datos.md`

## Objetivo y alcance del proyecto

Construir una plataforma inteligente (AgroIA) basada en Inteligencia Artificial, IoT, datos geográficos y meteorológicos que funcione como un **ingeniero agrónomo virtual** para el mercado agrícola colombiano. La plataforma analiza el estado real de un terreno mediante sensores IoT de campo, datos climáticos del IDEAM, información edafológica del IGAC e imágenes satelitales (Copernicus/Sentinel), y determina:

- Si las condiciones del suelo son adecuadas para una excelente cosecha del cultivo evaluado.
- Qué acciones correctivas se requieren cuando el suelo no cumple las condiciones ideales.
- Qué cultivo es el más recomendable para ese terreno específico.
- Recomendaciones de fertilización, manejo de plagas y optimización de recursos.

**Alcance MVP:** portal web responsive, gestión de usuarios con 4 roles, membresías, registro de fincas con geolocalización, ingesta de datos de sensores IoT (18+ variables), integración con APIs externas (IDEAM, IGAC, Copernicus, Google Maps, WhatsApp/SMS), 6 modelos de IA especializados, sistema de recomendaciones inteligentes con justificación, dashboard interactivo, reportes PDF, agente conversacional con arquitectura RAG, panel de administración, y modo experto para técnicos agrónomos.

**Piloto de validación:** cultivos de café en el Quindío (Eje Cafetero), en alianza con el Comité de Cafeteros del Quindío, una IES y una empresa de base tecnológica.

**Stack tecnológico definido por el cliente:**
- **Frontend:** Angular 21
- **Backend y modelos de IA:** Python (FastAPI, scikit-learn, XGBoost, TensorFlow/PyTorch)

## Plazos

No especificados explícitamente en el RFP. Se sugiere proponer un cronograma en 3 fases:
- **Fase 1 (MVP):** 4–6 meses — desarrollo del core, modelos cold-start, portal web, integraciones básicas.
- **Fase 2 (Piloto):** 6 meses — despliegue en Quindío, calibración con datos reales, validación con Comité de Cafeteros.
- **Fase 3 (Operación):** rollout comercial progresivo.

## Presupuesto / modelo de contratación

No especificado en el RFP. El proyecto tiene un componente de investigación aplicada que podría acceder a financiación pública (MinCiencias, programa ColombIA Inteligente). Modelo de ingresos de la plataforma: membresías (mensual, semestral, anual).

## Criterios de evaluación de la propuesta

No especificados formalmente en el RFP. Se infiere que los criterios incluirán: precisión de las recomendaciones agronómicas, cumplimiento del stack tecnológico, experiencia en ML/IoT/AgTech, metodología de desarrollo, capacidad de ejecutar el piloto en Quindío, y viabilidad del modelo de negocio.

## Stakeholders identificados

- **Agricultores** (clientes finales, especialmente pequeños y medianos productores)
- **Comité de Cafeteros del Quindío** (aliado estratégico para el piloto)
- **IES** (Institución de Educación Superior, por definir — aliado investigativo)
- **Empresa de base tecnológica** (aliado para IoT/sensores)
- **Cenicafé** (fuente de conocimiento agronómico para café)
- **MinCiencias / ColombIA Inteligente** (potencial financiador)
- **AGROSAVIA, IDEAM, IGAC, DANE, UPRA** (proveedores de datos abiertos)
- **Administrador de la plataforma** (rol interno)

## Entregables esperados

Según la Sección 11 del RFP consolidado:
1. Código fuente completo.
2. Arquitectura de la solución y diagramas C4 (contexto, contenedores, componentes).
3. Infraestructura como código (IaC — Terraform).
4. API REST documentada (OpenAPI/Swagger).
5. Modelo de datos.
6. Manual técnico y manual de usuario.
7. Casos de prueba y pruebas de seguridad.
8. Despliegue en ambiente productivo.
9. Componente investigativo (si aplica): sistematización de resultados, guías de réplica y publicaciones científicas.

## Supuestos y restricciones generales

**Supuestos del analista:**
- El modelo de 4 roles (Administrador, Cliente, Técnico Agrónomo, Investigador IES) es el válido, basado en el documento consolidado.
- El multi-tenancy se implementará con Row-Level Security en PostgreSQL como primera aproximación.
- El piloto se realizará exclusivamente en café en el Quindío, pero la arquitectura debe ser multi-cultivo y multi-región desde el inicio.
- Los sensores IoT y la infraestructura LoRaWAN serán provistos por el aliado tecnológico; la plataforma solo recibe los datos.
- La pasarela de pagos no se implementa en el MVP (solo se deja preparada la arquitectura).

**Restricciones explícitas del RFP y del cliente:**
- Stack frontend: Angular 21 (vinculante — definido por el cliente).
- Stack backend y modelos: Python (vinculante — definido por el cliente).
- No se permite que el agente IA navegue por Internet.
- El sistema nunca debe inventar información (no alucinación).
- Aislamiento total de datos entre clientes (mandatorio por Ley 1581 de 2012).
- Licencias de datos abiertos: verificar CC-BY-SA 4.0 (IGAC) y CC BY-NC-ND (Cenicafé) para uso comercial.

## Glosario

| Término | Definición |
|---|---|
| **AgroIA / AgroInteligente Colombia** | Nombre de la plataforma |
| **RAG** | Retrieval-Augmented Generation — arquitectura de IA que combina recuperación de documentos con generación de texto |
| **NDVI** | Normalized Difference Vegetation Index — índice de vegetación calculado desde imágenes satelitales |
| **LoRaWAN** | Protocolo de comunicación inalámbrica de largo alcance y bajo consumo para IoT |
| **CIC** | Capacidad de Intercambio Catiónico — propiedad del suelo que indica su capacidad de retener nutrientes |
| **UPRA** | Unidad de Planificación Rural Agropecuaria (Colombia) |
| **IGAC** | Instituto Geográfico Agustín Codazzi |
| **IDEAM** | Instituto de Hidrología, Meteorología y Estudios Ambientales |
| **Cenicafé** | Centro Nacional de Investigaciones de Café (Colombia) |
| **AGROSAVIA** | Corporación Colombiana de Investigación Agropecuaria |
| **SIPSA** | Sistema de Información de Precios y Abastecimiento del Sector Agropecuario (DANE) |
| **EVA** | Evaluaciones Agropecuarias Municipales (DANE) |
| **IES** | Institución de Educación Superior |
| **MLOps** | Machine Learning Operations — prácticas DevOps aplicadas a modelos de ML |
| **RBAC** | Role-Based Access Control — control de acceso basado en roles |
| **SLA** | Service Level Agreement — acuerdo de nivel de servicio |
| **Habeas Data** | Ley 1581 de 2012 — protección de datos personales en Colombia |
| **FAIR** | Findable, Accessible, Interoperable, Reusable — principios para publicación de datasets científicos |

## Resumen cuantitativo de la extracción

- **Requerimientos funcionales extraídos:** 22 (RF-001 a RF-022)
- **Requerimientos no funcionales extraídos:** 10 (RNF-001 a RNF-010)
- **Requisitos técnicos extraídos:** 15 (RT-001 a RT-015)
- **Información de diseño extraída:** 7 (RD-001 a RD-007)
- **Total de artefactos generados:** 54 archivos Markdown + 1 resumen ejecutivo

## Vacíos y riesgos detectados

1. **Modelo LLM concreto no definido:** el RFP no especifica qué modelo de lenguaje usar para el agente conversacional (GPT-4, Claude, Llama 3, Mistral). Esto tiene implicaciones de costo, latencia, privacidad de datos y calidad de respuestas en español. Si se usa un modelo comercial (API), debe garantizarse que los datos de agricultores no se expongan. Si es open-source autoalojado, se requiere infraestructura GPU.

2. **Hardware y proveedor de sensores IoT no especificado:** el RFP describe las variables a medir y sugiere LoRaWAN, pero no define fabricantes, modelos ni proveedores de sensores. Esto debe resolverse con el aliado tecnológico antes del piloto.

3. **Estrategia de conectividad rural no definida:** para zonas sin cobertura celular donde LoRaWAN no tenga gateway cercano, no se ha definido alternativa (NB-IoT, satelital). Es crítico para la adopción en zonas rurales profundas.

4. **Licencia de Cenicafé pendiente de validación comercial:** la biblioteca técnica de Cenicafé (corpus principal del RAG para café) está bajo CC BY-NC-ND (no comercial, sin obras derivadas). Dado que la plataforma se comercializará por membresías, se requiere validación formal con Cenicafé/FNC.

5. **Modelo de costos de infraestructura no estimado:** el RFP no establece un presupuesto para la operación cloud (AWS). Los costos de inferencia de IA (LLM + 6 modelos ML), almacenamiento de datos IoT y procesamiento de imágenes satelitales pueden ser significativos a escala.

6. **Gobernanza de datos del agricultor no definida:** aunque se menciona la Ley 1581 de 2012, el RFP no detalla: ¿a quién pertenecen los datos capturados por los sensores?, ¿puede el agricultor descargar/eliminar sus datos?, ¿se usarán datos agregados para mejorar los modelos sin consentimiento explícito? Esto es particularmente sensible si se publican datasets bajo principios FAIR.
