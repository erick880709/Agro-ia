---
id: HU-07
type: Historia de Usuario
epic: 011
priority: Baja
points: 8
---

# HU-07: Voz personalizada (Fase 2)

## Como
Productor o técnico de campo

## Quiero
Grabar mi propia voz para que las respuestas se lean con ella, y poder probarla, regrabarla, desactivarla o eliminarla

## Para
Una experiencia más personal

## Criterios de Aceptación
- [ ] CA1: Flujo guiado de grabación con consentimiento explícito e indicadores de calidad.
- [ ] CA2: Se verifica que la voz es la del propio usuario (frase leída en vivo); solo se permite la voz propia.
- [ ] CA3: "Mi voz" aparece como opción solo cuando existe y está activa.
- [ ] CA4: Se puede previsualizar, regrabar, desactivar y eliminar; al eliminar se borran muestra y representación.

## Recurso de datos involucrado

### Recurso
- **Nombre:** VozPersonalizada
- **Capa(s):** backend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| usuario_id | UUID | Sí | Dueño de la voz (aislamiento por usuario) |
| estado | texto | Sí | procesando / activa / desactivada / eliminada |
| creada_en | fecha | Sí | Fecha de creación |
| muestra / representación | binario | — | No especificado en la épica — definir con negocio (cifrado, retención) |

### Relaciones con otros recursos
- `Usuario` (1:1): cada usuario tiene a lo sumo una voz personalizada.

## Subtareas
- [ ] Flujo guiado de grabación con indicadores de calidad y frase de verificación.
- [ ] Consentimiento explícito y pantalla de información (Ley 1581).
- [ ] Procesamiento asíncrono con estado "procesando tu voz".
- [ ] Gestión de la voz (previsualizar, regrabar, desactivar, eliminar con borrado efectivo).
