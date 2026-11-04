# 02 — Diseño de pruebas de rendimiento

## Contenido
1. Tipos de prueba
2. Modelo de trabajo (workload model)
3. Ley de Little: usuarios, throughput y tiempos
4. Think time y pacing
5. Modelo abierto vs cerrado
6. Criterios de aceptación (SLA/SLO)
7. Ambiente y datos
8. Plantilla de plan de prueba

---

## 1. Tipos

| Tipo | Pregunta | Perfil de carga |
|---|---|---|
| **Humo** (smoke) | ¿El script y el ambiente funcionan? | 1–5 usuarios, pocos minutos |
| **Carga** (load) | ¿Cumple el SLA con la carga esperada de pico? | Rampa → meseta en la carga objetivo (30–60 min) |
| **Estrés** (stress) | ¿Dónde se rompe y cómo falla? ¿Se recupera? | Escalones crecientes por encima del objetivo hasta degradación |
| **Picos** (spike) | ¿Aguanta subidas bruscas (cierre de mes, campaña)? | Base → salto súbito → base |
| **Resistencia** (soak/endurance) | ¿Se degrada con el tiempo (fugas de memoria, conexiones)? | Carga normal sostenida 4–24 h |
| **Capacidad** | ¿Cuánto soporta la infraestructura actual? | Escalones con medición de recursos |
| **Regresión de rendimiento** | ¿Empeoró tras un cambio? | Mismo perfil corto en cada release, comparado con la base |

Empieza siempre por humo. Nunca reportes un resultado de carga si la prueba de humo tenía errores.

## 2. Modelo de trabajo

Fuentes, en orden de preferencia: logs de acceso/APM de producción (hora pico real) → analítica de negocio → estimación de negocio documentada como supuesto.

Define:
- **Flujos de negocio** (consultar saldo, transferir, pagar) y su **mezcla** porcentual.
- **Ritmo objetivo**: transacciones por hora/segundo en el pico (no en el promedio diario).
- **Tiempos de reflexión** entre pasos.
- **Datos**: volumen y variedad (usuarios distintos, cuentas, rangos de montos).

Ejemplo (banca digital, hora pico):
| Flujo | Mezcla | Transacciones/h pico |
|---|---|---|
| Login + consulta de saldo | 60 % | 36 000 |
| Transferencia propia | 25 % | 15 000 |
| Pago de servicio | 15 % | 9 000 |

## 3. Ley de Little

**N = X × (R + Z)**
- N: usuarios concurrentes (hilos)
- X: throughput (iteraciones/s)
- R: tiempo de respuesta de una iteración (suma de los pasos)
- Z: tiempo de reflexión total de la iteración

Ejemplo: transferencia con 15 000 iteraciones/h = 4,17 it/s; R estimado 2 s (4 pasos × 0,5 s); Z = 4 pasos × 5 s = 20 s.
N = 4,17 × (2 + 20) ≈ **92 usuarios**.

Úsala en los dos sentidos: para calcular hilos y, tras la prueba, para **verificar** que el throughput logrado es coherente con los hilos y tiempos medidos. Si no cuadra, el generador o el modelo fallaron.

## 4. Think time y pacing

- **Think time**: pausa entre pasos (timers: Uniform/Gaussian Random Timer). Sin think time, 10 hilos generan la carga de cientos de usuarios reales y los resultados no representan a nadie.
- **Pacing**: tiempo fijo por iteración para lograr un ritmo exacto (Constant Throughput Timer / Precise Throughput Timer, o Open Model).
- Lo usual: think time realista + un timer de throughput para fijar el ritmo objetivo.

## 5. Modelo abierto vs cerrado

| | Cerrado (Thread Group clásico) | Abierto (Open Model Thread Group, 5.5+) |
|---|---|---|
| Qué fijas | Número de usuarios | Tasa de llegadas (req/s) |
| Si el sistema se pone lento | La carga baja sola (los hilos esperan) | Las llegadas siguen; se acumulan solicitudes |
| Representa | Usuarios internos, sesiones largas | APIs públicas, tráfico de internet |
| Riesgo | Esconde la saturación (*coordinated omission*) | Puede crecer sin límite de hilos si no se acota |

Para APIs expuestas a muchos clientes independientes, el modelo abierto describe mejor la realidad.

**Evidencia (validación de la skill)**: con 10 hilos en modelo cerrado y la misma duración, al añadir +250 ms a un solo endpoint el total de muestras cayó de **7 504 a 4 648 (−38 %)**. La carga "se autorreguló" a la baja justo cuando el sistema empeoró: en un modelo cerrado, revisa siempre si el throughput logrado alcanzó el objetivo antes de dar por buena una prueba.

## 6. Criterios de aceptación

Por transacción, no globales:
| Transacción | p95 | p99 | Errores | Throughput mínimo |
|---|---|---|---|---|
| Login | ≤ 800 ms | ≤ 1500 ms | < 0,5 % | 10/s |
| Transferencia | ≤ 1200 ms | ≤ 2500 ms | < 0,1 % | 4,2/s |

Más criterios de sistema: CPU < 70 % en el pico, sin crecimiento de memoria en la prueba de resistencia, pools de conexiones sin agotarse. Los criterios se codifican en `sla.json` y se validan automáticamente con `scripts/analizar_jtl.py` (07, 08).

## 7. Ambiente y datos

- Ambiente lo más parecido posible a producción (tamaño, configuración, versiones); documenta las diferencias y su impacto.
- Datos con volumen realista (una base vacía responde rápido y miente).
- Excluir o mockear dependencias externas no controladas (y declararlo).
- **Generadores fuera del sistema bajo prueba** y con capacidad comprobada (12).
- Monitoreo del servidor durante la prueba (APM, Prometheus/Grafana, Dynatrace): el JTL solo muestra el lado del cliente.
- Autorización explícita, ventana coordinada y criterio de aborto.

## 8. Plantilla de plan de prueba

```markdown
# Plan de prueba de rendimiento — <sistema> <versión>
- Objetivo: <pregunta concreta>
- Tipo: <carga | estrés | ...>
- Alcance: <flujos incluidos / excluidos>
- Modelo de trabajo: <tabla de mezcla + cálculo de Little>
- Perfil: <rampa, meseta, duración> (gráfico o tabla de escalones)
- Criterios de aceptación: <tabla por transacción + criterios de sistema>
- Ambiente: <descripción, diferencias con producción>
- Datos: <origen, volumen, preparación y limpieza>
- Monitoreo: <qué se mide en servidor>
- Supuestos y riesgos: <lista>
- Autorización y ventana: <responsables, fecha, criterio de aborto>
```
