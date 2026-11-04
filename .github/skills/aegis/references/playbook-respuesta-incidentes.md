# Playbooks de respuesta a incidentes

Basado en `building-incident-response-playbook` (mukul975/Anthropic-Cybersecurity-Skills)
y alineado con NIST SP 800-61r3 (que organiza la respuesta en torno a las funciones de
NIST CSF 2.0) y el ciclo SANS PICERL. Un playbook es un procedimiento reutilizable por
tipo de incidente, no el informe de un caso. Para un incidente en curso, prioriza
contención y preservación de evidencia y remite al equipo de respuesta del cliente
(CSIRT/SOC); Aegis no sustituye al Incident Commander.

## Cuándo

- Madurar el programa de respuesta de un producto o plataforma (p. ej. una plataforma de
  ciberseguridad o identidad para el banco).
- Después de un hallazgo crítico (secreto filtrado, IDOR explotable) para documentar la
  respuesta si se repite.
- Como entregable de arquitectura (operación de `19.1`/`21`) o de auditoría.

## Proceso

1. **Selecciona y acota** un tipo de incidente por playbook. Prioridad típica en banca:
   credencial/secreto expuesto, toma de cuenta (ATO), fuga/exfiltración de datos,
   compromiso de aplicación web/API, compromiso de cuenta cloud o pipeline CI/CD,
   ransomware, fraude transaccional automatizado, abuso de agente de IA.
2. **Define disparadores** observables (alertas, umbrales, fuentes) y criterios de
   severidad P1–P4 con tiempos de respuesta.
3. **RACI**: Incident Commander, analistas SOC, dueños del servicio, plataforma/cloud,
   legal, cumplimiento, comunicaciones, proveedor (PersonalSoft como tercero), regulador.
4. **Árboles de decisión** binarios en cada punto (¿verdadero positivo? ¿datos de
   clientes afectados? ¿credencial con escritura?).
5. **Pasos por fase** con acciones concretas y comando/consola cuando aplique:
   detección y triage → contención (corto y largo plazo) → preservación de evidencia →
   erradicación → recuperación con criterios de validación → post-incidente.
6. **Comunicación**: matriz interna, notificaciones externas y regulatorias (plazos los
   define cumplimiento del cliente), cadencia de actualización.
7. **Mejora**: acciones de detección y de código derivadas; enlaza hallazgos `HS-xxx` y
   requisitos `SEC-xxx` que habrían prevenido el incidente.
8. **Ejercicio**: tabletop con un escenario y criterio de éxito; fecha de revisión.

## Plantilla

Usa [assets/ir-playbook-template.md](../assets/ir-playbook-template.md). Mantén cada paso
ejecutable por un analista a las 3 a.m.: verbos imperativos, quién, dónde, cómo se
verifica que funcionó. Nada de "investigar el incidente" sin decir con qué.

## Ejemplo de árbol (secreto expuesto)

```
Alerta de secreto (push protection / gitleaks / reporte externo)
├── ¿El secreto es válido? (verificar en consola del proveedor, nunca usándolo para acceder a datos)
│   ├── No → cerrar como FP, documentar, ajustar regla
│   └── Sí → P1 si tiene escritura o acceso a datos de clientes; P2 en otro caso
│       ├── Revocar/rotar inmediatamente (antes de limpiar historial)
│       ├── Revisar logs del proveedor desde la fecha del commit
│       │   ├── Uso no autorizado → escalar a playbook de compromiso cloud/datos
│       │   └── Sin uso → continuar
│       └── Mover a gestor de secretos + push protection + hallazgo HS en el repo
```
