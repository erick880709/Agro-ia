# Plantilla del comentario de cierre en el tablero

Texto plano o Markdown simple (Azure DevOps acepta HTML/Markdown en comentarios; Jira, su formato
wiki/ADF vía el servidor MCP). Sin credenciales, datos personales ni filas de bases de datos.

```markdown
**QA Ranger — <tarea: diseño | implementación | ejecución | revisión | diagnóstico | reporte>** (<fecha>)
Skill: <capabilityId> · Corrida: <runId> · Ambiente: <ambiente>

**Alcance:** <n> casos (<IDs>) para <HU/criterios>.
**Resultado:** <pasaron> pasaron · <fallaron> fallaron · <bloqueados/omitidos> bloqueados.
**Veredicto:** <GO | GO with known risks | NO-GO> (calculado por el generador de reportes)

**Casos fallidos / defectos:**
- <TC-03 [critical]> — <resumen del fallo> — <bug propuesto o enlace>

**Evidencia:** <enlace al artefacto del pipeline o ruta resources/qa/reports/<runId>/>
**Pendientes:** <lo no ejecutado y responsable> | ninguno
**Estado del work item:** <estado anterior> → <estado nuevo> | sin cambio (<motivo>)
```
