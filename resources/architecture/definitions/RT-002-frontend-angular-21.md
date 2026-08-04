# RT-002: Stack Frontend — Angular 21

**Tipo:** Requisito técnico
**Categoría:** Stack tecnológico / Frontend
**Fuente:** Instrucción directa del cliente (sobrescribe RFP original que sugería React/Next.js)

## Descripción
El frontend de la plataforma debe desarrollarse utilizando **Angular 21** como framework principal. Este requisito técnico es vinculante y fue definido explícitamente por el cliente, sobrescribiendo la recomendación original del RFP que mencionaba React o Next.js.

La aplicación frontend debe seguir las mejores prácticas del ecosistema Angular:
- Standalone components (nuevo modelo de Angular).
- Signals para gestión de estado reactivo.
- Angular Material o sistema de diseño personalizado para UI responsive.
- Lazy loading de módulos para optimizar el rendimiento inicial.
- SSR (Server-Side Rendering) con Angular Universal si se requiere SEO o carga inicial rápida.

## Criterio medible / restricción concreta
- Angular CLI versión 21.x para generación, build y despliegue.
- TypeScript 5.x como lenguaje.
- La aplicación debe compilar sin errores en modo strict.
- Tests unitarios con Jasmine/Karma (o Jest) con cobertura mínima > 80%.

## Impacto en la arquitectura
- Determina el stack completo del frontend: lenguaje, herramientas de build, testing, CI/CD.
- La elección de Angular implica un backend que sirva como API REST (cualquier backend compatible, en este caso Python).
- Angular Material proporciona componentes accesibles y responsivos que aceleran el desarrollo.
- La separación frontend/backend es natural con Angular como SPA + API REST en Python.

## Notas del analista
- Angular 21 es una elección sólida para aplicaciones empresariales con formularios complejos, dashboards y múltiples roles de usuario (caso de AgroIA).
- Considerar el uso de NgRx o SignalStore para gestión de estado global si la aplicación crece en complejidad.
- Para visualización de mapas, Leaflet es más ligero y compatible con Angular que Google Maps SDK. Para gráficos, Chart.js o ECharts funcionan bien con Angular.
