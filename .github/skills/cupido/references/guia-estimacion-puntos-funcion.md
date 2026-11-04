# Guía de Estimación por Puntos de Función (Modo PF)

*Guía de referencia · Preventa y planeación de sprint*

Usa esta guía cuando cada HU/TT trae (o se le pueden contar) **Puntos de Función**. Es el modo más objetivo de esta skill: el tamaño funcional se mide con reglas estándar (IFPUG o COSMIC), no con juicio relativo del equipo, y la conversión a horas se apoya en una tasa de productividad (PDR, horas/PF) que se puede contrastar con benchmarks públicos y calibrar con datos propios.

## Contenido
1. Cuándo usar Modo PF
2. Medir: IFPUG por HU (y cuándo pasar a COSMIC)
3. Convertir: la fórmula
4. Tasa de productividad (PDR) — de dónde sale
5. Perfil de quien ejecuta
6. Factores de ajuste
7. Capacidad diaria real (jornada de 8,4 h)
8. Rango y compromiso
9. Ejemplo resuelto
10. Errores comunes

---

## 1. Cuándo usar Modo PF

- El backlog de `specter` o del cliente trae PF por HU, o el equipo puede contarlos.
- Se necesita una cifra defendible ante el cliente (el PF es auditable; el SP no).
- Se quiere comparar la propuesta con benchmarks de industria.

Si solo hay SP, usa Modo Backlog **con horas/SP calibradas** (ver `guia-calibracion-y-confianza.md`). Si solo hay la épica, usa Modo Épica y valida con PF como cruce (sección 5.4 de la guía SDD).

## 2. Medir: IFPUG por HU

| Función | Baja | Media | Alta |
|---|---:|---:|---:|
| EI — Entrada externa | 3 | 4 | 6 |
| EO — Salida externa | 4 | 5 | 7 |
| EQ — Consulta externa | 3 | 4 | 6 |
| ILF — Archivo lógico interno | 7 | 10 | 15 |
| EIF — Archivo de interfaz externa | 5 | 7 | 10 |

Reglas obligatorias al contar por HU:

- **Un ILF/EIF se cuenta una sola vez**, en la HU que lo crea o lo integra por primera vez. Las HU siguientes que lo usan solo suman sus transacciones. Registra en la tabla de salida en qué HU se contó cada archivo lógico.
- **Usa PF no ajustados (UFP).** El factor de ajuste de valor (VAF) de IFPUG es opcional desde la versión 4.3; la complejidad técnica se cubre con los factores de la sección 6, no con el VAF, para no contarla dos veces.
- **HU de menos de 5 PF:** IFPUG pierde precisión. Considera COSMIC (1 CFP por movimiento de datos: Entry, Exit, Read, Write), que se adapta mejor a historias pequeñas. No mezcles IFPUG y COSMIC en la misma propuesta sin declararlo.

## 3. Convertir: la fórmula

```
Horas equipo (sin PM) = PF × PDR × (1 − fracción PM) × Π factores de ajuste
Desarrollo            = Horas equipo × 51% × factor de perfil
QA / Arquitecto / UX  = Horas equipo × 25% / 9% / 15%
PM                    = Σ equipo × % según duración (guía top-down, sección 6)
```

El reparto 51/25/9/15 es el valor por defecto documentado; se sustituye por el reparto real del equipo en cuanto exista. El cálculo lo hace siempre `scripts/calcular_estimacion.py` (modo `pf`), nunca a mano.

**Por qué se descuenta el PM de la PDR:** los benchmarks de PDR incluyen gestión. Esta skill calcula PM de forma global por duración, así que la PDR se usa sin su fracción de gestión (12% por defecto) para no contarlo dos veces.

## 4. Tasa de productividad (PDR) — de dónde sale

Orden de preferencia (declara siempre cuál usaste):

1. **PDR propia del equipo/cliente**, calculada con horas reales de al menos 20–30 HU cerradas del mismo tipo de tecnología.
2. **PDR de un proyecto análogo de PersonalSoft** (mismo stack, mismo cliente o dominio).
3. **Benchmark público** — `references/evidencia-benchmarks.md`. Valor por defecto del script: **10 h/PF de ciclo completo**, dentro del rango de medianas observado (6–24 h/PF). Para dominios bancarios/regulados, el rango observado es 11–15 h/PF.

Ajustes conocidos por tamaño: los proyectos pequeños (<100 PF) tienen PDR más alta que los grandes (en el dataset China: 10,5 h/PF en <100 PF vs 4,9 h/PF en >1000 PF). Una HU es "pequeña" por definición, así que no uses PDR de proyectos grandes para estimar HU sueltas.

## 5. Perfil de quien ejecuta

El factor de perfil aplica **solo a las horas de desarrollo** y corresponde a **quien ejecuta la HU**, no a quien estima.

| Perfil que ejecuta | Factor |
|---|---:|
| Senior | 0,85 |
| Mixto / no definido | 1,00 |
| Semi-senior | 1,10 |
| Junior | 1,45 |

Cuando estima un senior para que ejecute otro perfil, el factor debe quedar explícito: el sesgo más común es estimar con la velocidad propia. En el dataset Project-22 el líder describe a su equipo como "optimistas eternos" y era quien empujaba a subir las estimaciones.

## 6. Factores de ajuste

Los PF miden tamaño funcional, no dificultad técnica. Usa **máximo 3–4 factores por HU**; con más, la estimación se vuelve arbitraria.

| Factor | Rango |
|---|---|
| Integraciones externas (APIs, legados, mainframe) | 1,00 – 1,30 |
| Seguridad / cumplimiento regulatorio (banca) | 1,00 – 1,25 |
| Tecnología nueva para el equipo | 1,00 – 1,30 |
| Reutilización de componentes existentes | 0,70 – 1,00 |
| Ambigüedad de la HU | 1,00 – 1,30 |

Cuando ya existe PDR propia calibrada, los factores deben bajar hacia 1,0: la tasa ya los absorbe. Si se mantienen altos, se está contando la complejidad dos veces.

## 7. Capacidad diaria real (jornada de 8,4 h)

Las horas de esfuerzo no dependen de la jornada; los **días calendario** sí.

```
Horas efectivas/día = jornada (8,4 h) × factor productivo (0,70–0,80; por defecto 0,75) = 6,3 h
Días de desarrollo  = horas de desarrollo ÷ (personas × horas efectivas/día)
Iteraciones         = días de desarrollo ÷ días hábiles por iteración (redondeo hacia arriba)
```

**No descuentes dos veces.** Si la PDR u horas/SP se calibraron con timesheet que imputa la jornada completa (reuniones incluidas), usa factor productivo 1,0 (`"horas_calibradas_con_timesheet_completo": true` en el script). Si se calibró con horas netas de desarrollo, usa 0,75.

## 8. Rango y compromiso

Nunca entregues un solo número. El script entrega optimista (P5), más probable, pesimista (P95), esperado y **comprometido (P80)** según la fase de definición (cono de incertidumbre). Con HU con PF contados, la fase por defecto es `diseno` (0,80×–1,25×). Ver `guia-calibracion-y-confianza.md`.

## 9. Ejemplo resuelto

HU "Registrar alerta de exposición": 1 EI media (4) + 1 EO media (5) + 1 EQ baja (3) = **12 PF**. Ejecuta un senior. Factores: integración API externa 1,15; seguridad banca 1,10.

- Equipo sin PM: 12 × 10 × 0,88 × 1,265 = 133,6 h
- Desarrollo: 133,6 × 0,51 × 0,85 = **57,9 h** (≈ 4,8 h/PF de construcción)
- QA 33,4 h · Arquitecto 12,0 h · UX/UI 20,0 h → **123,4 h de equipo** (PM se suma a nivel de propuesta)
- Días de desarrollo con 1 senior a 6,3 h efectivas: 57,9 ÷ 6,3 ≈ **9,2 días hábiles**

Salida completa: `examples/salida-ejemplo.json`.

## 10. Errores comunes

- Contar el mismo ILF en cada HU que lo toca.
- Aplicar el VAF y además los factores de ajuste (doble conteo de complejidad).
- Usar la PDR de ciclo completo como si fueran horas de desarrollo (o al revés).
- Aplicar factor senior cuando ejecutará otro perfil.
- Dividir las horas entre 8,4 como si toda la jornada fuera productiva.
- Usar PDR de proyectos grandes para HU pequeñas.
