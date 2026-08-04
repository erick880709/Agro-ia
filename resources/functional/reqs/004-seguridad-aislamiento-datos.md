---
id: 004
slug: seguridad-aislamiento-datos
ia_cierre: 13/100
rondas: 1
estado: lista-para-diseno
fecha: 2026-08-03
---

# NECESIDAD DE NEGOCIO REFINADA

Sistema de seguridad integral que garantiza autenticación JWT+OAuth2 (access token 1h), autorización RBAC, comunicaciones TLS 1.2+, cifrado en reposo, cumplimiento OWASP Top 10 con SAST/DAST mensual en CI/CD, y multi-tenancy mediante Row-Level Security (RLS) en PostgreSQL con `tenant_id` en cada tabla — todo bajo residencia de datos en servidores en Colombia. El aislamiento de datos entre clientes es estricto: ningún agricultor puede acceder a información de otro, verificado mediante pruebas de penetración. Se cumple la Ley 1581 de 2012 (habeas data) con consentimiento informado, derecho de supresión y logs de auditoría retenidos ≥6 meses.

**Fuente(s) de origen**
- `resources/functional/requests/RF-004-aislamiento-datos-clientes.md`
- `resources/architecture/definitions/RNF-004-seguridad-autenticacion.md`
- `resources/architecture/definitions/RNF-005-seguridad-owasp-datos.md`
- `resources/architecture/definitions/RT-015-multi-tenancy-aislamiento.md`

**Justificación**

La plataforma maneja datos personales y agronómicos de agricultores colombianos. La Ley 1581 de 2012 exige protección de datos personales con consentimiento informado, derecho de acceso/rectificación/supresión y seguridad comprobable. Un incidente de fuga de datos entre clientes destruiría la confianza y expondría a sanciones legales. La multi-tenancy con RLS es la base técnica del aislamiento; JWT+OAuth2 con RBAC asegura que solo usuarios autorizados accedan a sus propios datos; OWASP y cifrado protegen contra ataques comunes; y la residencia de datos en Colombia asegura cumplimiento normativo y soberanía digital.

**Actores**

| Rol | Tipo | Responsabilidad |
|-----|------|-----------------|
| Administrador | Ejecutor / Auditor | Gestiona usuarios y roles; monitorea logs de seguridad; responde a incidentes |
| Cliente (Agricultor) | Sujeto de protección | Dueño de sus datos; debe dar consentimiento informado; puede solicitar acceso/rectificación/supresión |
| Sistema (backend) | Ejecutor automático | Valida JWT en cada request; aplica RLS; registra auditoría; ejecuta SAST/DAST en CI/CD |

**Alcance**

- ✅ IN SCOPE (MVP):
  - Autenticación: JWT RS256, OAuth2, access token 1h, refresh token 7 días
  - Autorización: RBAC con 4 roles, verificación en cada endpoint vía API Gateway
  - TLS 1.2+ en todas las comunicaciones
  - Cifrado en reposo: datos personales, credenciales (bcrypt/argon2)
  - Multi-tenancy: Row-Level Security en PostgreSQL, `tenant_id` en cada tabla
  - Datos compartidos multi-tenant: catálogo de cultivos, reglas agronómicas
  - Aislamiento S3: prefijo por tenant para reportes y fotografías
  - OWASP Top 10: protección contra inyección, XSS, CSRF, cabeceras HTTP
  - SAST/DAST: ejecución mensual en pipeline CI/CD
  - Pruebas de penetración: mensuales con herramientas automatizadas
  - Logs de auditoría: retención ≥6 meses, sistema centralizado
  - Ley 1581/2012: consentimiento informado, derecho de acceso/rectificación/supresión
  - Secrets Manager: AWS Secrets Manager o HashiCorp Vault
  - WAF en API Gateway
  - Network Policy en Kubernetes para aislar servicios sensibles
  - Residencia de datos: servidores en Colombia

- ❌ OUT OF SCOPE (MVP):
  - SOC2 o ISO 27001 (no requerido por el RFP)
  - Pentest por consultora externa (solo herramientas automatizadas en MVP)
  - Anonimización de datasets para publicación FAIR (fase de investigación)

**Criterios de Aceptación**

```
DADO que un cliente autenticado intenta acceder a datos de otro cliente
CUANDO manipula un ID en la URL o parámetro de API
ENTONCES RLS en PostgreSQL bloquea la consulta
Y la API retorna 403 Forbidden
Y el intento se registra en logs de auditoría
```

```
DADO que un token JWT ha expirado (más de 1h desde su emisión)
CUANDO el cliente intenta usarlo en una petición
ENTONCES el API Gateway rechaza la petición con 401 Unauthorized
Y el cliente debe usar su refresh token para obtener uno nuevo
```

```
DADO que se ejecuta el pipeline CI/CD
CUANDO se completa el build
ENTONCES se ejecuta SAST (análisis estático de código) automáticamente
Y una vez al mes se ejecuta DAST (análisis dinámico) contra el entorno de staging
Y las vulnerabilidades críticas bloquean el despliegue a producción
```

**Restricciones y Supuestos**

- TLS 1.2+, JWT RS256, bcrypt/argon2 para hashing, RLS PostgreSQL
- Secrets Manager, WAF, Network Policy, logs ≥6 meses
- Residencia de datos en Colombia (requiere nube con región local o nube privada)
- Pendiente: viabilidad de servidores en Colombia en AWS (evaluar Local Zones o nube local)

**Métricas de Éxito**

| Métrica | Meta |
|---------|------|
| Aislamiento entre clientes | 0 incidentes de fuga en pentest |
| Cobertura OWASP Top 10 | 10/10 cubiertos |
| SAST/DAST en CI/CD | 1 vez/mes |
| Logs de auditoría | 100% de operaciones sensibles registradas |

**Prioridad (MoSCoW)**
- Must: JWT+OAuth2, RBAC, TLS, RLS, OWASP, logs auditoría, Ley 1581
- Should: SAST/DAST mensual, pentest automatizado, WAF, Secrets Manager
- Could: Dashboard de seguridad, alertas de intentos de acceso no autorizado
- Won't: SOC2/ISO 27001, pentest externo, anonimización FAIR

**Brechas:** Viabilidad de servidores en Colombia (AWS Local Zones o alternativa), algoritmo de hashing (bcrypt vs argon2)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EVOLUCIÓN DEL ÍNDICE DE AMBIGÜEDAD
 Ronda 0 (inicial): 38/100
 Ronda 1:           13/100  ← CIERRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

✅ **Lista para diseño/estimación**
