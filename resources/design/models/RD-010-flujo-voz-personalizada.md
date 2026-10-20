# RD-010: Flujo de voz personalizada (Fase 2 / plus)

**Tipo:** Información de diseño
**Fuente:** RFP-AGROIA-002 — Secciones 4.1 y 6.2

## Descripción
Flujo guiado para que el usuario cree su propia voz sintética: en preferencias elige "Crear mi voz"; la aplicación explica qué se grabará, para qué se usará y por cuánto tiempo se conserva, y solicita consentimiento explícito; el usuario graba una muestra guiada leyendo textos propuestos, con indicadores de calidad (ruido, volumen, duración) y una frase de verificación de voz propia; la aplicación procesa la muestra de forma asíncrona ("procesando tu voz") y habilita una prueba de la voz resultante; si el usuario está conforme, activa "Mi voz" como tercera opción junto a femenina y masculina. El usuario puede regrabar, desactivar o eliminar su voz en cualquier momento.

## Elementos de referencia
- Paso de consentimiento informado.
- Grabación guiada con indicadores de calidad (ruido, volumen, duración).
- Estado asíncrono de procesamiento.
- Prueba/previsualización de la voz generada.
- Opciones de regrabar, desactivar y eliminar.

## Notas del analista
La voz personalizada es opcional (plus, Fase 2) y depende de infraestructura GPU o de un servicio de pago. Requiere tratamiento de dato biométrico (Ley 1581) y prevención de suplantación.
