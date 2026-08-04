---
id: 002
slug: catalogo-cultivos-fichas-tecnicas
ia_cierre: 14/100
rondas: 2
estado: lista-para-diseno
fecha: 2026-08-03
---

# NECESIDAD DE NEGOCIO REFINADA

Catálogo amplio de cultivos con fichas técnicas estructuradas que contienen umbrales edafoclimáticos, información agronómica y datos económicos verificables, trazables a fuentes oficiales. Cada ficha es creada manualmente por el administrador, pasa por revisión obligatoria de un técnico agrónomo (SLA: 5 días hábiles), y se publica con flujo borrador → en revisión → publicado. Los cultivos con solo fuente internacional (FAO GAEZ) se muestran con etiqueta visible "datos internacionales — no validados en Colombia" y sus umbrales no se usan en recomendaciones directas al agricultor hasta validación local. El sistema alerta automáticamente cada 12 meses si una ficha no ha sido revisada. Sirve como base de referencia para los modelos de IA (Modelo 2: predicción de cultivo ideal) y el motor de recomendaciones.

**Fuente(s) de origen**
- `resources/functional/requests/RF-009-catalogo-de-cultivos.md`
- `resources/design/models/RD-007-estructura-ficha-tecnica-cultivos.md`

**Justificación**

El motor de recomendaciones de AgroIA (refinamiento #1) necesita comparar las mediciones de suelo contra umbrales ideales por cultivo para determinar aptitud. Sin un catálogo validado, las recomendaciones carecen de base científica. Actualmente no existe una base de datos unificada de fichas técnicas de cultivos con umbrales verificables para el contexto colombiano. Las fuentes existen (Cenicafé, UPRA, AGROSAVIA, FAO GAEZ) pero están dispersas y no estandarizadas. Un catálogo centralizado, validado por agrónomos y con trazabilidad de fuentes es el habilitador crítico para que el motor pueda responder "¿este suelo es apto para café?" con respaldo científico.

**Actores**

| Rol | Tipo | Responsabilidad |
|-----|------|-----------------|
| Administrador | Ejecutor | Crea y edita fichas técnicas manualmente una por una; ingresa los datos desde fuentes oficiales |
| Técnico Agrónomo | Aprobador / Validador | Revisa cada ficha en ≤5 días hábiles; aprueba (→ publicado) o rechaza con correcciones (→ borrador); responsable de la veracidad agronómica |
| Cliente (Agricultor) | Beneficiario | Consulta fichas técnicas desde el dashboard y reportes |
| Investigador IES | Colaborador | Puede proponer nuevas fichas o actualizaciones basadas en evidencia científica |

**Alcance**

- ✅ IN SCOPE (MVP):
  - Catálogo amplio desde el día 1: todos los cultivos con fuentes disponibles
  - Café (Cenicafé): ficha completa, validada, trazable — prioridad máxima para el piloto Quindío
  - Cultivos colombianos con fuente oficial (UPRA, AGROSAVIA): ficha completa, validación normal
  - Cultivos solo con fuente internacional (FAO GAEZ, SoilGrids): ficha con etiqueta "datos internacionales — no validados en Colombia"; sus umbrales no se usan para recomendaciones directas; solo visibles como referencia
  - Flujo de publicación: Borrador → En revisión → Publicado
  - SLA de revisión por técnico agrónomo: 5 días hábiles
  - Si el técnico rechaza: ficha vuelve a "Borrador" con notas de corrección; el admin corrige y reenvía
  - Alerta automática cada 12 meses: "Esta ficha no ha sido revisada en más de un año"
  - Trazabilidad: cada umbral debe citar fuente verificable (ej. "Cenicafé, 2007, Guía de fertilidad del suelo")
  - Estructura extensible: campos fijos en columnas PostgreSQL + JSONB para campos específicos por cultivo

- ❌ OUT OF SCOPE (MVP):
  - Carga automática desde APIs externas (FAO, Kaggle) — solo carga manual en MVP
  - Sincronización automática con fuentes oficiales cuando se actualizan
  - Historial de versiones de cada ficha (solo versión actual en MVP)

**Criterios de Aceptación**

```
DADO que el administrador crea una nueva ficha técnica de cultivo
CUANDO completa todos los campos obligatorios y la envía a revisión
ENTONCES la ficha pasa a estado "En revisión"
Y se notifica al técnico agrónomo
Y el técnico tiene 5 días hábiles para revisarla
```

```
DADO que una ficha está en estado "En revisión"
CUANDO el técnico agrónomo la aprueba
ENTONCES la ficha pasa a estado "Publicado"
Y los umbrales de la ficha están disponibles para el motor de recomendaciones
Y la ficha es visible para los agricultores en el catálogo
```

```
DADO que una ficha proviene únicamente de fuente internacional (FAO GAEZ)
CUANDO se publica
ENTONCES se muestra con la etiqueta visible "datos internacionales — no validados en Colombia"
Y sus umbrales NO se usan para generar recomendaciones directas al agricultor
Y se indica "Requiere validación por un técnico agrónomo para uso en recomendaciones"
```

```
DADO que una ficha publicada no ha sido revisada en 12 meses
CUANDO se cumple el plazo
ENTONCES el sistema genera una alerta automática al administrador y al técnico agrónomo
Y la ficha sigue publicada pero muestra un aviso "Última revisión: [fecha] — revisión pendiente"
```

```
DADO que el técnico agrónomo rechaza una ficha en revisión
CUANDO indica los campos a corregir
ENTONCES la ficha vuelve a estado "Borrador"
Y el administrador recibe notificación con las correcciones solicitadas
```

**Restricciones y Supuestos**

- **Restricciones:**
  - Fuentes de datos con trazabilidad obligatoria: cada umbral debe citar su fuente (estudio, manual, norma)
  - Cenicafé: licencia CC BY-NC-ND pendiente de validación para uso comercial (misma brecha del refinamiento #1)
  - Datos IGAC bajo CC-BY-SA 4.0 (requiere atribución)
  - Estructura de datos: PostgreSQL con JSONB para extensibilidad por cultivo
  - CRUD de fichas solo accesible para Admin y Técnico; consulta pública para Clientes

- **Supuestos validados:**
  - La ficha de café (Cenicafé) es la más completa y validada para el piloto
  - Los cultivos sin fuente colombiana se poblarán progresivamente conforme se validen
  - El técnico agrónomo tiene capacidad para revisar fichas en el SLA de 5 días hábiles

- **Supuestos no validados:**
  - Cantidad exacta de cultivos en el catálogo inicial — [PENDIENTE DE DEFINIR — impacto: define esfuerzo de carga inicial. Estimar ~20-30 cultivos prioritarios para Colombia]
  - Disponibilidad del técnico agrónomo durante el piloto (rol puede estar externalizado al Comité de Cafeteros)

**Métricas de Éxito**

| Métrica | Línea Base | Meta | Plazo |
|---------|-----------|------|-------|
| Fichas completas y validadas (estado "Publicado") | 0 | ≥5 cultivos colombianos prioritarios (café, maíz, arroz, plátano, papa) | MVP (antes del piloto) |
| SLA de revisión (desde envío hasta aprobación/rechazo) | N/A | ≤5 días hábiles (mediana) | Continuo |
| Cobertura de trazabilidad (% de umbrales con fuente verificable) | 0% | 100% | MVP |
| Fichas con revisión periódica al día (<12 meses desde última revisión) | N/A | 100% de las fichas publicadas | Continuo |
| Fichas con fuente internacional etiquetadas correctamente | N/A | 100% | MVP |

**Prioridad (MoSCoW)**

- **Must Have:** Ficha de café completa y validada, estructura de datos con campos obligatorios, flujo borrador→revisión→publicado, SLA 5 días, trazabilidad de fuentes, etiqueta "datos internacionales", CRUD de fichas
- **Should Have:** Alerta de revisión cada 12 meses, catálogo de ≥5 cultivos colombianos validados, JSONB para extensibilidad
- **Could Have:** Notificaciones al admin cuando una ficha requiere revisión, dashboard de fichas pendientes para el técnico
- **Won't Have (en este alcance):** Carga automática desde APIs, sincronización con fuentes externas, historial de versiones

**Dependencias**

- Motor de recomendaciones (refinamiento #1) — consume los umbrales de las fichas para determinar aptitud
- Motor de conocimiento agronómico (RF-010) — las fichas alimentan las reglas del sistema experto
- Modelo 2 de IA: predicción del cultivo ideal — usa el catálogo como espacio de salida (top 5 cultivos)
- Equipo de agrónomos del Comité de Cafeteros o Cenicafé — validan la ficha de café y potencialmente otras

**Brechas pendientes**

| Campo | Información faltante | Impacto en estimación/diseño |
|-------|---------------------|------------------------------|
| Cantidad exacta de cultivos a precargar | "Catálogo amplio" es ambiguo. ¿20, 50, 100+? | Define esfuerzo de carga manual inicial. Estimar 20-30 cultivos prioritarios colombianos |
| Licencia Cenicafé para uso comercial | Misma brecha del refinamiento #1 — CC BY-NC-ND sin confirmación | Bloquea la ficha de café en producción comercial |

---

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EVOLUCIÓN DEL ÍNDICE DE AMBIGÜEDAD
 Ronda 0 (inicial): 47/100
 Ronda 1:           31/100
 Ronda 2:           14/100  ← CIERRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

✅ **Lista para diseño/estimación**
