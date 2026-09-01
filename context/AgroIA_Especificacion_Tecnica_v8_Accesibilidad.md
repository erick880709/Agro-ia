# AgroIA — Especificación Técnica v8
### Accesibilidad y lenguaje simple del reporte para usuarios no agrónomos
**Fecha:** 2026-09-01 · **Basado en:** revisión del reporte `Finca Demo — El Vergel` (01/09/2026) · **Autor:** Revisión de comunicación/UX + agronomía

---

## 0. Principio rector

Todo lo de este documento es **cambio de presentación (copy, orden, visibilidad de detalle)**, no cambio de cálculo ni de datos. Ningún hallazgo de este documento modifica el motor de reglas, el pipeline de recomendación ni los contratos de API ya existentes — se trata de **cómo se muestra** la misma información, no de qué información se genera. Esto significa que, a diferencia de las especificaciones anteriores, la mayoría de los cambios son de plantilla de reporte (HTML) y, cuando aplica, de una pequeña extensión al diccionario de "lenguaje de campo" que el sistema ya usa en la sección 03.

**Regla de no regresión:** ningún cambio de esta especificación puede reducir el detalle técnico disponible para quien lo necesita — donde se propone ocultar o reordenar, es **condicional a la audiencia del reporte** (sección 0.1), nunca una eliminación de información.

---

## 0.1 Audiencia del reporte ≠ rol de sesión — distinción necesaria antes de implementar

**Corrección respecto a la versión anterior de este documento:** los hallazgos H3 y H6 (y ahora también H2) no pueden condicionarse únicamente al **rol de la persona logueada**, porque el reporte tiene dos modos de consumo distintos:

1. **Vista en vivo dentro de la app** (autenticada): aquí sí aplica el rol de sesión — un Agrónomo navegando el dashboard ve la versión técnica, un Cliente ve la versión simple.
2. **Exportación estática** (`🖨 Guardar PDF` / `⬇ Descargar HTML`, y el envío por WhatsApp ya especificado en la v4): el archivo resultante es fijo y frecuentemente **lo genera una persona pero lo termina leyendo otra** — el caso más común es un Agrónomo o Extensionista generando el reporte para entregárselo al agricultor. Si el PDF se genera con el rol de sesión de quien lo exporta, el agricultor recibiría la versión técnica aunque el propósito del documento sea que él la entienda.

**Regla de cierre:** se introduce el concepto de **audiencia efectiva**, que reemplaza a "rol de sesión" como criterio de condicionamiento en toda esta especificación:

```
audiencia_efectiva =
  si es vista en vivo dentro de la app  → rol de sesión del usuario autenticado
  si es exportación (PDF/HTML/WhatsApp) → selección explícita de audiencia en el momento
                                            de exportar, con "Agricultor" (no técnica)
                                            como valor por defecto, y "Agrónomo" (técnica)
                                            disponible como toggle en el mismo botón de
                                            exportar
```

Se elige "Agricultor" como valor por defecto en la exportación (y no "según mi rol") porque el caso de uso más frecuente es un agrónomo exportando *para* un tercero no técnico — ese es el camino de menor fricción, y el agrónomo que exporte para su propio archivo técnico solo necesita un clic adicional en el toggle.

**Nota de alcance:** esto no requiere un selector de audiencia por cada campo individual — es **una sola decisión al momento de exportar**, que se propaga a H2, H3 y H6 de forma consistente (secciones 2 y 3, actualizadas más abajo).

---

## 1. Diagnóstico (resumen)

El reporte ya resuelve bien el problema central: la sección 03 "En palabras del campo" traduce el diagnóstico técnico a lenguaje llano y funciona. El problema es de **consistencia**: esa traducción no cubre todo el reporte, y hay puntos donde el diseño visual comunica lo contrario de lo que significa. Se identificaron 6 hallazgos, con impacto ordenado de mayor a menor.

---

## 2. Hallazgos y especificación de cierre

### H1 — El semáforo de confianza puede comunicar lo contrario de lo que significa [Alta]

**Problema:** la barra `🔴 Violaciones activas: 100%` se lee, por color y número, como "algo está mal al 100%", cuando el valor alto probablemente representa "sin violaciones = puntaje limpio". La codificación de color no es consistente con el significado en las 4 barras del semáforo.

**Especificación de cierre:**
1. Renombrar la barra a una redacción que no dependa de interpretar si "alto es bueno o malo": en vez de `Violaciones activas: 100%`, usar `Sin violaciones activas: 100%` (mover la negación al título, no dejar que el número la implique).
2. Agregar un texto de una línea debajo de cada barra explicando qué significa un valor alto, ej.:
   - `🟢 Calibración del sensor — 100%: el sensor está calibrado y validado en laboratorio.`
   - `🟡 Cobertura de fertilidad — 100%: se cuenta con todas las variables de fertilidad necesarias.`
   - `🔴 Sin violaciones activas — 100%: no hay alertas críticas pendientes en este momento.`
   - `🟣 Respaldo humano — 0%: todavía ningún agrónomo ha confirmado esta recomendación.`
3. **Criterio de aceptación:** una persona sin contexto técnico, viendo solo el color y el texto (sin necesidad de deducir la lógica), debe poder identificar correctamente si cada barra es una buena o mala noticia.

### H2 — "Próximos pasos" usa siglas sin traducir, justo en la sección de acción [Alta]

**Problema:** `Completar las variables de fertilidad faltantes (MO, CIC, Ca, Mg, S, Fe, Mn, Zn, Cu, B)` — mientras que la sección 03 sí traduce variables como "humedad" a lenguaje simple, esta lista de siglas no pasa por el mismo diccionario.

**Corrección respecto a la versión anterior:** este hallazgo se dejó sin condicionar por audiencia, lo cual penaliza al agrónomo — para quien leer `Ca, Mg, S` de un vistazo es más rápido que procesar una frase completa cada vez que revisa un reporte. Se corrige para que la traducción aplique solo donde aporta, no siempre.

**Especificación de cierre:**
1. Reutilizar el mismo diccionario de "lenguaje de campo" ya usado en la sección 03 (que ya mapea `humedad → "El agua que guarda el suelo para la planta"`, etc.) para renderizar también esta lista de "próximos pasos" — no se crea un diccionario nuevo, se extiende el uso del existente a esta sección.
2. **Condicional a la audiencia efectiva (sección 0.1):**
   - **Audiencia Agricultor:** reemplazar la lista de siglas por su nombre en palabras simples, con la sigla entre paréntesis solo como referencia:
     - Antes: `MO, CIC, Ca, Mg, S, Fe, Mn, Zn, Cu, B`
     - Después: `materia orgánica (MO), capacidad de retener nutrientes del suelo (CIC), calcio (Ca), magnesio (Mg), azufre (S), y los micronutrientes hierro, manganeso, zinc, cobre y boro`
   - **Audiencia Agrónomo:** se mantiene el formato compacto actual (`MO, CIC, Ca, Mg, S, Fe, Mn, Zn, Cu, B`), sin cambios — regla de no regresión.
3. **Criterio de aceptación:** en audiencia Agricultor, ningún ítem de "Próximos pasos" muestra una sigla técnica como primera palabra sin traducción al lado; en audiencia Agrónomo, el formato compacto se conserva idéntico al actual.

### H3 — Telemetría técnica sin explicación puede generar alarma innecesaria [Media]

**Problema:** `RSSI — dBm`, `Uptime 0 min` son datos de diagnóstico de red, no de la finca — para un agricultor pueden leerse como "el aparato está fallando".

**Especificación de cierre (usa audiencia efectiva, sección 0.1, no rol de sesión directamente):**
1. Cuando la audiencia efectiva es **Agricultor** (vista en vivo de un usuario Cliente, o exportación con audiencia Agricultor), estos campos (`RSSI`, `Uptime`) se colapsan por defecto bajo un enlace "Ver detalle técnico del sensor ▾", visible pero no expandido.
2. Cuando la audiencia efectiva es **Agrónomo** (vista en vivo de Admin/Agrónomo/Extensionista, o exportación con el toggle técnico activado), se mantienen visibles como hoy — regla de no regresión.
3. **Criterio de aceptación:** un reporte con audiencia efectiva Agricultor no muestra `RSSI`/`Uptime` en el primer scroll, sin importar si esa audiencia vino del rol de sesión o de una exportación explícita; sigue disponible a un clic de distancia.

### H4 — El mapa de calor no tiene puente hacia lenguaje simple [Media]

**Problema:** la cuadrícula con notación `0/1`/`1/1` ("variables fuera del ideal / variables con regla") requiere alfabetización de datos que no todo usuario tiene.

**Especificación de cierre:**
1. Anteceder el bloque del mapa de calor con una frase-resumen calculada a partir de los mismos datos que ya alimentan la cuadrícula (no requiere cálculo nuevo, solo agregación de lo existente):
   > `De los 26 puntos que se midieron en su lote, X presentan alguna variable fuera de lo ideal.`
2. El mapa de calor visual se mantiene igual, sin cambios — este es un texto adicional antes, no un reemplazo.
3. **Criterio de aceptación:** la frase-resumen aparece siempre que el bloque del mapa de calor se renderiza, para todos los roles.

### H5 — Duplicación de números que confunde por redundancia [Baja]

**Problema:** `confianza 95% (real 95%)` — mostrar el mismo número dos veces genera la pregunta de por qué hay dos si son iguales.

**Especificación de cierre:**
1. Regla de plantilla: si `confianza_base == confianza_real`, mostrar solo `confianza 95%`.
2. Si difieren, mantener el formato actual `confianza {base}% (real {real}%)`, que sí aporta información cuando los valores son distintos.
3. **Criterio de aceptación:** ningún reporte muestra el mismo porcentaje repetido entre paréntesis.

### H6 — Orden de lectura: lo más simple está en el medio del reporte, no al principio [Media]

**Problema:** para el rol Cliente, las secciones técnicas (01 Diagnóstico, 02 Ranking con motor de reglas) preceden a la sección 03 "En palabras del campo", que es la más accesible.

**Especificación de cierre:**
1. **Reordenamiento condicional por audiencia efectiva** (sección 0.1 — no por rol de sesión directamente, ya que este es precisamente el hallazgo donde más importa la diferencia entre "quién genera" y "quién lee" el reporte):
   - **Audiencia Agricultor** (vista en vivo Cliente, o exportación por defecto): orden del reporte = `Resumen en palabras del campo → Próximos pasos → Diagnóstico técnico (01) → Ranking (02) → Mapa de calor (M) → Advertencias (04)`.
   - **Audiencia Agrónomo** (vista en vivo Admin/Agrónomo/Extensionista, o exportación con el toggle técnico activado): se mantiene el orden técnico actual (01 → 02 → M → 03 → 04 → 05), sin cambios — regla de no regresión.
2. La numeración de secciones (01, 02, M, 03, 04, 05) se conserva igual en ambos casos — solo cambia el orden de aparición en la página, no los identificadores, para no romper referencias cruzadas ni el PDF generado.
3. **Criterio de aceptación:** un reporte con audiencia efectiva Agricultor —sin importar si esa audiencia vino de la sesión de un Cliente o de la exportación hecha por un Agrónomo para un tercero— muestra el bloque de lenguaje simple y el plan de acción antes que cualquier tabla con jerga técnica (siglas, "motor de reglas", semáforo de confianza).

---

## 3. Resumen de cambios por tipo (para estimar esfuerzo)

| Tipo de cambio | Hallazgos | Complejidad |
|---|---|---|
| Copy/texto (solo redacción, sin lógica) | H1 (texto de barras) | Baja — cambio de plantilla/diccionario |
| Lógica de plantilla condicional por **audiencia efectiva** (sin cálculo nuevo) | H2 (traducción de siglas), H3 (colapsar telemetría), H5 (mostrar un número o dos), H6 (reordenar secciones) | Baja-Media — condicionales sobre datos ya existentes, ahora resueltos por audiencia efectiva (0.1) en vez de solo rol de sesión |
| Agregación de datos ya existentes (sin nuevo endpoint) | H4 (frase-resumen del mapa de calor) | Baja — cuenta sobre los mismos puntos que ya alimentan la cuadrícula |
| UI nueva, pequeña, sin persistencia | Selector de audiencia al exportar (sección 0.1) | Baja — un toggle de dos opciones junto a los botones `🖨 Guardar PDF` / `⬇ Descargar HTML` ya existentes; opcionalmente, guardar la última preferencia de audiencia por agrónomo es una mejora futura, no un requisito de esta entrega |

**Ningún hallazgo de este documento requiere migración de base de datos, endpoint nuevo, ni cambio en el motor de reglas o en el ML.** Es la especificación de menor riesgo técnico de toda la serie — el trabajo es enteramente de presentación, incluyendo el selector de audiencia (que es un parámetro de render, no un dato persistido).

---

## 4. Checklist de QA para el cierre

- [ ] **0.1** — Confirmar que existe el selector de audiencia (Agricultor/Agrónomo) junto a los botones de exportar, con "Agricultor" como valor por defecto
- [ ] **0.1** — Confirmar que la vista en vivo dentro de la app sigue usando el rol de sesión (sin selector adicional) y que solo la exportación requiere la elección explícita
- [ ] H1 — Verificar que las 4 barras del semáforo tengan texto explicativo y que ninguna combinación color+valor se preste a lectura ambigua (aplica a ambas audiencias)
- [ ] H2 — Confirmar que "Próximos pasos" traduce las siglas solo en audiencia Agricultor, y conserva el formato compacto en audiencia Agrónomo
- [ ] H3 — Confirmar que RSSI/Uptime están colapsados por defecto solo en audiencia Agricultor, visibles sin cambios en audiencia Agrónomo
- [ ] H4 — Confirmar que la frase-resumen del mapa de calor aparece en todos los reportes, con el conteo correcto de puntos fuera de lo ideal (aplica a ambas audiencias)
- [ ] H5 — Confirmar que no se duplica el mismo porcentaje de confianza cuando base y real coinciden (aplica a ambas audiencias)
- [ ] H6 — Confirmar el nuevo orden de secciones solo en audiencia Agricultor; confirmar que audiencia Agrónomo no tiene ningún cambio de orden
- [ ] **Caso crítico a probar explícitamente:** un Agrónomo exporta un reporte sin tocar el selector → el PDF/HTML resultante debe salir en audiencia Agricultor (valor por defecto), no en la audiencia de su propio rol de sesión

---

## 5. Nota de cierre

Esta especificación es deliberadamente distinta en naturaleza a las anteriores (v3–v7): no añade capacidad al sistema, **hace que la capacidad que ya existe llegue de verdad a quien más la necesita** — el agricultor que abre el reporte sin formación técnica. Es, en ese sentido, la especificación más directamente alineada con el objetivo original de AgroIA: ser el puente entre el dato de suelo y una decisión que la persona pueda entender y tomar con confianza.
