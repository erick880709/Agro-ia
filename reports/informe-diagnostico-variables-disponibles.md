# Diagnóstico por lote — solo variables medidas

| | |
|---|---|
| **Finca** | Carcel Peñas blancas (Calarcá, Quindío) |
| **ID** | `042217d5-0c84-40be-aa5f-080429fbfcba` |
| **Alcance** | Solo las variables medidas por el sensor: **pH, CE, N, P, K** (5 de 18) |
| **Datos** | Depurados con la regla del sensor: 101 lecturas dentro del rango objetivo (pH 3–9, CE 0,01–10 dS/m, NPK 1–1.999 mg/kg) |
| **Método** | Mediana de las lecturas por lote · reglas UPRA / Cenicafé / AGROSAVIA |

> Las variables **pH y CE** son confiables (sensor calibrado de fábrica). **N, P y K** fueron
> medidas pero el sensor no está calibrado, por lo que sus recomendaciones son **condicionales
> a laboratorio**. Las variables no medidas (materia orgánica, CIC, calcio, magnesio, azufre,
> micronutrientes, humedad y temperatura de suelo) quedan **fuera del alcance** de este
> diagnóstico y **no penalizan la confianza**.

## Lote Frijol

**Clasificación:** Moderadamente apta · **Confianza:** 40% · **Lecturas:** 38 · **Reglas evaluadas:** 6

| Variable | Mediana | Mín | Máx |
|---|---|---|---|
| pH | 7.8 | 7.3 | 8.9 |
| CE (dS/m) | 0.069 | 0.039 | 0.101 |
| N (ppm) | 2 | 1 | 4 |
| P (ppm) | 4 | 2 | 7 |
| K (ppm) | 11 | 6 | 16 |

| Variable | Estado | Valor | Rango óptimo | Prioridad | Acción |
|---|---|---|---|---|---|
| pH | EXCESO | 7.8 | 5.5 – 7 | Alta | Encalar si el pH es menor a 5.5; el fríjol es sensible a la acidez. |
| Fósforo (P) | DEFICIT | 4 | 20 – 60 | Alta | Ajustar fósforo: fundamental para nodulación y floración. — condicional a laboratorio |
| pH | EXCESO | 7.8 | 5 – 7.5 | Media | Corregir acidez con encalado (cal dolomita) si pH < 5.0, o alcalinidad incorporando materia orgánica ácida si pH > 7.5. |
| Nitrógeno (N) | DEFICIT | 2 | 40 – 120 | Media | Ajustar nitrógeno: el fríjol fija N pero responde a arranque (10-20 kg/ha). — condicional a laboratorio |
| Potasio (K) | DEFICIT | 11 | 100 – 250 | Media | Ajustar potasio: KCl en banda al momento de la siembra. — condicional a laboratorio |

---

## Lote Café

**Clasificación:** No apta · **Confianza:** 18% · **Lecturas:** 63 · **Reglas evaluadas:** 6

| Variable | Mediana | Mín | Máx |
|---|---|---|---|
| pH | 7.4 | 6.8 | 8.9 |
| CE (dS/m) | 0.071 | 0.049 | 0.28 |
| N (ppm) | 2 | 1 | 13 |
| P (ppm) | 5 | 3 | 19 |
| K (ppm) | 12 | 8 | 45 |

| Variable | Estado | Valor | Rango óptimo | Prioridad | Acción |
|---|---|---|---|---|---|
| pH | EXCESO | 7.4 | 5.5 – 6.5 | Critica | Ajustar pH al rango 5.5-6.5: encalado dolomítico si es ácido o yeso agrícola si es alcalino. |
| Nitrógeno (N) | DEFICIT | 2 | 200 – 400 | Alta | Nitrógeno fuera del rango objetivo (200-400): ajustar plan de fertilización nitrogenada fraccionada según Cenicafé. — condicional a laboratorio |
| Fósforo (P) | DEFICIT | 5 | 30 – 75 | Alta | Fósforo fuera del rango objetivo (30-75): aplicar DAP o roca fosfórica en hoyado o en banda. — condicional a laboratorio |
| Potasio (K) | DEFICIT | 12 | 100 – 300 | Alta | Potasio fuera del rango objetivo (100-300): aplicar KCl según la etapa del cultivo. — condicional a laboratorio |

---

## Conclusiones

1. **pH (confiable dentro del rango del sensor):** ambos lotes están alcalinos para su cultivo: fríjol 7.8 (óptimo 5.5–7.0) y café 7.4 (óptimo 5.5–6.5, crítico). El sensor mide de 3 a 9 pH (±0,3), por lo que los picos de 9,0/8,9 saturan su límite superior y son artefactos; el valor estable confiable ronda 7,1–7,8.
2. **CE (confiable, verificar unidades):** el sensor entrega µS/cm (0–10.000); el informe la expresa en dS/m (1 dS/m = 1.000 µS/cm). Los valores 0,05–0,08 dS/m = 50–80 µS/cm están muy por debajo del umbral de salinidad; sin riesgo de sales.
3. **N, P, K (indicativos, NO cuantitativos):** el sensor NPK tiene exactitud ±2% del fondo de escala (±~40 mg/kg), mayor que los propios valores (1–45 mg/kg). Sirven como señal relativa, no como medida absoluta; validar con análisis de laboratorio.

## Especificaciones del sensor y su efecto en el informe

| Especificación (JXBS-3001-NPK-RS, 7 en 1) | Implicación en el informe |
|---|---|
| pH: rango 3–9, exactitud ±0,3 | Lecturas ≥8,7–9,0 saturan el sensor; no son suelo real. El dato firme es 'alcalino ~7,1–7,8'. |
| CE: 0–10.000 µS/cm, resolución 10 µS/cm | Confirmar que 'dS/m' es la conversión correcta (÷1.000); valores <0,01 dS/m quedan bajo la resolución. |
| NPK: 0–1.999 mg/kg, exactitud ±2% F.S. | Error absoluto ~±40 mg/kg ⇒ los valores 1–45 mg/kg son solo indicativos. |
| Humedad y temperatura de SUELO (0–100%, −40–80 °C) | El sensor las mide, pero la BD las trae nulas; son justo las reglas faltantes de café (60–80% y 18–24 °C). |

