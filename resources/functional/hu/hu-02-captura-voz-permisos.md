---
id: HU-02
type: Historia de Usuario
epic: 010
priority: Alta
points: 5
---

# HU-02: Captura de voz y gestión de permisos del micrófono

## Como
Productor o técnico de campo

## Quiero
Iniciar y detener la grabación de mi voz, con solicitud de permiso solo al activarla y orientación si lo deniego

## Para
Dictar mi consulta sin fricción y recuperarme si el permiso no está habilitado

## Criterios de Aceptación
- [ ] CA1: El permiso de micrófono se solicita únicamente al activar la función de voz.
- [ ] CA2: Si el permiso se deniega, se explica cómo habilitarlo y el campo de escritura sigue disponible.
- [ ] CA3: La captura finaliza por acción del usuario o tras 2 s de silencio continuo.
- [ ] CA4: La grabación se detiene automáticamente al alcanzar 60 s y pasa a procesamiento.
