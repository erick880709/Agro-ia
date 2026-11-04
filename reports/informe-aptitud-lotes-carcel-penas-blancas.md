# Informe de aptitud por lote — Finca Carcel Peñas blancas

| | |
|---|---|
| **Finca** | Carcel Peñas blancas (Calarcá, Quindío) |
| **ID** | `042217d5-0c84-40be-aa5f-080429fbfcba` |
| **Motor** | Sistema experto de reglas UPRA / Cenicafé / AGROSAVIA |
| **Fecha de análisis** | 2026-11-03 |
| **Método de agregación** | Mediana de las lecturas por lote (la lectura de NPK es sin calibrar) |

> ⚠️ **Alcance de la confiabilidad:** el sensor NPK (`esp32-npk-001`) no está calibrado
> contra laboratorio. Las conclusiones sobre **pH y conductividad eléctrica** son confiables
> (calibradas de fábrica); las de **nitrógeno, fósforo y potasio** son **condicionales** y
> requieren análisis de laboratorio antes de aplicar fertilizantes.

---

## Lote Frijol

**Clasificación:** Moderadamente apta (pendiente de validación técnica)  
**Confianza del modelo:** 24%  
**Lecturas analizadas:** 110  
**Coordenada del punto:** `pos_x=148.71, pos_y=-613.37` (m)

### Datos de entrada (mediana y rango)

| Variable | Mediana | Mín | Máx |
|---|---|---|---|
| pH | 7.9 | 7.1 | 9 |
| Nitrógeno (N) | 0 | 0 | 4 |
| Fósforo (P) | 2 | 0 | 7 |
| Potasio (K) | 5 | 0 | 17 |
| Conductividad eléctrica (CE) | 0.03 | 0 | 0.1 |
| Humedad ambiental | 31.5 | 24.3 | 65.4 |
| Temperatura ambiental | 21.5 | 20.8 | 25.1 |

### Evaluación frente al cultivo

| Variable | Estado | Valor | Rango óptimo | Prioridad | Acción recomendada |
|---|---|---|---|---|---|
| pH | EXCESO | 7.9 | [5.5 - 7.0] | Alta | Encalar si el pH es menor a 5.5; el fríjol es sensible a la acidez. |
| | | | | | _pH 7.9 — alcalino en escala general, pero fuera del rango óptimo para Fríjol [5.5–7]_ |
| P | DEFICIT | 2 | [20.0 - 60.0] | Alta | Ajustar fósforo: fundamental para nodulación y floración. ⚠️(condicional a laboratorio) |
| pH | EXCESO | 7.9 | [5.0 - 7.5] | Media | Corregir acidez con encalado (cal dolomita) si pH < 5.0, o alcalinidad incorporando materia orgánica ácida si pH > 7.5. |
| | | | | | _pH 7.9 — alcalino en escala general, pero fuera del rango óptimo para Fríjol [5.5–7]_ |
| N | DEFICIT | 0 | [40.0 - 120.0] | Media | Ajustar nitrógeno: el fríjol fija N pero responde a arranque (10-20 kg/ha). ⚠️(condicional a laboratorio) |
| K | DEFICIT | 5 | [100.0 - 250.0] | Media | Ajustar potasio: KCl en banda al momento de la siembra. ⚠️(condicional a laboratorio) |

**Resumen del modelo:** Análisis de aptitud para Fríjol: clasificación Moderadamente apta (pendiente de validación técnica).

---

## Lote Café

**Clasificación:** No apta (pendiente de validación técnica)  
**Confianza del modelo:** 11%  
**Lecturas analizadas:** 89  
**Coordenada del punto:** `pos_x=87.18, pos_y=-458.92` (m)

### Datos de entrada (mediana y rango)

| Variable | Mediana | Mín | Máx |
|---|---|---|---|
| pH | 7.3 | 6.5 | 8.9 |
| Nitrógeno (N) | 1 | 0 | 13 |
| Fósforo (P) | 4 | 0 | 19 |
| Potasio (K) | 9 | 1 | 45 |
| Conductividad eléctrica (CE) | 0.06 | 0.01 | 0.28 |
| Humedad ambiental | 50.6 | 30.7 | 64.7 |
| Temperatura ambiental | 22.7 | 20.7 | 24.1 |

### Evaluación frente al cultivo

| Variable | Estado | Valor | Rango óptimo | Prioridad | Acción recomendada |
|---|---|---|---|---|---|
| pH | EXCESO | 7.3 | [5.5 - 6.5] | Critica | Ajustar pH al rango 5.5-6.5: encalado dolomítico si es ácido o yeso agrícola si es alcalino. |
| | | | | | _pH 7.3 — neutro en escala general, pero fuera del rango óptimo para Café [5.5–6.5]_ |
| N | DEFICIT | 1 | [200.0 - 400.0] | Alta | Nitrógeno fuera del rango objetivo (200-400): ajustar plan de fertilización nitrogenada fraccionada según Cenicafé. ⚠️(condicional a laboratorio) |
| P | DEFICIT | 4 | [30.0 - 75.0] | Alta | Fósforo fuera del rango objetivo (30-75): aplicar DAP o roca fosfórica en hoyado o en banda. ⚠️(condicional a laboratorio) |
| K | DEFICIT | 9 | [100.0 - 300.0] | Alta | Potasio fuera del rango objetivo (100-300): aplicar KCl según la etapa del cultivo. ⚠️(condicional a laboratorio) |

**Resumen del modelo:** Análisis de aptitud para Café: clasificación No apta (pendiente de validación técnica).

---

## Conclusiones y plan de acción

### Hallazgo principal: pH alcalino en ambos lotes

El parámetro más confiable (pH, calibrado de fábrica) está **por encima del rango óptimo**
en los dos lotes:

| Lote | pH medido | Rango óptimo | Diagnóstico |
|---|---|---|---|
| Frijol | 7.9 | [5.5 - 7.0] | Alto: el fríjol tolera hasta 7.0 y el suelo está en 7.9 |
| Café | 7.3 | [5.5 - 6.5] | Crítico: el café requiere suelo ácido (5.5–6.5) |

**Acciones recomendadas (en orden de prioridad):**

1. **Café (crítico):** bajar el pH de 7.3 a 5.5–6.5. Para suelo alcalino se aplica
   **yeso agrícola** y/o **azufre elemental** con materia orgánica, en dosis según análisis
   de laboratorio (CIC y carbonatos). No aplicar cal dolomítica (subiría aún más el pH).
2. **Frijol:** bajar el pH de 7.9 a ≤ 7.0 incorporando **materia orgánica ácida**
   (compost, gallinaza madura) y, si el laboratorio lo confirma, enmienda ácida.
3. **Validar NPK en laboratorio antes de fertilizar:** el sensor reporta N, P y K muy bajos,
   pero **no está calibrado**; no se debe fertilizar con base en esos valores. Un análisis de
   suelo permitirá calcular dosis reales de nitrógeno, fósforo y potasio.
4. **Completar variables de fertilidad faltantes** (materia orgánica, CIC, calcio, magnesio,
   azufre y micronutrientes) para subir la confianza del modelo y cerrar el plan de fertilización.
5. **Corregir el GPS del sensor:** 2 lecturas se registraron con la coordenada por defecto
   del firmware (4.578333, -75.666944), fuera de la finca; revisar el firmware del `esp32-npk-001`.

> La confianza del modelo es baja (24% fríjol, 11% café) porque faltan variables de
> fertilidad y el NPK no está calibrado. Las conclusiones de **pH son firmes**; las demás
> son **orientativas** y deben confirmarse con análisis de laboratorio.
