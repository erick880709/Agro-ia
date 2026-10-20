---
id: TT-02
type: Tarea Técnica
epic: 011
priority: Alta
points: 8
---

# TT-02: Cadena de respaldo de motores (speechSynthesis → nube → Piper)

## Descripción
Implementar la cadena: `speechSynthesis` por defecto, Google TTS/Azure como motor consistente y Piper como contingencia; con lista curada de voces femeninas/masculinas por plataforma.

## Criterios de Done
- [ ] Lista curada de voces por plataforma (el estándar no expone género).
- [ ] Conmutación automática ante fallo o cuota agotada.

## Subtareas
- [ ] Lista curada de voces femeninas/masculinas por navegador y sistema operativo.
- [ ] Adaptador `speechSynthesis` (motor por defecto).
- [ ] Adaptador de nube (Google TTS o Azure) con control de cuota.
- [ ] Adaptador Piper autoalojado como contingencia.

## Dependencias
- TT-01
