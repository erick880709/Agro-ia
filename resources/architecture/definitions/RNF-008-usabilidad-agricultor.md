# RNF-008: Experiencia de Usuario — Sencillez para el Agricultor

**Tipo:** Requerimiento no funcional
**Categoría:** Usabilidad
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.16

## Descripción
La plataforma debe ser utilizable por agricultores sin conocimientos técnicos, asegurando:

- **Lenguaje natural y sencillo:** todas las recomendaciones, alertas y mensajes del sistema deben expresarse en español, en lenguaje coloquial que un agricultor promedio pueda entender sin formación técnica previa. Evitar terminología científica sin explicación.
- **Interfaz intuitiva:** navegación simple, pocos pasos para llegar a la información relevante, iconografía clara y universal.
- **Toda recomendación explicada:** el sistema debe explicar el "por qué" de cada recomendación en términos comprensibles.
- **Flujo guiado:** para acciones complejas (registro de finca, configuración de sensores), la interfaz debe guiar al usuario paso a paso.

## Criterio medible / restricción concreta
- No especificados en el RFP — definir: pruebas de usabilidad con agricultores reales del piloto, métricas como tiempo para completar tareas clave, tasa de error en uso, satisfacción (SUS — System Usability Scale).

## Impacto en la arquitectura
- Diseño UX centrado en el usuario (UCD) con validación temprana en campo.
- Dos modos de interfaz: simplificado (agricultor) y experto (técnico/agrónomo).
- Contenido de ayuda contextual y tooltips en la interfaz.
- Soporte para carga lenta de páginas (zonas rurales con conectividad limitada).

## Notas del analista
- Este requisito es fundamental para la adopción. En el contexto de agricultores colombianos, muchos de los cuales pueden tener bajo nivel de alfabetización digital, la usabilidad es tan importante como la precisión de los modelos de IA.
- Se recomienda realizar pruebas de usabilidad con agricultores reales del Quindío durante el piloto, idealmente con acompañamiento del Comité de Cafeteros.
- Considerar soporte offline o Progressive Web App (PWA) para zonas sin conectividad constante, aunque no está explícitamente solicitado en el RFP.
