# Branding PersonalSoft para Propuestas de Estimación

*Alineada al Manual de marca PersonalSoft (versión mayo 2025) y a la Plantilla PPT Corporativa oficial.*

El PPTX ejecutivo se genera **siempre** desde `assets/branding/Plantilla_PPT_Corporativa_PersonalSoft.pptx` con el flujo de edición de plantillas de la skill `pptx` (`unzip → add_slide.py → editar ppt/slides/slideN.xml → clean.py → zip → validate.py --original`). Nunca desde un tema genérico ni recreando el logo o los fondos a mano.

> La plantilla bundleada es la oficial con dos optimizaciones de peso: el fondo animado de la portada (slide 1) quedó como imagen estática y una imagen de fondo se comprimió. Si el cliente valora la portada animada, usa la plantilla original de 42 MB que entrega el área de marca.

## Paleta oficial (Manual de marca)

| Nombre | Uso | Hex | Pantone |
|---|---|---|---|
| **Azul Eléctrico** | Color principal: bloques de color, cifras destacadas, series principales de gráficos | `0072BC` | 3553 |
| **Azul Infinito** | Títulos de slide, encabezados de tabla, línea divisoria bajo título | `0E337C` | 6105 |
| **Azul Grafito** | Texto oscuro de alto contraste, fondos oscuros, segunda serie | `132436` | 4146 |
| **Blanco Puro** | Fondos claros y texto sobre fondos azules | `FFFFFF` | — |

- Para series adicionales (ej. roles en un gráfico), usa tintes de estos azules (ej. `5AA9DD`, `A9CFEA`) y gris neutro `B7BEC7`. No introduzcas rojos, verdes ni naranjas: el manual prohíbe cambios de color no autorizados.
- La versión anterior de esta guía indicaba `263474` y Arial como base: no corresponden al manual vigente. `263474` solo aparece en algunos elementos heredados de la plantilla; no lo uses en contenido nuevo.

## Tipografía

**Reddit Sans** (Light para cuerpo largo, Regular/Medium para cuerpo, ExtraBold/Black para títulos y cifras), tal como la usa la plantilla. Fallback: Arial. Si el equipo que abrirá el PPTX no tiene Reddit Sans instalada, PowerPoint la sustituye; deja ~10% de holgura en cajas de texto.

## Reglas del logo (Manual de marca)

- Usa el imagotipo horizontal que ya trae la plantilla. La versión vertical y la rotada requieren aprobación del área de marca.
- Respeta el área de seguridad (ancho de la letra "O" alrededor del logo).
- No estires, inclines, recolores, sombrees ni pongas bordes al logo; no lo pongas sobre fondos de bajo contraste.
- Co-branding con el cliente (ej. Bancolombia): estructura `Marca aliada | PersonalSoft` con separador vertical y el área de seguridad de ambos.

## Tono de marca

Experto, sencillo, práctico y cercano. Frases cortas, orientadas a solución ("modo solución"). Cierre con el slogan **We make *it* happen**.

## Mapeo de slides de la plantilla oficial (16 slides)

| Slide | Layout | Úsala para |
|---|---|---|
| 1 | Portada con fondo (animado en la original), logo inferior | Portada alternativa |
| 2 | Portada estática, fondo abstracto azul, logo inferior | **Portada** de la propuesta (título + subtítulo en blanco) |
| 3 | Título + imagen izquierda sobre gris + texto derecho | Contexto de negocio con imagen |
| 4 | Título grande sobre blanco | Divisor de sección claro |
| 5 | Título + texto izquierdo, imagen sangrada derecha | Épica / propuesta de valor |
| 6 | Frase sobre Azul Eléctrico | Mensaje clave o cita |
| 7 | Split: bloque azul con título + texto derecho | **Resumen ejecutivo** (cifras en el bloque azul) |
| 8 | Estadísticas (gráficos) | Distribución por rol, comparativo tradicional vs IA |
| 9 | Tabla + gráfico | Estimación por ítem, cronograma |
| 10 | Blanco con ícono | Contenido libre (diagramas, flujos) |
| 11 | Blanco con línea de título | Contenido libre con título |
| 12 | Divisor azul con logo | Separador de sección |
| 13 | Cierre "¡Gracias!" con dirección y slogan | **Cierre** |
| 14–16 | Fondos abstractos con ícono | Divisores visuales |

**Slots ≠ datos:** si un layout trae más cajas que tus datos, elimina el grupo completo (no solo el texto).

## Reglas del PPTX ejecutivo

- Máximo 10–12 slides.
- Todas las cifras salen del JSON de `scripts/calcular_estimacion.py`; el PPTX, el HTML y el MD muestran exactamente los mismos valores.
- Gráficos nativos (python-pptx o XML de chart), con la paleta oficial.
- Corre `validate.py salida.pptx --original assets/branding/Plantilla_PPT_Corporativa_PersonalSoft.pptx` y la QA visual de la skill `pptx` antes de entregar.
- Busca texto de relleno sobrante: `markitdown salida.pptx | grep -iE "lorem|ipsum|Título|Texto o reseña|Inserta aquí"`.

## Reglas del HTML detallado

- Acentos con `0072BC` (principal) y `0E337C` (títulos); texto `132436` en modo claro.
- Modo oscuro vía `prefers-color-scheme`: fondo `132436`, títulos en un tinte claro de `0072BC` (ej. `5AA9DD`) para mantener contraste.
- Tipografía: `"Reddit Sans", Arial, Helvetica, sans-serif` (puede cargarse desde Google Fonts si el entorno lo permite).
