# Guía: diligenciar la Taxonomía de Costos Bancolombia (pestaña "Esfuerzo & Condiciones")

*Aplica cuando el cliente es Bancolombia (o Grupo Cibest) y la preventa debe entregarse en su formato "Taxonomía de Costos". Solo se diligencia la pestaña **Esfuerzo & Condiciones**; las demás pestañas (Valores diferenciales, Costos Adicionales & Riesgos) las completa el área financiera/comercial.*

## 1. Regla de oro: no abrir y guardar el formato con openpyxl

La hoja trae 12 listas desplegables (extensión x14 que referencian las pestañas de parametrización) y el logo como dibujo. **openpyxl los elimina al guardar.** Usa siempre:

```bash
python3 scripts/diligenciar_taxonomia_bancolombia.py entrada.json "<formato del cliente>.xlsx" \
        resources/estimation/taxonomia-bancolombia-{slug}.xlsx [--escenario tradicional|con_ia]
```

El script edita el XML de la hoja, conserva todo lo demás, fuerza el recálculo al abrir en Excel y valida cada valor contra las listas de "Parametrización Taxonomia" y "Parametrización Roles". Usa siempre **el formato que entregue el usuario** (puede cambiar de versión); si no lo adjunta, pídelo.

## 2. Cómo interpreta el formato el esfuerzo

Por cada rol: `HH Esfuerzo (M) = Días asignados (L) × Horas/día (E9) × Recursos (J)` y `TOTAL (O) = (M + HH Garantía + HH Disponibilidad) × Asignación (K)`. `E11 = suma de subtotales` de todos los bloques, así que **los bloques se suman**: cada bloque es una fase, no un escenario alternativo.

El script fija para cada rol:
- **L (días)** = duración de la fase en días hábiles = horas de desarrollo de la fase ÷ (personas de desarrollo × horas efectivas/día), redondeado hacia arriba.
- **J (recursos)** = personas de desarrollo para el rol de desarrollo; 1 para los demás (sube si el rol no cabe en la fase a tiempo completo).
- **K (asignación)** = horas del rol ÷ (L × E9 × J), sin redondear, para que **O reproduzca exactamente las horas del motor**.
- M, O, Q (sprints = L/10) y R (meses = L/20) quedan como fórmulas del formato.

## 3. Mapeo de la estimación al formato

| Formato | Origen |
|---|---|
| Bloques (ESCENARIO 1, 2, …) | Una fase por prioridad: Alta → Fase 1 MVP, Media → Fase 2, Baja → Fase 3 (`agrupar_por: "unica"` para un solo bloque). Se crean o eliminan bloques según haga falta. |
| Filas de rol | PM, Arquitecto, Desarrollo, QA, UX/UI del motor; se omiten roles con 0 h. PM global prorrateado por horas de cada fase. |
| Horas | Escenario `tradicional` (por defecto) o `con_ia` (desarrollo con factor SDD). Genera un archivo por escenario si el cliente quiere ambos. |
| E8 / E9 | "Días" / jornada (8,4 h por defecto). |
| E10 Duración | Suma de días de las fases (fases secuenciales). |
| Ficha técnica (C8–C15, E12, E13, G8) | Sección `ficha_tecnica` del JSON. Versión/fecha **financiera** se dejan vacías. |

Mapeo por defecto de roles a "Parametrización Roles" (combinaciones válidas en el formato actual):

| Rol del motor | Familia de Trabajo | Familia de Cargo | Cargo | Seniority |
|---|---|---|---|---|
| PM | T. Gerencia de Proyectos y Agilismo | Gerente de Proyecto | Project Manager | Senior |
| Arquitecto | T. Arquitectura de TI y Digital | Arquitectura de Aplicación | Senior Architect | Senior |
| Desarrollo (senior/mixto) | 2. Ingeniería de software | Desarrollo Full-Stack Senior | Senior Software Developer | Senior |
| Desarrollo (semi-senior) | 2. Ingeniería de software | Desarrollo Full-Stack Intermedio | Intermediate Software Developer | Intermediate |
| Desarrollo (junior) | 2. Ingeniería de software | Desarrollo Back-End Junior | Junior Software Developer | Junior |
| QA | 4. Ingeniería de QA | Analista de Certificación Senior | Senior Certification Analyst | Senior |
| UX/UI | 1. Diseño de Producto Digital | Diseñador Cusotmer Journey(CJ) y de Experiencia(UX) | Technical Lead | Senior |

El perfil de desarrollo se toma del perfil dominante (por horas) de los ítems de la fase. Sobrescribe cualquier rol en `taxonomia_bancolombia.roles` cuando el alcance lo pida (ej. arquitecto de integración, desarrollador mainframe, automatizador de pruebas). Los textos deben coincidir **exactamente** con la lista (incluidos errores tipográficos del formato como "Cusotmer").

## 4. Decisiones que debes declarar al usuario

1. **Cifra:** por defecto `mas_probable`. El margen hasta P80 que entrega el motor **no** se mete en Esfuerzo: repórtalo para registrarlo en "Costos Adicionales & Riesgos" (así no se cuenta dos veces cuando finanzas agregue riesgos). Usa `cifra: "p80"` solo si el usuario lo pide.
2. **Modo de horas:** por defecto `esfuerzo` (O = horas estimadas). Usa `dedicacion` (O = horas ÷ factor productivo) solo si la productividad se calibró con horas netas y el cliente paga tiempo asignado completo — nunca descuentes dos veces.
3. HH Garantía, HH Disponibilidad, póliza y datos financieros se dejan vacíos salvo que el usuario los dé.

## 5. Sección del JSON de entrada

```json
"taxonomia_bancolombia": {
  "ficha_tecnica": {
    "cliente": "Bancolombia", "arquitecto_responsable": "Edwin Alfonso Hincapíe",
    "nombre_proyecto": "…", "url_sharepoint": "", "id_jira": "MV-0000",
    "modelo_negocio": "Delivery", "modelo_adquisicion": "Agile Controlled",
    "linea_servicio": "Soluciones empresariales", "version_preventa": 1,
    "fecha_preventa": "2026-09-24", "poliza": "Ninguna"
  },
  "nombre_servicio": "…",
  "cifra": "mas_probable", "modo_horas": "esfuerzo", "agrupar_por": "prioridad",
  "base_operacion": "Colombia", "nivel_ingles": "Nativo", "disponibilidad": "Horario Oficina",
  "roles": { "arquitecto": { "familia_trabajo": "…", "familia_cargo": "…", "cargo": "…", "seniority": "…" } }
}
```

Pregunta al usuario lo que no sepas de la ficha técnica (arquitecto responsable, ID Jira, modelo de adquisición); no inventes esos datos.

## 6. Verificación antes de entregar

- El resumen JSON del script debe tener `esfuerzo_total_formato_h` = `esfuerzo_motor_mas_probable_h` (o P80 si se pidió) y `advertencias` vacías; si no, corrige los valores señalados.
- Para revisar cifras localmente: copia el archivo y corre `recalc.py` de la skill `xlsx` **sobre la copia**. El único error esperado es `#NAME?` en F9 (XLOOKUP del formato, que LibreOffice no evalúa; Excel sí). Nunca entregues la copia recalculada.
- Las cifras del PPTX, HTML y MD deben coincidir con las del formato.
