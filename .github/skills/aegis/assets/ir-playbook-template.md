# Playbook IR — <Tipo de incidente>

| Campo | Valor |
|---|---|
| ID / versión | PB-<NN> v<x.y> |
| Owner | <rol> |
| Última revisión / próxima | <fecha> / <fecha> |
| Marco | NIST SP 800-61r3 · SANS PICERL |
| Activos en alcance | <servicios, datos> |

## 1. Disparadores
- <alerta/umbral/fuente observable>

## 2. Severidad
| Nivel | Criterio | Tiempo de respuesta | Quién se activa |
|---|---|---|---|
| P1 | <…> | inmediato | IC + SOC + dueño + legal |
| P2 | <…> | 30 min | |
| P3 | <…> | 4 h | |
| P4 | <…> | 24 h | |

## 3. RACI
| Actividad | IC | SOC | Dueño servicio | Plataforma/Cloud | Legal/Cumplimiento | Comunicaciones | Proveedor |
|---|---|---|---|---|---|---|---|

## 4. Detección y triage
- [ ] <paso verificable: dónde mirar, con qué consulta/consola, qué confirma verdadero positivo>

## 5. Árbol de decisión
```
<árbol binario>
```

## 6. Contención
- Corto plazo: <acción, quién, cómo verificar>
- Largo plazo: <…>
- Preservación de evidencia: <qué, cómo, cadena de custodia>

## 7. Erradicación
- <causa raíz, remoción, verificación>

## 8. Recuperación
- <restauración, criterios de validación, monitoreo reforzado y duración>

## 9. Comunicación
| Audiencia | Cuándo | Canal | Responsable |
|---|---|---|---|
| Regulador / clientes | <plazo definido por cumplimiento> | | |

## 10. Post-incidente
- Reunión de lecciones aprendidas: <plazo>
- Hallazgos de código/IaC relacionados: <HS-xxx> · Requisitos: <SEC-xxx>
- Mejoras de detección: <regla/alerta>

## 11. Ejercicio
- Escenario tabletop: <…> · Criterio de éxito: <…> · Fecha: <…>
