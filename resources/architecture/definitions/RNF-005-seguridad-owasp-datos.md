# RNF-005: Seguridad — Cumplimiento OWASP y Protección de Datos

**Tipo:** Requerimiento no funcional
**Categoría:** Seguridad
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 6.3

## Descripción
La plataforma debe cumplir con los estándares de seguridad de aplicaciones web definidos en OWASP Top 10, incluyendo pero no limitado a:

- Protección contra inyección SQL, NoSQL y comandos.
- Validación y sanitización de entradas de usuario.
- Protección contra Cross-Site Scripting (XSS).
- Protección contra Cross-Site Request Forgery (CSRF).
- Cabeceras de seguridad HTTP (CSP, HSTS, X-Frame-Options, X-Content-Type-Options).
- Rate limiting en endpoints de API.
- Registro y auditoría de accesos y operaciones relevantes (log de seguridad).

Adicionalmente, se debe cumplir con la normativa colombiana de protección de datos personales (Ley 1581 de 2012 — Habeas Data), particularmente en lo relacionado con:

- Consentimiento informado para la captura de datos de los agricultores.
- Derecho de acceso, rectificación y supresión de datos personales.
- Gobernanza y propiedad de los datos capturados por los sensores del agricultor.
- Aplicación de principios FAIR si se publican datasets derivados con fines de investigación.

## Criterio medible / restricción concreta
- Pruebas de seguridad (SAST/DAST) deben ejecutarse como parte del pipeline CI/CD.
- Los logs de auditoría deben conservarse por un mínimo de 6 meses.
- No especificados en el RFP — definir: periodicidad de los escaneos de seguridad, responsable de la respuesta a incidentes, plan de notificación de brechas de seguridad.

## Impacto en la arquitectura
- WAF (Web Application Firewall) en el API Gateway.
- Sanitización de inputs en cada endpoint de API.
- Sistema centralizado de logs de auditoría (ELK stack o servicio cloud equivalente).
- Políticas de retención de datos configuradas en la base de datos y almacenamiento de objetos.
- Mecanismo de anonimización de datos para datasets de investigación.

## Notas del analista
- La Ley 1581 de 2012 exige que los datos personales se almacenen de forma que se garantice su seguridad y confidencialidad. El aislamiento de datos entre clientes (RF-004) es un habilitador directo de este cumplimiento.
- Si el componente investigativo planea publicar datasets bajo principios FAIR, se debe implementar un proceso de anonimización/agregación que impida la reidentificación de agricultores individuales.
- El RFP menciona que los datos del agricultor no deben exponerse a Internet (agente IA sin navegación libre), pero no detalla requisitos de residencia de datos (¿los datos deben permanecer en servidores en Colombia?).
