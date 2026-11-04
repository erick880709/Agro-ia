# Ubicación → suelo: qué se puede y qué no se puede inferir

## Principio
La altitud, la temperatura y la lluvia influyen en el suelo (meteorización, materia orgánica, lavado de bases, acidez), pero **el suelo también depende del material parental, la pendiente, la edad y el manejo**. Dos fincas a la misma altitud y con el mismo clima pueden tener suelos muy distintos. Por eso las coordenadas permiten formular una **hipótesis**, nunca un diagnóstico de nutrientes.

## Qué entrega cada fuente a partir de coordenadas
| Fuente | Da | No da |
|---|---|---|
| SoilGrids 2.0 (ISRIC, 250 m, modelo global) | pH, carbono orgánico, nitrógeno total, CEC, arcilla/arena/limo, a 0-5, 5-15 y 15-30 cm, con intervalo de incertidumbre (Q0.05–Q0.95) | P disponible, K, Ca, Mg, Al, micronutrientes; es una estimación estadística, con más incertidumbre donde hay pocas muestras (montaña tropical) |
| IGAC (estudios de suelos, geoportal datos abiertos agrología) | Unidades cartográficas de suelo, descripción de perfiles y análisis de laboratorio de los perfiles representativos | Valores de **tu lote**; escala semidetallada no sustituye análisis propio |
| Análisis de laboratorio del lote | Valores reales de pH, MO, P, K, Ca, Mg, Al, microelementos | — (es la única base válida para dosis) |

## Estado de la cartografía IGAC relevante (verificar vigencia)
- IGAC inició en septiembre de 2025 el estudio de suelos a escala 1:25.000 en 80 municipios cafeteros de Antioquia, Caldas y Risaralda (comunicado IGAC, 9-sep-2025).
- Ese comunicado menciona un acuerdo con la CRQ para un estudio a escala 1:10.000 en la zona productiva del Quindío (Armenia, La Tebaida, Montenegro, Quimbaya, Filandia y Circasia). Confirmar si ya hay resultados publicados.
- Portal de descarga: geoportal.igac.gov.co (datos abiertos, sección agrología) y colombiaenmapas.gov.co.

## Patrones geográficos generales (orientativos, por verificar con IGAC/Cenicafé)
- Zona cafetera central (Caldas, Risaralda, Quindío, norte del Tolima, norte del Valle): suelos derivados en buena parte de cenizas volcánicas; suelen tener alta materia orgánica y retención de fósforo. Cenicafé reporta contenidos de MO altos en estos suelos y ajusta las dosis de N según la MO.
- Laderas altas y frías: más lluvia/nubosidad y menor mineralización, acidez frecuente.
- Tierras bajas cálidas y húmedas (Pacífico, Amazonía, parte del Caribe): alta meteorización y lavado de bases, suelos ácidos y de baja fertilidad natural en muchas zonas.
- Valles secos y Caribe seco: pH más alto, menor lavado, riesgo de salinidad en zonas planas con riego.
*Estos patrones son hipótesis de partida; la skill debe presentarlos como tales y pedir análisis de suelo.*

## Cómo usarlo en la respuesta
1. Dar la ficha del sitio (coordenadas validadas, altitud, temperatura estimada, piso térmico).
2. Si hay SoilGrids: mostrar pH, MO y N con intervalo, explicando que es un modelo.
3. Formular hipótesis cualitativas (acidez probable, MO alta/baja) con la salvedad anterior.
4. Pedir análisis de suelo (pH, MO, P, K, Ca, Mg, Al, CIC y microelementos relevantes al cultivo) antes de cualquier plan de fertilización.
5. Remitir a IGAC para la unidad cartográfica del predio y a Cenicafé/AGROSAVIA/UPRA según el cultivo.
