# Guía de Rango de Confianza y Calibración

*Cómo pasar de "un número" a "un rango con compromiso", y cómo mejorar la precisión con datos reales.*

## 1. Cono de incertidumbre → fase de definición

La fase de definición se elige según el insumo disponible y fija el ancho del rango. El script la interpreta como percentiles P5 y P95 de una distribución **log-normal** (la forma que mejor describe el esfuerzo real de software: cola larga a la derecha).

| Fase (`fase_definicion`) | Insumo típico en este ecosistema | Optimista | Pesimista | Buffer implícito P80 |
|---|---|---:|---:|---:|
| `concepto` | Necesidad cruda, sin `epicureo` | 0,50× | 2,00× | ≈ 43% |
| `requerimientos` | Épica refinada por `epicureo` (Modo Épica) | 0,67× | 1,50× | ≈ 23% |
| `diseno` | Backlog de `specter` o HU con PF contados | 0,80× | 1,25× | ≈ 12% |
| `listo` | HU refinada con spec SDD aprobada | 0,90× | 1,10× | ≈ 5% |

Los buffers implícitos coinciden en orden de magnitud con la tabla de buffers de la versión anterior (15/25/35–40%), así que la tabla sigue siendo válida como regla rápida, pero ahora está anclada a la madurez del insumo.

## 2. Qué se presenta al cliente

| Cifra | Uso |
|---|---|
| **Más probable** | Referencia interna, planeación del squad |
| **Esperado (media)** | Comparación entre escenarios (tradicional vs IA) |
| **Comprometido (P80)** | Cifra de la propuesta comercial y del costo |
| Optimista / Pesimista | Contexto de riesgo, nunca como compromiso |

Regla: **el costo de la propuesta se calcula sobre P80**, no sobre el más probable.

Por qué P80 a nivel proyecto y no a nivel tarea: en el dataset SiP el P80 por tarea es 1,5×–2× el estimado, pero en agregado la sobrecarga es 1,3×. Las desviaciones de tareas individuales se compensan parcialmente en el total.

## 3. Registro de reales (obligatorio para calibrar)

Por cada HU/TT cerrada, registra en `resources/estimation/actuals-log.csv`:

```
id,modo,pf,sp,tipo_sdd,perfil,horas_estimadas_dev,horas_reales_dev,horas_estimadas_equipo,horas_reales_equipo,uso_ia(si/no),notas
```

Si el registro vive en Jira o en una hoja del cliente, guarda la referencia en vez de copiar los datos.

## 4. Métricas de precisión

```
PRED(25) = % de ítems con |real − estimado| / estimado ≤ 25%
Sesgo    = mediana(real / estimado)
```

| PRED(25) | Lectura | Acción |
|---|---|---|
| < 50% | Pobre | Recalibrar cada sprint; revisar PDR y factores |
| 50–65% | En desarrollo | Recalibrar cada 2 sprints; atacar el tipo de HU con peor desvío |
| 65–75% | Bueno | Recalibrar mensualmente |
| > 75% | Excelente | Recalibrar trimestralmente |

Referencia: en SiP solo el 45% de tareas humanas cae dentro de ±25%. Llegar a PRED(25) ≥ 65% ya es mejor que la media de la industria.

## 5. Reglas de ajuste

Tras al menos 10 ítems cerrados:

| Patrón | Ajuste |
|---|---|
| Sesgo > 1,2 sostenido | Subir PDR (o h/SP) del tipo afectado |
| Sesgo < 0,8 sostenido | Bajar PDR (o h/SP) |
| Un tipo SDD sistemáticamente fuera | Ajustar solo ese factor SDD |
| Ahorro IA real < estimado | Bajar el factor de generación y revisar el decaimiento por tamaño |
| Factores de ajuste siempre altos | La PDR base está baja; subirla y devolver factores a ~1,0 |

- Cambios pequeños: **nunca más de 20% por ciclo** en un parámetro.
- Recalcula la PDR propia como `Σ horas reales ÷ Σ PF` por tipo de tecnología, no como promedio de cocientes.
- Mantén una **biblioteca de historias de referencia** (una por tamaño y tipo, con horas reales) para anclar estimaciones nuevas por analogía.

## 6. Guardas anti-patrón (el script las emite como advertencias)

- Talla XL o SP ≥ 13 → descomponer o Spike antes de comprometer.
- HU < 5 PF con IFPUG → considerar COSMIC.
- Pesimista/optimista > 3× → refinar antes de comprometer.
- Duración > 6 meses → PM dedicado y entregas por fases con reestimación.
- Fase `concepto` → presentar solo como ROM.
