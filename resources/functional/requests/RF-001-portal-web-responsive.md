# RF-001: Portal Web Responsive

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 5.1; RFP-inicial.md — Sección 3 (Portal Web)
**Prioridad:** Alta

## Descripción
La plataforma debe contar con un sitio web responsive que se adapte correctamente a diferentes dispositivos: Desktop, Tablet y Celulares. Debe ser compatible con los navegadores modernos: Chrome, Safari, Edge y Firefox. El portal web constituye el punto de entrada principal para todos los actores del sistema (agricultores, técnicos agrónomos, investigadores y administradores).

## Actores involucrados
- Agricultor
- Técnico Agrónomo
- Investigador IES
- Administrador

## Criterios de aceptación
- La interfaz debe renderizarse correctamente en resoluciones Desktop (≥1024px), Tablet (768px–1023px) y Mobile (<768px).
- Compatibilidad verificada en las últimas 2 versiones estables de Chrome, Safari, Edge y Firefox.
- No especificados en el RFP — definir criterios de usabilidad y accesibilidad (WCAG) con el cliente.

## Dependencias / relacionados
- RF-002: Gestión de usuarios
- RD-006: Lineamientos de UX
- RT-002: Stack frontend Angular 21

## Notas del analista
- El RFP original sugiere React/Next.js como stack frontend, pero el cliente ha definido **Angular 21** como framework obligatorio para el frontend. Esto implica usar Angular Material o similar para el design system responsive.
- No se especifica si se requiere PWA (Progressive Web App) para funcionamiento offline en zonas rurales con conectividad limitada — se recomienda evaluarlo con el cliente.
