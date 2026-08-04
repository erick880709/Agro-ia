---
id: 008
slug: usuarios-roles-membresias
ia_cierre: 15/100
rondas: 1
estado: lista-para-diseno
fecha: 2026-08-03
---

# NECESIDAD DE NEGOCIO REFINADA

Gestión completa del ciclo de vida de usuarios con registro self-service por email, 4 roles RBAC (Administrador, Cliente/Agricultor, Técnico Agrónomo, Investigador IES), y 3 planes de membresía con límites de fincas y análisis. Sin 2FA en MVP. Pasarela de pagos preparada arquitectónicamente pero no implementada. Sesión JWT de 1h con refresh token.

**Planes de membresía**

| Plan | Fincas máx | Análisis/mes | Chat IA | Historial | Precio (COP) |
|------|-----------|-------------|---------|-----------|--------------|
| Mensual | 1 | 2 | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| Semestral | 3 | 6 | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |
| Anual | 4 | 8 | [PENDIENTE] | [PENDIENTE] | [PENDIENTE] |

**Fuente(s):** RF-002, RF-003, RF-005

**Actores:** Administrador (gestión total), Cliente (self-service, limitado a su plan), Técnico Agrónomo, Investigador IES

**Alcance**
- ✅ Self-service con email, JWT 1h, RBAC 4 roles, RLS PostgreSQL, límites por plan, notificaciones al alcanzar límite
- ❌ Sin 2FA, sin pasarela de pagos implementada, sin SSO/redes sociales, sin plan gratuito (a definir)

**Métricas**
| Métrica | Meta |
|---------|------|
| Registro completado | <2 min |
| Roles y permisos correctos | 100% |

**Prioridad:** Must: registro, login, recuperación, RBAC, límites. Should: notificaciones límite. Won't: 2FA, SSO, pasarela pagos.

**Brechas:** Chat IA e historial por plan, precios, complejidad de contraseña (asumir 8+ caracteres con mayúscula+número), ¿plan gratuito?

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EVOLUCIÓN DEL ÍNDICE DE AMBIGÜEDAD
 Ronda 0 (inicial): 24/100
 Ronda 1:           15/100  ← CIERRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

✅ **Lista para diseño/estimación**
