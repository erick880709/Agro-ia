# RD-006: Lineamientos de UX — Modo Agricultor y Modo Experto

**Tipo:** Información de diseño
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 5.13, 5.16, 9; contextAgro.md (Visión)

## Descripción
La experiencia de usuario debe diseñarse alrededor de dos perfiles de usuario con necesidades muy diferentes:

### Modo Agricultor (por defecto)
- **Lenguaje:** español coloquial, sin tecnicismos. Las recomendaciones deben leerse como si un agrónomo de confianza estuviera hablando con el agricultor.
- **Visualización:** semáforos de colores (verde = apto, amarillo = atención, rojo = crítico), iconografía clara, barras de progreso simples.
- **Terminología:** evitar palabras como "conductividad eléctrica", "capacidad de intercambio catiónico" sin explicación. Si se usan, acompañar con una definición en lenguaje sencillo.
- **Flujo guiado:** paso a paso para acciones como registrar una finca o interpretar un reporte.
- **Canal principal:** dashboard web responsive + notificaciones WhatsApp.

### Modo Experto (activado por perfil de Técnico Agrónomo/Investigador)
- **Lenguaje:** técnico, con terminología agronómica precisa y unidades de medida.
- **Visualización:** datos crudos, tablas numéricas, gráficos estadísticos, matrices de correlación.
- **Capacidades avanzadas:** comparar fincas, exportar datos (CSV, JSON, Excel), anotar y corregir recomendaciones, ver métricas de modelos (F1-score, RMSE, drift).
- **Propósito:** validación científica de las recomendaciones, calibración de modelos, investigación aplicada.

### Principios transversales
- Toda recomendación debe incluir su justificación en el nivel de lenguaje correspondiente al modo.
- El sistema nunca debe "inventar" — si no hay certeza, debe decir "No hay datos suficientes".
- Si el RAG o el modelo no puede responder con confianza, debe ofrecer contactar a un técnico agrónomo humano.
- La interfaz debe funcionar en zonas rurales con conectividad limitada (carga progresiva, imágenes optimizadas, modo offline para consulta de reportes guardados).

## Elementos de referencia
- No hay wireframes ni mockups adjuntos en el RFP. Deben generarse durante la fase de diseño UX/UI (ver skill `figma-prd-mockups`).
- El diseño visual debe ser profesional pero cálido, transmitiendo confianza al agricultor. Paleta de colores sugerida: verdes tierra, marrones, tonos naturales asociados al agro colombiano.

## Notas del analista
- La dualidad de modos (agricultor vs. experto) es un diferenciador clave. Muchas plataformas agrícolas fallan porque son demasiado técnicas para el agricultor o demasiado simplistas para el agrónomo.
- Se recomienda realizar pruebas de usabilidad con agricultores reales del Quindío durante el piloto, idealmente con acompañamiento del Comité de Cafeteros.
- Para el modo offline, considerar PWA (Progressive Web App) con service workers para cachear reportes y datos de fincas.
