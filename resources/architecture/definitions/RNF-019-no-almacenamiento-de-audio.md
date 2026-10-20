# RNF-019: No almacenamiento de grabaciones de audio

**Tipo:** Requerimiento no funcional
**Categoría:** Seguridad y privacidad
**Fuente:** RFP-AGROIA-001 — Secciones 10, 11 y 13

## Descripción
La plataforma no debe almacenar grabaciones. Si la transcripción se procesa en servidor, el audio debe descartarse al terminar la transcripción.

## Criterio medible / restricción concreta
No se deben conservar grabaciones; para procesamiento en servidor, el descarte ocurre al completar la transcripción.

## Impacto en la arquitectura
La solución debe evitar almacenamiento persistente y definir un ciclo de vida transitorio para el audio en cualquier componente de servidor.

## Notas del analista
El RFP no define retención de registros técnicos temporales ni mecanismos de verificación del borrado en proveedores externos.
