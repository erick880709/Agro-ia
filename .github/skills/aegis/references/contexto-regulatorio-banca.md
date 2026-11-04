# Contexto regulatorio (banca y seguros en Colombia)

Aegis no emite dictámenes de cumplimiento: traduce requisitos a controles técnicos
verificables y señala dónde el código o la IaC los contradicen. Las versiones vigentes
y su aplicabilidad las confirma el área de cumplimiento/riesgo del cliente; registra en
la línea base qué marcos aplican.

## Marcos frecuentes

| Marco | Qué traduce Aegis a controles |
|---|---|
| **PCI DSS v4.0.1** (si hay datos de tarjeta) | No almacenar SAD tras autorización; PAN enmascarado en pantalla y logs (6 primeros/4 últimos como máximo); cifrado de PAN en reposo; TLS fuerte; desarrollo seguro y revisión de código (req. 6); gestión de vulnerabilidades y parches; inventario de scripts en páginas de pago (6.4.3); MFA para acceso administrativo; logs de auditoría (req. 10) |
| **SFC — Circular Externa 007 de 2018** (requisitos mínimos de seguridad de la información y ciberseguridad, incorporados a la Circular Básica Jurídica) | Gestión de riesgo de ciberseguridad, gestión de incidentes y reporte, controles de acceso, monitoreo; las versiones e instrucciones posteriores de la SFC pueden actualizarla |
| **SFC — Circular Externa 029 de 2014** (seguridad y calidad en canales y medios para operaciones) | Cifrado en canales, autenticación fuerte en operaciones monetarias, registro de operaciones |
| **Ley 1581 de 2012 y Decreto 1377 de 2013** (habeas data) | Minimización, finalidad, autorización del titular, seguridad de datos personales, transferencias; implica no sobreexponer PII en APIs, logs ni entornos no productivos |
| **ISO/IEC 27001:2022 Anexo A** | Controles 8.25–8.29 (ciclo de desarrollo seguro, requisitos, arquitectura segura, codificación segura, pruebas de seguridad) y 8.9 (gestión de configuración), 8.12 (prevención de fuga de datos) |
| **NIST SSDF (SP 800-218)** | Prácticas PW (producir software bien asegurado) y RV (responder a vulnerabilidades) como marco de madurez del ciclo |

## Cómo usarlo en un hallazgo

- Agrega el requisito en `ext.compliance` solo cuando el hallazgo lo contradice de forma
  directa (p. ej. PAN completo en log → PCI DSS 3.4/10.x). No pegues listas de marcos a
  cada hallazgo.
- La referencia regulatoria eleva prioridad y documentación, no la severidad técnica:
  la severidad sigue el impacto demostrado.
- Datos reales de clientes en ambientes de desarrollo o pruebas (copias de producción sin
  anonimizar) son hallazgo de privacidad aunque el código sea correcto.
