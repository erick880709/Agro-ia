---
id: 012
slug: plataforma-confiable-medicion-suelo
ia_cierre: 15/100
rondas: 2
estado: lista-para-diseno
fecha: 2026-11-03
---

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EVOLUCIÓN DEL ÍNDICE DE AMBIGÜEDAD
 Ronda 0 (inicial): 38/100
 Ronda 1:           20/100
 Ronda 2:           15/100  ← CIERRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

# NECESIDAD DE NEGOCIO REFINADA

Convertir AgroIA en una **plataforma confiable de medición de suelo**, donde cada lectura del sensor JXBS-3001-NPK-RS que alimenta un reporte o recomendación tenga **origen trazable, calidad evaluada (motor de 10 estados), incertidumbre explícita propagada a reglas y reportes, calibración local contra laboratorio acreditado y un grado de evidencia (A/B/C/D)** que limite lo que se puede concluir con ella, sin emitir dosis ni clasificaciones definitivas sin análisis de suelo.

**Fuente(s) de origen**
- `resources/summary/executive-summary-rfp-agroia-003.md`
- 36 RF (RF-057…RF-092) · 6 RNF (RNF-033…RNF-038) · 4 RT (RT-031…RT-034) · 2 RD (RD-011…RD-012)

**Justificación**
Hoy el sistema trata cada lectura como un valor exacto y equivalente a un análisis de laboratorio, cuando el sensor es un instrumento de **tamizaje**: mide 7 de 18 variables, N/P/K con ±40 mg/kg (del mismo orden que los valores reales) y sin equivalencia a Bray II / K intercambiable. El costo de no resolverlo: recomendaciones erróneas, falsa confianza cerca de umbrales, y mapas/promedios no representativos.

**Actores**

| Rol | Tipo | Responsabilidad |
|-----|------|-----------------|
| Equipo agronómico (agrónomo/extensionista) | Aprobador | Valida umbrales, metas de calibración y protocolos de campo |
| Técnico de campo | Ejecutor | Muestreo puntual, instalación de sensores, registro de contexto |
| Administrador de plataforma | Ejecutor | Gestiona parámetros de calidad y salud de sensores |
| Científico de datos (ML) | Ejecutor | Entrena modelos solo con etiquetas de laboratorio |
| Cliente (AgroIA) | Aprobador / Beneficiario | Prioriza y valida el cierre |
| Laboratorio acreditado (AGROSAVIA Tibaitatá 13-LAB-031) | Proveedor externo | Referencia analítica de la campaña |

**Alcance**

- ✅ IN SCOPE: integridad de ingesta (E1), motor de calidad (E2), incertidumbre y clasificación (E3), calibración local (E4), muestreo y contexto (E5), grados de evidencia (E6), reportes/UI (E7), ciclo de vida del sensor (E8), ML con etiquetas de laboratorio (E9); modelo de datos ampliado (RD-011) y lineamientos de UI (RD-012).
- ✅ Esquema de instalación **mixto**: muestreo puntual con sonda de mano (calibración/reportes) + 2–3 estaciones centinela enterradas por unidad de suelo (series de humedad/temperatura).
- ✅ Unidades de suelo por fases: andisoles del Eje Cafetero → suelos ácidos arcillosos (oxisoles/ultisoles) → aluviales. Arenosos y salinos: humedad **no aplicable** en esta etapa.
- ✅ Profundidad: 0–20 cm por defecto; 20–40 cm para perennes de raíz profunda (parámetro por cultivo; café 20 cm en el plato del árbol).
- ❌ OUT OF SCOPE: reemplazo del sensor, nuevos tipos de sensor, recetas de dosis sin laboratorio, rediseño del asesor conversacional, calibración de suelos arenosos/salinos.

**Criterios de Aceptación**

```
DADO un vector de prueba con temperatura negativa (complemento a dos)
CUANDO el consumidor lo decodifica
ENTONCES interpreta el signo correcto y guarda valor_crudo + valor_escalado

DADO una lectura de pH 5,4 contra un umbral de 5,5 (exactitud ±0,3)
CUANDO se clasifica
ENTONCES se informa "indeterminada (frontera)" con probabilidad por clase

DADO un reporte generado
CUANDO se revisa
ENTONCES no contiene lecturas invalidada/saturada/humedad_insuficiente
  y declara grados de evidencia y variables no medidas

DADO una variable sin calibración local vigente
CUANDO alimenta el motor de reglas
ENTONCES queda en grado C y no produce dosis ni clasificación definitiva

DADO una reclasificación histórica
CUANDO se ejecuta por lotes
ENTONCES no se pierde ningún registro y conserva la versión de regla vigente
```

**Restricciones y Supuestos**

- **Restricciones:** sin análisis de suelo no hay dosis; todo umbral/rango/tolerancia es parámetro administrable (no fijo en código); el valor crudo se conserva siempre; laboratorio único acreditado con métodos Cenicafé/IGAC (pH 1:1, MO Walkley-Black, N Kjeldahl, P Bray II, Ca/Mg/K/Na acetato de amonio 1N pH 7, CIC, Al si pH≤5,5, textura, humedad gravimétrica × densidad aparente, CE con curva 1:5 y CEe, submuestra nitrato/amonio); variante de sensor 12 V DC con transceptor RS485; se mantienen RLS, roles y auditoría.
- **Supuestos validados:** metas de calibración **duras** (si no se cumplen, la variable queda en grado C); esquema mixto; prioridad crítica.
- **Supuestos no validados:** línea base cuantitativa desconocida (se medirá como entregable de fase 0); referencia exacta del sensor por confirmar con etiqueta física; método definitivo de CE por acordar con el laboratorio.

**Métricas de Éxito**

| Métrica | Línea Base | Meta | Plazo |
|---------|-----------|------|-------|
| Vectores de prueba decodificados (incl. temp. negativa) | Sin vectores hoy | 100 % | Fase 0/1 |
| Lecturas inválidas/saturadas/humedad_insuficiente en reportes | >0 hoy | 0 | Fase 2 |
| pH: sesgo / RMSE vs pH agua 1:1 | Por medir | ≤0,3 / ≤0,4 | Fase 3 |
| Humedad: RMSE vs gravimétrico × Da | Por medir | ≤5 ptos VWC | Fase 3 |
| CE: R² vs CE 1:5 / CEe | Por medir | ≥0,8 | Fase 3 |
| N/P/K: R² en el rango del suelo | Por medir | ≥0,6 (o grado C) | Fase 3 |
| Pares sensor–laboratorio | 0 hoy | ≥30 por unidad y variable | Fase 3 |

**Prioridad (MoSCoW)**

- **Must Have:** F0 verificación de variante, F1 integridad (E1, E2), F2 incertidumbre (E3) y grados de evidencia (E6).
- **Should Have:** F3 calibración + campaña de campo (E4, E5).
- **Could Have:** F5 ciclo de vida (E8) y ML (E9), incrementales.
- **Won't Have (este alcance):** reemplazo de sensor, rediseño del asesor, calibración de arenosos/salinos.

**Dependencias**

- Contratación del laboratorio acreditado ONAC (condiciona la fase 3).
- Fase 0 (verificación de variante) antes de E1.
- Datos SIG IGAC/UPRA para las unidades de suelo.
- Módulo de costos (comisión de muestreo en grilla) para RF-083.
- Costo externo de la campaña de laboratorio (no presupuestado en el RFP).
