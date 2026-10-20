---
id: HU-03
type: Historia de Usuario
epic: 010
priority: Alta
points: 8
---

# HU-03: Transcripción de voz a texto en español con revisión

## Como
Productor o técnico de campo

## Quiero
Que mi dictado se convierta a texto en español y aparezca en el campo editable, sin enviarse automáticamente

## Para
Corregir lo que el sistema entendió antes de enviar la consulta

## Criterios de Aceptación
- [ ] CA1: La voz se transcribe a texto en español con precisión ≥ 90% en pruebas con vocabulario agronómico.
- [ ] CA2: Se usa transcripción híbrida: Web Speech API por defecto y endpoint en servidor como respaldo.
- [ ] CA3: La transcripción aparece en el campo de entrada, editable, y no se envía hasta confirmar.
- [ ] CA4: Si falla la transcripción, se muestra un mensaje claro y el usuario puede seguir escribiendo.
- [ ] CA5: La transcripción queda visible en un tiempo ≤ 5 s (p95) tras finalizar el dictado.

## Recurso de datos involucrado

### Recurso
- **Nombre:** ConsultaTranscrita (texto transitorio en el campo de entrada; no persiste)
- **Capa(s):** frontend

### Campos del recurso
| Campo | Tipo | Requerido | Descripción / Restricciones |
|---|---|---|---|
| texto_transcrito | texto | Sí | Resultado de la transcripción; editable por el usuario antes del envío |

### Relaciones con otros recursos
- Ninguna persistida. No especificado en la épica — definir con negocio si se requiere conservar borradores ante navegación o cierre de sesión.

## Subtareas
- [ ] Integrar Web Speech API con idioma español y captura de transcripciones intermedias.
- [ ] Integrar respaldo con el endpoint de transcripción en servidor cuando el navegador no soporte voz.
- [ ] Insertar la transcripción en el campo de entrada de forma editable, sin envío automático.
- [ ] Manejar errores de transcripción con mensaje claro y retorno al flujo escrito.
