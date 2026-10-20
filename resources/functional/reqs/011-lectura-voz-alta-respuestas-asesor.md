---
id: 011
slug: lectura-voz-alta-respuestas-asesor
ia_cierre: 14/100
rondas: 1
estado: lista-para-diseno
fecha: 2026-10-19
---

# Lectura en voz alta de las respuestas del Asesor agronómico

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 EVOLUCIÓN DEL ÍNDICE DE AMBIGÜEDAD
 Ronda 0 (inicial): 38/100
 Ronda 1:           14/100  ← CIERRE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 RONDA 1 · ÍNDICE DE AMBIGÜEDAD: 14/100 · MUY BAJA
 Propósito y JTBD      [4/25]   [██░░░░░░░░]
 Alcance y límites     [3/25]   [█░░░░░░░░░]
 Criterios de éxito    [3/20]   [██░░░░░░░░]
 Restricciones         [2/15]   [█░░░░░░░░░]
 Actores               [1/10]   [█░░░░░░░░░]
 Prioridad             [1/5]    [██░░░░░░░░]
```

## NECESIDAD DE NEGOCIO REFINADA

Permitir que los usuarios del Asesor agronómico **escuchen** las respuestas leídas en voz alta — apagado por defecto, con activación persistente por cuenta, selección de voz (femenina, masculina o su propia voz clonada) y control de reproducción y velocidad — sin alterar la respuesta escrita ni el agente.

**Fuente(s) de origen**
- `resources/functional/requests/RF-038 … RF-056` (19 RF)
- `resources/architecture/definitions/RNF-024 … RNF-032` (9 RNF)
- `resources/architecture/definitions/RT-020 … RT-030` (11 RT)
- `resources/design/models/RD-009 … RD-010` (2 RD)

## Justificación

Muchos usuarios son productores y técnicos que trabajan en campo, con las manos ocupadas, bajo el sol o con poca costumbre de leer textos largos en pantalla. Escuchar la respuesta mejora accesibilidad y comprensión, y es el complemento natural de la entrada por voz (RFP-AGROIA-001): juntas habilitan una conversación hablada completa.

## Actores

| Rol | Tipo | Responsabilidad |
|-----|------|-----------------|
| Productor / agricultor | Beneficiario · Ejecutor | Escucha respuestas; elige voz y activa/desactiva la lectura |
| Técnico / extensionista | Beneficiario · Ejecutor | Usa la lectura en campo sin mirar la pantalla |
| Administrador | Aprobador · Ejecutor | Configura motores, límites, activación general y consulta métricas |
| Asistente agronómico | Sistema | Genera la respuesta de texto que se convierte en audio |

## Alcance

✅ **IN SCOPE**
- **Fase 1 (obligatoria):** interruptor persistente por cuenta; selector de voz femenina/masculina con "Escuchar muestra"; lectura automática (apagada por defecto) y manual (botón altavoz); controles reproducir/pausar/detener/repetir; control de velocidad (0,75x–1,5x); limpieza del texto para lectura natural (unidades agronómicas); detención automática al apagar/enviar/salir; conmutación a motor de respaldo; estado visible (preparando/reproduciendo/error). Lectura **completa** de la respuesta.
- **Cadena de motores:** `speechSynthesis` por defecto → nube con capa gratuita (Google TTS/Azure) → Piper (contingencia).
- **Fase 2 (voz personalizada):** solo la **propia voz** del usuario; flujo guiado con consentimiento y verificación; motores GPT-SoVITS y Chatterbox (MIT) en GPU cloud; previsualizar, regrabar, desactivar y eliminar; "Mi voz" como opción condicional.
- Activación administrativa y límites; métricas de uso sin audio; integración conjunta con RFP-001.

❌ **OUT OF SCOPE**
- Cambios al agente o a las reglas UPRA/Cenicafé/AGROSAVIA.
- Conversación de voz en tiempo real con interrupciones.
- Idiomas distintos del español.
- Clonación de voces de terceros o de personas públicas.
- Aplicación móvil nativa.

## Criterios de Aceptación

```
DADO que el usuario activa "Leer respuestas en voz alta" y elige una voz
CUANDO el asistente genera una nueva respuesta
ENTONCES la aplicación la lee en voz alta y muestra el estado de reproducción

DADO que la función está apagada por defecto para usuarios nuevos
CUANDO el usuario no la ha activado
ENTONCES las respuestas solo se muestran en texto

DADO que el usuario pulsa el botón de altavoz de una respuesta
CUANDO quiere escucharla manualmente
ENTONCES se reproduce con la voz y velocidad configuradas

DADO que el usuario apaga la función, envía una consulta o sale del chat
CUANDO hay una lectura en curso
ENTONCES la lectura se detiene de inmediato

DADO que el motor de voz principal falla o agota su cuota
CUANDO se va a leer una respuesta
ENTONCES se conmuta al motor de respaldo o se informa el problema sin afectar el chat de texto

DADO que el texto de la respuesta contiene símbolos, formato o unidades agronómicas
CUANDO se prepara la lectura
ENTONCES se lee de forma natural (ej. "kg/ha" como "kilos por hectárea"), sin pronunciar símbolos

DADO que el usuario crea su voz personalizada
CUANDO graba una muestra con consentimiento explícito y verificación de voz propia
ENTONCES "Mi voz" aparece como opción y puede previsualizarla, regrabarla, desactivarla o eliminarla
```

## Restricciones y Supuestos

- **Restricciones:**
  - Solo clonación de la propia voz del usuario (Ley 1581, dato biométrico); prohibida la de terceros.
  - Motores de clonación con licencia MIT (GPT-SoVITS, Chatterbox); descartados F5-TTS (pesos CC-BY-NC) y XTTS-v2 (CPML).
  - Motor por defecto `speechSynthesis`; motores intercambiables detrás de interfaz común.
  - GPU en la nube (RunPod/HuggingFace Spaces) para voz personalizada.
  - Costo operativo Fase 1: USD 0/mes dentro de capas gratuitas, con alerta al 80% de cuota.
  - No almacenar audio de respuestas; audio personal cifrado y con eliminación efectiva.
- **Supuestos validados:** asistente y endpoint de chat estables; usuarios con altavoz/audífonos y navegador compatible.
- **Supuestos no validados:** lista curada de voces del navegador (el estándar no expone género); calidad de clonación con acentos colombianos (requiere prueba de concepto).

## Métricas de Éxito

| Métrica | Línea Base | Meta | Plazo |
|---------|-----------|------|-------|
| Inicio de reproducción | N/A | ≤ 3 s (p95) | Al cierre de pruebas |
| Costo operativo Fase 1 | N/A | USD 0/mes (capas gratuitas) | Continuo |
| Disponibilidad del chat ante fallo de lectura | 100% | 100% (sin regresión) | Continuo |
| Persistencia de preferencias | N/A | 100% entre sesiones/dispositivos | Al cierre de pruebas |
| Cobertura de matriz de pruebas | 0% | 100% de navegadores/dispositivos | Al cierre de pruebas |
| (Fase 2) Inteligibilidad y parecido de la voz | N/A | Validado con grupo de usuarios de prueba | Al cierre de PoC |

## Prioridad (MoSCoW)

- **Must Have:** interruptor persistente, selector de voz + muestra, lectura automática y manual, controles de reproducción, limpieza del texto, detención automática, conmutación a respaldo, estado visible, chat escrito intacto, no almacenamiento de audio de respuestas.
- **Should Have:** control de velocidad, sincronización multi-dispositivo, activación administrativa y límites, métricas de uso.
- **Could Have:** voz personalizada (Fase 2/plus) — GPT-SoVITS/Chatterbox en GPU cloud.
- **Won't Have (en este alcance):** conversación en tiempo real, otros idiomas, clonación de terceros, app nativa, cambios al agente.

## Dependencias

- **RFP-AGROIA-001 (entrada por voz):** entrega conjunta para la experiencia hablada completa.
- **Endpoint de chat existente:** estable y sin cambios.
- **RT-020 (interfaz común de síntesis):** precondición de la cadena de motores.
- **GPU cloud (Fase 2):** aprovisionamiento del servicio para GPT-SoVITS/Chatterbox.
- **Asesoría jurídica (Fase 2):** tratamiento de dato biométrico (Ley 1581).

---

**✅ Lista para diseño/estimación**
