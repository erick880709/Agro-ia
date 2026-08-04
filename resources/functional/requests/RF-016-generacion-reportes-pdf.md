# RF-016: Generación de Reportes en PDF

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.12; RFP-inicial.md — Sección 3 (Reportes)
**Prioridad:** Media

## Descripción
El sistema debe generar reportes en formato PDF descargables para cada análisis realizado sobre una finca. Cada reporte debe contener:

- **Estado del suelo:** clasificación de aptitud según UPRA (Alta/Media/Baja/No apta).
- **Resumen ejecutivo:** conclusión principal en lenguaje sencillo para el agricultor.
- **Variables medidas:** tabla con los valores actuales de cada variable de sensor vs. los valores ideales para el cultivo.
- **Gráficas:** visualizaciones de las variables más relevantes (pH, NPK, humedad) comparadas contra los umbrales ideales.
- **Recomendaciones:** listado priorizado de acciones correctivas, cada una con justificación, nivel de confianza, costo estimado e impacto esperado.
- **Cultivos sugeridos:** top 5 cultivos alternativos recomendados si el cultivo actual no es el óptimo.
- **Plan de acción:** cronograma sugerido de intervenciones (fertilización, enmiendas, riego, próximas mediciones).

## Actores involucrados
- Cliente (Agricultor) — solicita y descarga reportes de sus fincas
- Técnico Agrónomo — puede generar reportes para los clientes que asesora

## Criterios de aceptación
- El reporte se genera en menos de 10 segundos para una finca con datos típicos.
- El PDF es autocontenido (no requiere conexión a Internet para visualizarse).
- El diseño del PDF es profesional e incluye el logo de la plataforma.
- Los reportes quedan almacenados en el historial del cliente y pueden re-descargarse.
- No especificados en el RFP — definir: ¿plantillas de reporte personalizables?, ¿marca blanca para empresas?, ¿firma digital o código QR de validación?

## Dependencias / relacionados
- RF-006: Gestión de fincas
- RF-013: Recomendaciones inteligentes
- RF-015: Dashboard de usuario
- RT-003: Backend Python (generación de PDF con ReportLab/WeasyPrint)

## Notas del analista
- La generación de PDFs en el backend Python puede usar bibliotecas como ReportLab, WeasyPrint o pdfkit. WeasyPrint permite diseñar con HTML/CSS, lo que facilita plantillas profesionales.
- El almacenamiento de reportes generados debe considerar el crecimiento en el tiempo. Se recomienda usar almacenamiento de objetos (S3) con una referencia en la base de datos.
