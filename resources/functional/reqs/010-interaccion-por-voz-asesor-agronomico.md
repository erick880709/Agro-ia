---
id: 010
slug: interaccion-por-voz-asesor-agronomico
ia_cierre: 13/100
rondas: 2
estado: lista-para-diseno
fecha: 2026-10-19
---

# Interacción por voz en el Asesor agronómico

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EVOLUCIÓN DEL ÍNDICE DE AMBIGÜEDAD
 Ronda 0 (inicial): 45/100
 Ronda 1:           24/100
 Ronda 2:           13/100  ← CIERRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 RONDA 2 · ÍNDICE DE AMBIGÜEDAD: 13/100 · MUY BAJA
 Propósito y JTBD      [3/25]   [█░░░░░░░░░]
 Alcance y límites     [3/25]   [█░░░░░░░░░]
 Criterios de éxito    [3/20]   [██░░░░░░░░]
 Restricciones         [2/15]   [█░░░░░░░░░]
 Actores               [1/10]   [█░░░░░░░░░]
 Prioridad             [1/5]    [██░░░░░░░░]
```

## NECESIDAD DE NEGOCIO REFINADA

Permitir que los usuarios del Asesor agronómico de AgroIA interactúen mediante **voz**, además de la escritura: capturar el dictado, transcribirlo a texto en español (con vocabulario agronómico), permitir su revisión y edición, y enviarlo al chat existente como una consulta de texto — sin modificar la lógica del agente, con degradación elegante cuando la voz no esté disponible y con respuesta del asistente únicamente en texto.

**Fuente(s) de origen**
- `context/RFP-AGROIA-001_Interaccion_por_voz_Asesor_agronomico.md`
- `resources/functional/requests/RF-023 … RF-037` (15 RF)
- `resources/architecture/definitions/RNF-011 … RNF-023` (13 RNF)
- `resources/architecture/definitions/RT-017 … RT-019` (3 RT)
- `resources/design/models/RD-008-interaccion-de-voz-en-el-chat.md`

## Justificación

Hoy toda interacción con el Asesor agronómico exige escribir, lo que limita el uso a productores y técnicos de campo que operan desde el móvil, con guantes, a la intemperie o con poca familiaridad con el teclado. No resolverlo mantiene la barrera de adopción del asesor y reduce el valor de la pantalla de reportes.

## Actores

| Rol | Tipo | Responsabilidad |
|-----|------|-----------------|
| Productor / agricultor | Beneficiario · Ejecutor | Consulta su reporte por voz desde el móvil o el computador |
| Técnico / extensionista | Beneficiario · Ejecutor | Usa el chat en campo para orientar decisiones |
| Administrador | Aprobador · Ejecutor | Activa/desactiva la función, configura parámetros y consulta métricas |
| Asistente agronómico (sistema) | Sistema | Procesa la consulta de texto y responde, sin cambios |

## Alcance

✅ **IN SCOPE (Fase 1)**
- Botón de micrófono identificable junto al campo de texto, con estados **inactivo · grabando · procesando · error** e indicador de nivel de audio.
- Solicitud de permiso de micrófono solo al activar la función; orientación si fue denegado.
- Grabación con fin por silencio (2 s) o detención manual; **duración máxima de 60 s** configurable.
- Transcripción **híbrida (C)**: Web Speech API por defecto + transcripción en servidor como respaldo.
- Inserción **editable** de la transcripción (sin envío automático).
- Envío al endpoint de chat existente, conservando el contexto de finca/reporte.
- Comandos de control por voz: **“enviar”, “borrar”, “cancelar”, “repetir”** (solo si se pronuncian solos).
- Activación/desactivación administrativa desde **Administración → Parámetros**.
- Degradación elegante ante falta de soporte, permisos denegados, errores de transcripción y conectividad limitada.
- Métricas de uso agregadas (panel de administración) y matriz de pruebas por dispositivo/navegador.

❌ **OUT OF SCOPE (Fase 2)**
- Respuesta hablada del asistente (texto a voz).
- Conversación de voz continua o manos libres.
- Personalización de voces de salida.
- Cambios al motor de reglas, al agente o a la lógica de recomendaciones.
- Idiomas distintos del español.
- Aplicación móvil nativa.

## Criterios de Aceptación

```
DADO que el usuario abre un reporte y entra al Asesor agronómico con una finca seleccionada
CUANDO pulsa el botón de micrófono y concede el permiso
ENTONCES la interfaz muestra el estado "grabando" con indicador de nivel de audio

DADO que el usuario dicta su consulta en español
CUANDO detiene la grabación (manual o tras 2 s de silencio)
ENTONCES el sistema transcribe a texto (híbrido) y lo inserta en el campo editable sin enviarlo

DADO que la transcripción alcanza una precisión ≥ 90% con vocabulario agronómico
CUANDO el usuario revisa y pulsa Enviar (o dice "enviar")
ENTONCES la consulta se envía como texto al endpoint de chat existente, conservando el contexto
      de finca/reporte, y el asistente responde en texto

DADO que el usuario pronuncia "borrar", "cancelar" o "repetir" solos
CUANDO el sistema los reconoce
ENTONCES limpia el campo o reinicia la captura según el comando

DADO que el navegador no soporta captura de voz, el permiso es denegado, no hay conexión
      o falla la transcripción
CUANDO ocurre cualquiera de estos eventos
ENTONCES se muestra un mensaje claro y el flujo de escritura permanece disponible

DADO que el administrador desactiva la función en Administración → Parámetros
CUANDO un usuario abre el chat
ENTONCES el botón de micrófono se oculta o deshabilita en todos los clientes
```

## Restricciones y Supuestos

- **Restricciones:**
  - No almacenar grabaciones; descartar el audio al terminar la transcripción.
  - Transmisión de audio únicamente por canal cifrado (HTTPS).
  - Cumplimiento de la Ley 1581 de 2012 y de las políticas de privacidad de AgroIA.
  - Navegadores soportados: Chrome, Edge, Safari y Firefox (últimas 2 versiones estables).
  - Parámetros administrables (duración, activación, idioma), no fijos en código.
  - Accesibilidad: etiquetas aria y estados no dependientes solo del color; sin conformidad WCAG formal.
  - Presupuesto de transcripción: sin costo fijo; cuota mensual con alerta/desactivación al superarla.
- **Supuestos validados:** endpoint de chat estable y sin cambios; transcripción híbrida (C); experiencia Opción A.
- **Supuestos no validados:** ninguno bloqueante para Fase 1; detalles de diseño (iconografía, textos de ayuda exactos, versión TLS) se definen en la fase de interfaz/seguridad.

## Métricas de Éxito

| Métrica | Línea Base | Meta | Plazo |
|---------|-----------|------|-------|
| Precisión de transcripción (vocabulario agronómico) | 0% (no existe) | ≥ 90% | Al cierre de pruebas |
| Tiempo de transcripción visible | N/A | ≤ 5 s (p95) | Al cierre de pruebas |
| Disponibilidad del chat escrito ante fallo de voz | 100% funcional | 100% (sin regresión) | Continuo |
| Cobertura de matriz de pruebas | 0% | 100% de navegadores/dispositivos soportados | Al cierre de pruebas |
| Costo operativo de transcripción | N/A | Sin costo fijo; dentro de cuota mensual | Continuo |

## Prioridad (MoSCoW)

- **Must Have:** botón de micrófono + estados, permiso, grabación, transcripción en español, revisión/edición, envío al chat existente, contexto de finca/reporte, continuidad del chat escrito, degradación elegante, duración máxima configurable, no almacenamiento de audio.
- **Should Have:** comandos de control por voz (RF-08).
- **Could Have:** vocabulario agronómico reforzado (RF-13), métricas de uso (RF-14), activación administrativa (RF-15).
- **Won't Have (en este alcance):** respuesta hablada, conversación continua, otros idiomas, app nativa, cambios al agente.

## Dependencias

- **RF-014 (Agente conversacional IA)** y su endpoint de chat: permanecen estables y sin cambios.
- **RT-016 (Confirmación de arquitectura vigente):** validar en la Fase 0.
- **RT-019 (Parámetros administrables):** mecanismo de configuración alineado con la administración existente.
- **RNF-015 (Matriz de compatibilidad):** requiere la lista de navegadores confirmada.
- **RF-009 (Catálogo de cultivos):** fuente del vocabulario agronómico (RF-035).

---

**✅ Lista para diseño/estimación**
