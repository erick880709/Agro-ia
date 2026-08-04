# RT-006: API Gateway

**Tipo:** Requisito técnico
**Categoría:** Infraestructura / Integración
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 7.2

## Descripción
La plataforma debe contar con un **API Gateway** como punto de entrada único para todos los clientes (frontend Angular, aplicaciones móviles futuras, integraciones de terceros). Sus responsabilidades incluyen:

- **Enrutamiento:** dirigir cada solicitud al microservicio correspondiente según la ruta y el verbo HTTP.
- **Autenticación y autorización:** validar tokens JWT/OAuth2 en cada solicitud antes de enrutarla.
- **Rate limiting:** proteger los servicios backend de abusos o tráfico excesivo.
- **Documentación de API:** exponer un portal de desarrolladores con Swagger/OpenAPI.
- **CORS:** configurar correctamente el acceso desde el frontend.
- **Transformación de solicitudes/respuestas:** adaptar formatos si es necesario.

## Criterio medible / restricción concreta
- Latencia añadida por el API Gateway < 50ms en el percentil 95.
- Todas las solicitudes externas deben pasar por el API Gateway; ningún microservicio debe ser accesible directamente desde Internet.
- No especificados en el RFP — definir: producto concreto (Kong, Traefik, AWS API Gateway, NGINX Ingress Controller).

## Impacto en la arquitectura
- Centraliza preocupaciones transversales (autenticación, rate limiting, logging) que de otra forma cada microservicio tendría que implementar.
- Simplifica la segmentación de red: solo el Gateway está expuesto a Internet; los microservicios corren en subnets privadas.
- Permite cambiar la implementación interna de un microservicio sin afectar a los clientes (la ruta del Gateway no cambia).

## Notas del analista
- Para Kubernetes, Traefik o NGINX Ingress Controller son opciones ligeras y bien integradas.
- AWS API Gateway es una alternativa gestionada que reduce la carga operativa pero introduce acoplamiento al proveedor cloud.
- Kong es una opción robusta si se necesita un API Gateway con plugin de autenticación, rate limiting y portal de desarrolladores incluidos.
