# Resumen Ejecutivo — RFP-AGROIA-002: Lectura en voz alta de las respuestas del Asesor agronómico

**Cliente:** Equipo AGROINTELIGENTE COLOMBIA
**Fecha del documento:** 19 de octubre de 2026
**Documento fuente:** `context/RFP-AGROIA-002_Lectura_de_respuestas_en_voz_alta.md`

## Objetivo y alcance del proyecto
Permitir que el usuario escuche las respuestas del Asesor agronómico leídas en voz alta, con control para activar o desactivar la función, elección de voz femenina o masculina, controles de reproducción y velocidad, y como valor agregado (Fase 2/plus) una voz personalizada grabada por el usuario. Complementa el RFP-AGROIA-001 (entrada por voz) para habilitar una conversación hablada completa.

**Fase 1 (obligatoria):** lectura con voces predefinidas, interruptor persistente, selector de voz con muestra, lectura automática y manual, controles de reproducción/velocidad, limpieza del texto para lectura natural y plan de respaldo entre motores.
**Fase 2 (plus):** flujo guiado de grabación de la propia voz, consentimiento explícito, verificación de voz propia, y gestión (previsualizar, regrabar, desactivar, eliminar).

Fuera de alcance: cambios al agente o a sus reglas, conversación en tiempo real con interrupciones, idiomas distintos del español, clonación de voces de terceros y aplicación móvil nativa.

## Plazos
Cronograma sugerido, sujeto al plan del oferente:
- Fase 0 (arquitectura y selección de motores): 3–5 días.
- Fase 1 (interfaz): 3–5 días.
- Fase 2 (lectura con voces predefinidas y respaldo): 1–2 semanas.
- Fase 3 (pruebas y documentación): 1 semana.
- Fases 4–5 (voz personalizada, opcionales y contratables por separado): 3–5 semanas.
- Fase 6 (despliegue y seguimiento): 1 semana.

## Presupuesto / modelo de contratación
No se fija presupuesto. Restricción económica explícita: priorizar APIs y componentes gratuitos o de código abierto; costo operativo cercano a cero en Fase 1 y estimación explícita para Fase 2 (infraestructura GPU o servicio de pago).

## Criterios de evaluación de la propuesta
- Adecuación técnica y calidad de la experiencia de voz: 25%.
- Costo total y uso eficiente de capas gratuitas: 20%.
- Privacidad, seguridad y cumplimiento normativo (incluida la voz personalizada): 20%.
- Resiliencia (respaldo, control de cuota, tolerancia a fallos): 10%.
- Experiencia y equipo: 10%.
- Plan de pruebas, documentación y soporte: 10%.
- Viabilidad de la voz personalizada (plus): 5%.

## Stakeholders identificados
- Equipo AGROINTELIGENTE COLOMBIA, solicitante.
- Productores / agricultores y técnicos / extensionistas, usuarios de la lectura en campo.
- Administrador, configura motores, límites y activación general.
- Asistente agronómico, genera la respuesta de texto que se convierte en audio.

## Entregables esperados
1. Función de lectura implementada y desplegada.
2. Servicio de voz con interfaz común de motores intercambiables y cadena de respaldo.
3. Selector de voz con muestra y controles de reproducción.
4. (Plus) Flujo de grabación y gestión de voz personalizada con servicio de síntesis.
5. Código fuente con pruebas automatizadas.
6. Matriz de pruebas por dispositivo y navegador.
7. Informe de decisión técnica (motores, licencias y costos vigentes).
8. Estimación de consumo y costo mensual con plan de monitoreo de cuotas.
9. Actualización de documentos vivos (menús/pantallas, funcional técnico, catálogo funcional, OpenAPI si aplica).
10. Guía breve de uso para usuario final y administrador.

## Supuestos y restricciones generales
- El Asesor agronómico y su endpoint de chat existen y permanecen estables.
- Los usuarios cuentan con altavoz o audífonos y un navegador compatible.
- Las voces predefinidas cubren español neutro o latinoamericano.
- La voz personalizada es opcional y puede diferirse si el costo de GPU o la licencia no se justifican.
- Las capas gratuitas de terceros pueden cambiar sin previo aviso.

## Glosario
- **Síntesis de voz (TTS):** conversión de texto a audio hablado.
- **Motor de voz:** proveedor o componente que realiza la síntesis (navegador, nube, autoalojado).
- **Voz personalizada:** voz sintética generada a partir de una muestra grabada por el propio usuario.
- **Cuota:** límite de caracteres/uso de los planes gratuitos de los motores en la nube.
- **Dato biométrico:** dato personal derivado de características físicas (la voz), sujeto a la Ley 1581 de 2012.

## Resumen cuantitativo de la extracción
- Requerimientos funcionales extraídos: 19
- Requerimientos no funcionales extraídos: 9
- Requisitos técnicos extraídos: 11
- Información de diseño extraída: 2

## Decisiones cerradas con el usuario (2026-10-19)
- **Motor por defecto:** `speechSynthesis` (Web Speech API) cuando el usuario no selecciona ni crea una voz.
- **Voz personalizada:** solo la **propia voz del usuario** (cumple RFP + Ley 1581), con motores **GPT-SoVITS y Chatterbox** (MIT, autoalojados). **F5-TTS descartado** (código MIT pero pesos CC-BY-NC-4.0) y **XTTS-v2 descartado** (CPML).
- **Hosting de GPU:** servicio de GPU en la nube (RunPod / HuggingFace Spaces / similar).

## Vacíos y riesgos detectados
- "Inicio de la reproducción en pocos segundos" y "costo cercano a cero" no están cuantificados; falta definir umbrales.
- La Web Speech API no expone el género de la voz; se requiere una lista curada de voces por plataforma.
- No se define el modo de lectura por defecto (completa vs. parcial con "seguir leyendo") ni si la función se entrega apagada o encendida para usuarios nuevos.
- No se define el contrato exacto del endpoint de síntesis en servidor ni el mecanismo de verificación del borrado de la voz personalizada.
- Pendiente confirmar la integración con RFP-AGROIA-001 (entrega conjunta o separada) y la viabilidad/costo real de GPU para la voz personalizada (prueba de concepto).
