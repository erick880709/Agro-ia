# RD-001: Diagrama de Contexto C4 — Actores y Sistemas Externos

**Tipo:** Información de diseño
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 4 (Actores del sistema)

## Descripción
El RFP define un diagrama de contexto (nivel C4 — Context) con los siguientes actores humanos y sistemas externos que interactúan con la plataforma AgroInteligente Colombia.

### Actores humanos

| Actor | Rol |
|---|---|
| **Agricultor** | Consulta alertas y recomendaciones sobre sus fincas y cultivos. Es el usuario final principal. |
| **Técnico Agrónomo** | Analiza los modelos y valida las predicciones/recomendaciones generadas por la IA. Actúa como revisor de calidad. |
| **Investigador IES** | Administra modelos y experimentos de Machine Learning. Soporta el componente de investigación aplicada (posible financiación MinCiencias/ColombIA Inteligente). |
| **Administrador** | Monitorea la infraestructura, usuarios, membresías y configuración general de la plataforma. |

### Sistemas externos

| Sistema | Función | Dependencia |
|---|---|---|
| **Sensores IoT** | Proveen datos de campo (pH, NPK, humedad, temperatura del suelo, etc.) | Crítica — sin sensores no hay datos de suelo |
| **IDEAM** | Datos climáticos (pronóstico, lluvias, temperatura, humedad ambiental, viento, radiación solar) | Alta — complementa los datos de suelo |
| **IGAC** | Datos edafológicos (información de suelos a nivel nacional) | Media — enriquece el análisis con mapas de suelos oficiales |
| **Copernicus / Sentinel / Landsat** | Imágenes satelitales e índices de vegetación (NDVI) | Media — monitoreo remoto del cultivo |
| **WhatsApp / SMS** | Canal de notificaciones y alertas al agricultor | Media — comunicación con el agricultor |
| **Google Maps / Proveedor GIS** | Geolocalización, latitud, longitud, altitud | Alta — registro y ubicación de fincas |

## Elementos de referencia
- El diagrama de contexto C4 debe ser generado formalmente durante la fase de arquitectura (ver skill `archi`), incluyendo los flujos de datos entre sistemas.
- La dirección de las flechas en el diagrama debe indicar quién inicia la interacción y en qué dirección fluye la información.
- Se recomienda usar notación C4-PlantUML o Structurizr DSL para mantener el diagrama como código.

## Notas del analista
- La dependencia de los sensores IoT es crítica: sin ellos, el sistema se degrada a recomendaciones basadas únicamente en datos externos (clima, satélites), que son menos precisas.
- La integración con múltiples sistemas externos (IDEAM, IGAC, Copernicus, GIS) implica que la plataforma debe manejar graceful degradation cuando alguno de estos servicios no está disponible.
- La IES (Institución de Educación Superior) aliada aún no está identificada por nombre en el RFP. Es un stakeholder clave para el componente investigativo.
