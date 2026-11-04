# RF-057: Decodificación fiel

**Tipo:** Requerimiento funcional
**Fuente:** RFP-AGROIA-003 §6 (Requerimientos, Épica E1)
**Prioridad:** No especificada

## Descripción
El consumidor decodifica los registros Modbus 0x0006 (pH), 0x0012 (humedad), 0x0013 (temperatura), 0x0015 (CE) y 0x001E–0x0020 (N, P, K) con sus escalas; la temperatura se interpreta como entero de 16 bits con signo (complemento a dos). Se almacena `valor_crudo` (entero), `valor_escalado` y la unidad correspondiente.

## Actores involucrados
Consumidor IoT (apps/iot), firmware del ESP32

## Criterios de aceptación
100 % de los vectores de prueba decodificados correctamente, incluida temperatura negativa (§9).

## Dependencias / relacionados
RT-031 (especificaciones del sensor); depende de RF-059 (firmware) para el transporte de la trama.

## Notas del analista
Hoy no se guarda el valor crudo (H-12); conservarlo permite auditar errores de escala o signo.
