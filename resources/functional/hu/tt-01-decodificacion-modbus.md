---
id: TT-01
type: Tarea Técnica
epic: RFP-AGROIA-003
priority: Alta
points: 8
---

# TT-01: Decodificación fiel Modbus JXBS-3001

## Descripción
Decodificar los registros 0x0006 (pH), 0x0012 (humedad), 0x0013 (temperatura), 0x0015 (CE) y 0x001E–0x0020 (N/P/K) con sus escalas; temperatura como entero de 16 bits con signo (complemento a dos). Guardar valor_crudo + valor_escalado + unidad; CE a dS/m y humedad como VWC.

## Criterios de Done
- [ ] 100 % de los vectores de prueba decodificados, incluida temperatura negativa.
- [ ] Cada lectura persiste valor_crudo, valor_escalado y unidad.

## Dependencias
- Ninguna

## Subtareas
- [ ] Mapear registros y escalas del sensor.
- [ ] Implementar temperatura en complemento a dos.
- [ ] Construir vectores de prueba propios.
