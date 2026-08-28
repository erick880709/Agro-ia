# Especificación de Cierre de Brechas — AgroIA v3.0

## Contexto

AgroIA v2.14 es una plataforma de decisión agronómica trazable, validada en producción con sensores IoT, motor de reglas UPRA/Cenicafé/AGROSAVIA y ML en modo sombra. La versión 3.0 cierra las brechas agronómicas, de seguridad y de campo que impiden la adopción masiva y la certificación como plataforma líder en el mercado colombiano.

**Principios rectores:**
- Nunca bloquear por datos faltantes (degradación con aval de agrónomo).
- El sistema experto es la fuente de verdad; el ML es sombra validada por humanos.
- Trazabilidad total (cada acción queda auditada).
- Honestidad técnica: el usuario sabe qué datos son reales, estimados o validados por IA.

**Excluido de esta especificación (por seguir en fase demo):**
- Escalabilidad de infraestructura (Render/Neon Free, cold starts, 502/500). Se mantiene la arquitectura actual sin colas de mensajería (Kafka/SQS). El sistema debe ser validado con decenas de dispositivos; la escalabilidad se abordará en v3.5 cuando se supere el piloto del Quindío.

---

## 1. Seguridad y Autenticación (JWT/OAuth2)

### 1.1 Objetivo
Reemplazar el esquema actual de autenticación basado en header `X-User-Role` por un sistema de tokens JWT con flujo OAuth2 (opcionalmente con integración a Keycloak/Auth0). Esto garantiza la identidad del usuario, previene suplantación y cumple con los requisitos de seguridad para manejar datos financieros y de producción reales.

### 1.2 Funcionalidades
- **Login**: `POST /api/v1/auth/login` devuelve `access_token` (JWT) con expiración de 8 horas y `refresh_token` (30 días). Mantiene compatibilidad con las cuentas demo.
- **Token validation middleware**: Verifica el token en cada solicitud (excepto `/health`, `/docs`). Si es inválido o expirado, devuelve `401 UNAUTHORIZED`.
- **Refresh**: `POST /api/v1/auth/refresh` con `refresh_token` devuelve un nuevo `access_token`.
- **Logout**: `POST /api/v1/auth/logout` invalida el token (se guarda en una blacklist en Redis o en BD con expiración).
- **Auditoría**: Cada login/refresh/logout se registra en `auditoria` con IP y user-agent.

### 1.3 Cambios en el modelo de datos
- Tabla `agroia.tokens_blacklist`: `jti`, `expires_at` (cleanup diario). Opcional si se usa Redis.
- `usuarios` mantiene el `password_hash` (bcrypt).

### 1.4 API Endpoints
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Login con email/contraseña, devuelve `access_token` y `refresh_token`. |
| POST | `/api/v1/auth/refresh` | Renueva `access_token`. |
| POST | `/api/v1/auth/logout` | Invalida el token actual. |
| GET | `/api/v1/auth/me` | Devuelve los datos del usuario autenticado. |

### 1.5 Seguridad
- JWT firmado con HS256 (o RS256 en producción) usando una clave secreta de 32+ caracteres (variable de entorno `JWT_SECRET`).
- `refresh_token` almacenado en BD (hash) para revocación manual si es necesario.
- CORS configurado solo para los dominios de producción.
- Headers `X-User-Role` y `X-User-Email` se eliminan y se leen del token. Se mantiene la cabecera solo para debugging y solo en entornos de desarrollo.

### 1.6 UX
- El cliente guarda el token en `localStorage` (o en cookie HttpOnly para mayor seguridad, aunque esto requiere CSRF). La SPA incluye el token en el header `Authorization: Bearer <token>`.
- Si el token expira, se dispara automáticamente el refresh antes de cada petición (interceptor en `api()`).
- Las cuentas demo siguen funcionando con las mismas credenciales.

### 1.7 Esfuerzo estimado: 2 semanas
### 1.8 Dependencias
- `python-jose` o `PyJWT` para JWT.
- `passlib` ya está instalado.
- Opcional: integrar con Auth0 (facilita gestión de usuarios y MFA).

---

## 2. Diagnóstico Visual de Plagas y Enfermedades (Visión por Computador)

### 2.1 Objetivo
Proveer un modelo de visión propio que, dada una imagen del cultivo, devuelva la plaga/enfermedad más probable con su nivel de severidad, sin depender de APIs externas de pago (OpenAI). Esto reduce costos, latencia y permite funcionar sin internet en el campo (una vez descargado el modelo).

### 2.2 Funcionalidades
- **Entrenamiento del modelo**: Se utiliza un conjunto de datos de imágenes etiquetadas de plagas comunes en Colombia (Roya, Broca, Cercospora, Monilia, Gotera, etc.). Fuentes: ICA, FEDECAFE, AGROSAVIA, y datasets públicos.
- **Modelo**: EfficientNet-B0 (liviano) o MobileNetV3, entrenado con transfer learning. Se guarda como `models/plagas_model.pth` (PyTorch) o `.h5` (TensorFlow).
- **Inferencia**: Endpoint `POST /api/v1/vision/analizar-plaga` recibe una imagen (multipart/form-data) y devuelve:
  ```json
  {
    "plaga": "Roya del cafeto (Hemileia vastatrix)",
    "confianza": 0.92,
    "severidad": "Alta",
    "recomendacion": "Aplicar fungicida sistémico...",
    "fuente": "Modelo propio AgroIA v1.0"
  }

  Modo offline: La app móvil (PWA) descarga el modelo al dispositivo (TensorFlow Lite) y puede ejecutar inferencia local sin conexión. La sincronización con el backend se hace cuando hay internet.

2.3 Integración
El chat asesor (P8) puede invocar el modelo si se adjunta una foto. Si el modelo falla (baja confianza), se puede hacer una consulta al LLM (OpenAI) como respaldo.

El módulo de monitoreo de plagas (P12C) puede sugerir automáticamente la plaga basada en la imagen cuando el usuario sube una foto (opcional).

2.4 Almacenamiento
Las imágenes de diagnóstico se guardan en media/vision/ con metadatos en vision_diagnosticos (tabla): id, finca_id, imagen_url, resultado_json, created_at, usuario_id.

Esto alimenta el histórico de plagas y el módulo de trazabilidad BPA.

2.5 API
Método	Endpoint	Descripción
POST	/api/v1/vision/analizar-plaga	Sube imagen y recibe diagnóstico.
GET	/api/v1/vision/diagnosticos/{finca_id}	Historial de diagnósticos.
POST	/api/v1/admin/vision/reentrenar	(Admin) Reentrena el modelo con nuevas imágenes etiquetadas.
2.6 Esfuerzo estimado: 1.5 meses (incluyendo recolección de imágenes y entrenamiento)
2.7 Dependencias
TensorFlow o PyTorch.

OpenCV para preprocesamiento de imágenes.

GPU para entrenamiento (puede usarse Google Colab o AWS SageMaker).

3. App Móvil Offline-First (PWA + IndexedDB)
3.1 Objetivo
Permitir que los técnicos y operarios usen la plataforma en zonas sin cobertura de internet, capturando labores, fotos y lecturas de sensores (cuando el sensor no tiene conectividad), con sincronización automática al recuperar señal.

3.2 Funcionalidades
Service Worker: Cachea los assets estáticos (HTML, CSS, JS) y las configuraciones básicas (catálogo de cultivos, reglas, fincas asignadas).

IndexedDB: Guarda en local:

Tareas (labores) pendientes.

Lecturas de sensores (tramas IoT) que no pudieron ser enviadas.

Fotos de plagas/diagnóstico.

Ciclos productivos iniciados en campo.

Sincronización automática: Cuando se detecta conexión, se envía al backend mediante un Background Sync.

Modo offline en el dashboard: Muestra los datos locales y un banner "Datos pendientes de sincronizar (N)". Al sincronizar, se actualiza la vista.

3.3 Integración
El módulo de labores (P1) y el panel de fincas (P2) están preparados para leer de IndexedDB.

El simulador de sensores (P3) puede guardar la trama en local y sincronizarla.

La app se instala desde el navegador como PWA (manifest.json) y se puede usar en cualquier teléfono Android/iOS.

3.4 API Endpoints adicionales
GET /api/v1/sync/estado (devuelve el número de registros pendientes de sincronizar en el servidor, para saber si hay datos locales vs remotos).

POST /api/v1/sync/labores (recibe un batch de labores completadas offline).

POST /api/v1/sync/sensor-readings (recibe un batch de lecturas de sensores).

3.5 Seguridad
Los datos offline se cifran en el cliente (usando el localStorage encriptado o Web Crypto).

En el servidor, se validan las fechas y se verifica que los datos no estén duplicados (usando idempotency_key).

3.6 Esfuerzo estimado: 1 mes
3.7 Dependencias
Service Worker (sw.js) y manifest.json.

IndexedDB wrapper (localForage o idb).

Background Sync API (disponible en Chrome/Edge, con fallback a sincronización en segundo plano con setInterval).

4. Reglas de Antagonismo y Sinergia Nutricional
4.1 Objetivo
Enriquecer el motor de reglas actual con relaciones de segundo orden entre nutrientes, para que el diagnóstico no sea lineal y refleje las interacciones reales del suelo.

4.2 Funcionalidades
Nuevas reglas universales en la tabla reglas_agronomicas con tipo = 'antagonismo':

K-Ca-Mg: Si K está en exceso (en el rango "Alto" o "Muy Alto") y Ca o Mg están en rango bajo o medio, se añade una advertencia: "El exceso de K puede reducir la absorción de Ca/Mg. Priorizar la aplicación de estos".

P-Zn: Si P está en exceso y Zn está bajo, se añade: "Alta disponibilidad de P puede fijar Zn. Considere aplicación foliar de Zn".

N retrasa maduración: Si N está en exceso en etapa de fructificación, se recomienda reducir dosis de N para evitar retraso en cosecha.

Ca-Mg y pH: Si pH es bajo (<5.5) y Mg está bajo, se recomienda cal dolomítica en lugar de cal agrícola.

Ajuste en el orquestador: Después de evaluar las reglas primarias, se evalúan las reglas de antagonismo y se inyectan como violaciones (o warnings) con prioridad "Media" o "Baja" según la severidad. No se penalizan tanto como las violaciones directas, pero aparecen en el reporte.

4.3 Modelo de datos
Se añade el campo tipo (VARCHAR) a reglas_agronomicas con valores: primaria (actual) y antagonismo. Por defecto primaria.

Las reglas de antagonismo no requieren umbrales numéricos, sino condiciones lógicas (ej. variable_estado = 'exceso').

4.4 API
El orquestador (orchestrator.py) consulta las reglas de antagonismo después de evaluar las primarias y las agrega al resultado en un nuevo campo recomendaciones_secundarias o las fusiona en recomendaciones con un flag secundaria.

4.5 Reporte
En la sección 01 (Diagnóstico UC2), las reglas de antagonismo se muestran con un badge "Ajuste nutricional" o "Interacción", en lugar de "Déficit/Exceso".

4.6 Esfuerzo estimado: 1 mes (incluyendo la definición de las reglas con agrónomos expertos)
4.7 Dependencias
Ninguna nueva librería.

5. Inteligencia de Mercado de Venta (Precios de Cosecha)
5.1 Objetivo
Enriquecer la recomendación de cultivos (UC1) con datos económicos: precio de venta por región, rendimiento esperado y proyección de utilidad, para que el productor tome decisiones no solo edáficas sino también económicas.

5.2 Funcionalidades
Tabla precios_cosecha:

cultivo_id (FK)

departamento (o region)

precio_promedio_cop_kg (o cop_t)

fecha_actualizacion

fuente (DANE, Bolsa Nacional, gremio, ingreso manual).

Admin panel: En el menú Administración → "Precios de cosecha", el Admin puede actualizar los precios por cultivo y región (o conectar a una API del DANE si estuviera disponible).

Cálculo de utilidad: En UC1, para cada cultivo sugerido, se calcula:

Ingreso bruto = rendimiento_esperado_ficha (t/ha) * precio_promedio_cop_kg

Costo insumos = costo_plan_ideal (de la sección 8.9)

Utilidad = ingreso_bruto - costo_insumos

Ranking final: Los cultivos se ordenan por un "score ponderado" = aptitud (0-100) * 0.7 + utilidad_normalizada * 0.3, permitiendo al productor elegir entre el más apto o el más rentable.

5.3 Integración
El orquestador (UC1) recibe precios_cosecha y los incluye en el resultado de sugerencias_cultivos.

En el reporte (sección 02, Recomendación UC1), se añade una columna "Utilidad estimada" en COP/ha y un badge "Más rentable" para el cultivo con mayor utilidad.

5.4 API
Método	Endpoint	Descripción
GET	/api/v1/cultivos/precios?departamento=	Obtiene precios de cosecha para un departamento.
PUT	/api/v1/admin/precios-cosecha	Admin actualiza precios.
5.5 Esfuerzo estimado: 2 semanas
5.6 Dependencias
Ninguna nueva librería.

6. Integración con Laboratorios ICA Acreditados (Ingesta de Análisis de Suelo)
6.1 Objetivo
Permitir que los resultados de análisis de suelo realizados en laboratorios acreditados por el ICA sean ingeridos automáticamente (via API, CSV o XML) y actualicen la lectura del sensor, elevando la confianza de la recomendación (cambiando npk_sin_calibrar a validado_en_laboratorio).

6.2 Funcionalidades
Formato de datos: Definir un esquema estándar para los resultados de laboratorio (pH, N, P, K, Ca, Mg, S, MO, CIC, textura, etc.). Se puede basar en el estándar de la red de laboratorios agropecuarios colombianos.

Carga masiva: En P4 (Cargar archivo), además de los formatos actuales, aceptar un archivo Excel/CSV con el formato del laboratorio (mapeable por el usuario).

API: POST /api/v1/lab/ingestar recibe un JSON con los datos y los asocia a una finca y lote. Opcional: se puede implementar un webhook para que los laboratorios envíen los resultados automáticamente.

Validación: Los valores deben estar dentro de rangos físicos razonables. Si no, se rechazan con advertencia.

Efecto en confianza: Si la finca tiene un resultado de laboratorio reciente (fecha de muestreo < 90 días), el orquestador prioriza ese valor sobre el sensor y marca la variable como confiabilidad = "Validado en laboratorio". Además, se elimina la penalización npk_sin_calibrar para esas variables.

6.3 Modelo de datos
Tabla agroia.analisis_laboratorio:

id, finca_id, lote_id, fecha_muestreo, fecha_resultado, laboratorio_nombre, resultados (JSONB con los pares variable-valor).

El SueloAdapter debe buscar el análisis más reciente y si su fecha es posterior a la última lectura del sensor, usarlo en lugar del sensor (o fusionar, dando prioridad al laboratorio para las variables que mide).

6.4 API
Método	Endpoint	Descripción
POST	/api/v1/fincas/{id}/lab/ingestar	Ingesta de resultados de laboratorio.
GET	/api/v1/fincas/{id}/lab/analisis	Historial de análisis de laboratorio.
DELETE	/api/v1/fincas/{id}/lab/analisis/{id}	(Admin) Eliminar análisis erróneo.
6.5 Esfuerzo estimado: 1 mes
6.6 Dependencias
Definir el formato estándar con el ICA o con los laboratorios más usados.

7. Módulo de Sostenibilidad y Huella de Carbono (Opcional para v3.0, pero estratégico)
7.1 Objetivo
Calcular la huella de carbono de la finca (por ciclo de cultivo) y generar un score de sostenibilidad basado en prácticas regenerativas, que pueda ser usado para acceder a financiamiento verde o certificaciones.

7.2 Funcionalidades
Cálculo de huella: Utilizar factores de emisión por tipo de fertilizante (N2O, CO2), uso de maquinaria, consumo de combustible, etc. Se puede basar en la metodología IPCC o en la guía de cálculo de huella de carbono para el sector agropecuario colombiano.

Prácticas regenerativas: Evaluar (a partir del historial de labores y ciclos) la adopción de prácticas como rotación de cultivos, abonos verdes, cero quema, control biológico de plagas, etc., y asignar un puntaje.

Reporte: Añadir una sección "Sostenibilidad" al reporte con el score y recomendaciones para mejorar.

7.3 Modelo de datos
Tabla agroia.calculo_carbono: finca_id, cultivo_id, ciclo_id, huella_co2e_kg, practicas_score, fecha_calculo, detalle (JSONB con desglose).

7.4 Esfuerzo estimado: 1.5 meses (si se quiere hacer con rigor científico)
7.5 Dependencias
Definir factores de emisión y metodología con consultores ambientales.

Resumen de Esfuerzos y Priorización
Módulo	Esfuerzo	Prioridad	Justificación
Seguridad (JWT/OAuth2)	2 semanas	1 (Urgente)	Requisito para manejar datos reales de productores.
App Móvil Offline (PWA)	1 mes	2 (Estratégico)	Permite que los técnicos usen la herramienta en el campo.
Visión Plagas (CNN)	1.5 meses	3 (Diferenciador)	Valor añadido visible para el productor.
Reglas de Antagonismo	1 mes	4 (Agronómico)	Mejora la precisión del diagnóstico.
Precios de Cosecha	2 semanas	5 (Económico)	Convierte la recomendación en decisión de negocio.
Laboratorios ICA	1 mes	6 (Calidad de datos)	Aumenta la confianza de los datos de suelo.
Sostenibilidad	1.5 meses	7 (Largo plazo)	Importante para financiamiento verde.
Total estimado: 8.5 meses de trabajo de un equipo de 3 desarrolladores (backend, frontend, ML), con la posibilidad de paralelizar varios módulos.

Anexo: Impacto en la Confianza del Sistema
Brecha cerrada	Impacto en la confianza percibida	Impacto en la confianza real (numérica)
Seguridad	Alta (tranquilidad del usuario)	Ninguno
App Offline	Alta (usabilidad en campo)	Ninguno
Visión Plagas	Muy Alta (diagnóstico rápido)	+5% en la recomendación final (por detección temprana)
Antagonismos	Media (calidad del diagnóstico)	+10% en precisión de recomendaciones de nutrientes
Precios de Cosecha	Muy Alta (decisión de siembra)	Ninguno (solo en UC1)
Laboratorios	Muy Alta (confianza en los datos)	Hasta +15% en confianza real (por validación de NPK)
Sostenibilidad	Media (para financiamiento)	Ninguno
Conclusión: La implementación de estas 7 especificaciones convierte a AgroIA en la plataforma de decisión agronómica más completa de Colombia, cubriendo el ciclo completo: suelo + planta + negocio + campo + sostenibilidad.

t