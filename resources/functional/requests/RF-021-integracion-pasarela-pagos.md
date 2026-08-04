# RF-021: Integración Futura con Pasarela de Pagos

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.3; RFP-inicial.md — Sección 3 (Gestión de Membresías)
**Prioridad:** Baja (para MVP — preparación arquitectónica)

## Descripción
La arquitectura del sistema debe estar preparada para integrar una pasarela de pagos en una fase posterior al MVP, permitiendo la comercialización de membresías mediante pago electrónico. Durante el MVP, la lógica de membresías debe estar implementada (límites, control de acceso), pero el pago puede ser simulado o gestionado manualmente por el administrador.

La integración futura debe contemplar:
- Procesamiento de pagos con tarjeta de crédito/débito.
- Pagos por transferencia bancaria (PSE en Colombia).
- Facturación electrónica.
- Renovación automática de membresías.
- Gestión de reembolsos y disputas.

## Actores involucrados
- Cliente (Agricultor) — realiza el pago
- Administrador — gestiona pagos y resuelve incidencias
- Pasarela de pagos (sistema externo)

## Criterios de aceptación
- La arquitectura de pagos está documentada y los endpoints están definidos (aunque no implementados en MVP).
- Los webhooks de notificación de pago están contemplados en el diseño.
- El flujo de activación de membresía está desacoplado del método de pago.
- No especificados en el RFP — definir: ¿proveedor de pasarela (PayU, Stripe, MercadoPago, Wompi)?, ¿divisas aceptadas (COP, USD)?, ¿modelo de facturación electrónica exigido por la DIAN?

## Dependencias / relacionados
- RF-005: Gestión de membresías
- RT-014: CI/CD (preparación de entornos)

## Notas del analista
- En Colombia, las pasarelas más usadas son PayU Latam, MercadoPago, Wompi (Bancolombia) y Stripe (cobertura limitada). PayU y Wompi tienen buena integración con PSE (transferencia bancaria), que es el método de pago preferido en Colombia.
- La facturación electrónica es obligatoria en Colombia (regulada por la DIAN). Cualquier solución de pagos debe contemplar este requisito para la fase de comercialización real.
