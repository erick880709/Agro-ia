# Comentario de cierre en el work item (code-review)

Markdown simple. Sin secretos, datos personales ni fragmentos de código explotables: enlaza el reporte.

```markdown
**Code review — <veredicto>** · <fecha> · Ronda <n>
Revisión: <SHA / rama / "sin commit + hash"> · Rigor: <ligero | estándar | reforzado> · Independencia: <independiente | misma-sesion>

**Hallazgos:** <b> bloqueantes · <m> mayores · <n> menores · <k> nits · <p> preguntas
- B-01 <resumen en una frase> (`archivo:línea`)
- M-01 …

**Criterios:** AC-01 ✅ · AC-02 ❌ · AC-03 ⚠️ <nota breve>
**Gate:** build <✅/❌/not_run> · lint <…> · tests <…>
**Sonar:** quality gate <OK | ERROR | vencido | no-disponible> · cobertura código nuevo <valor> % (objetivo <umbral> %)
**Reporte:** <docs/changes/<id>/review.md | docs/reviews/CR-NNN-<slug>.md>
**Estado:** <anterior> → <nuevo> | sin cambio (<motivo>)
```
