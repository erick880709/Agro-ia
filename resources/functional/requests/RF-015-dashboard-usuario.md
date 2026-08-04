# RF-015: Dashboard de Usuario

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.11; RFP-inicial.md — Sección 3 (Dashboard)
**Prioridad:** Alta

## Descripción
Cada usuario debe contar con un dashboard personalizado que le permita visualizar de forma integrada el estado de sus fincas y cultivos. El dashboard debe incluir:

- **Estado general del terreno:** indicador visual de aptitud por finca (Alta/Media/Baja/No apta según UPRA).
- **Mapa de sus fincas:** visualización geoespacial de las fincas registradas, con capacidad de hacer clic para ver detalle.
- **Historial de mediciones:** serie temporal de las variables de sensor (pH, NPK, humedad, etc.).
- **Alertas:** notificaciones de condiciones críticas (deficiencia severa, riesgo de plaga, sequía pronosticada).
- **Indicadores clave (KPIs):** nivel de fertilidad, salud del suelo, productividad estimada.
- **Gráficos interactivos:** variables de suelo vs. umbrales ideales del cultivo, tendencias.
- **Predicción climática:** pronóstico de los próximos días relevante para la finca.
- **Acceso a reportes:** listado de reportes generados con opción de descargar en PDF.

## Actores involucrados
- Cliente (Agricultor) — visualiza el dashboard de sus fincas
- Técnico Agrónomo — puede ver dashboards de múltiples clientes (según permisos)
- Administrador — visualiza estadísticas agregadas de la plataforma

## Criterios de aceptación
- El dashboard carga en menos de 3 segundos para una finca típica.
- Los gráficos y mapas son interactivos (zoom, filtros por fecha, selección de variables).
- Las alertas se muestran de forma priorizada (críticas primero).
- No especificados en el RFP — definir: ¿personalización del dashboard por usuario?, ¿exportación de gráficos?, ¿comparativa entre fincas del mismo cliente?

## Dependencias / relacionados
- RF-006: Gestión de fincas
- RF-007: Captura de sensores IoT
- RF-013: Recomendaciones inteligentes
- RF-027: Visualización geoespacial
- RT-002: Stack frontend Angular 21

## Notas del analista
- La visualización de datos geoespaciales y series temporales en Angular 21 puede implementarse con bibliotecas como Leaflet (mapas), Chart.js o D3.js (gráficos), y Angular Material para los componentes UI.
- Para el mapa de fincas, considerar que en zonas rurales la conectividad puede ser limitada; se recomienda carga progresiva y caché local de tiles de mapa.
