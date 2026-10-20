# RF-039: Selector de voz femenina o masculina

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-002 — Secciones 3, 4.1 y 7 (RF-02)
**Prioridad:** Mandatoria (M)

## Descripción
El usuario debe poder elegir entre una voz femenina y una voz masculina en español para la lectura de respuestas.

## Actores involucrados
- Productor / agricultor
- Técnico / extensionista

## Criterios de aceptación
- Se ofrece un selector con voz femenina y masculina en español.
- La voz elegida se usa en la lectura de respuestas.

## Dependencias / relacionados
- RF-040: Botón "Escuchar muestra"
- RT-020: Interfaz común de síntesis
- RT-021: Cadena de respaldo de motores

## Notas del analista
La Web Speech API no expone el género de forma estándar; el RFP prevé una lista curada de voces por plataforma (sección 9.3). La garantía de género explícito depende del motor en la nube seleccionado (B o C).
