# RNF-007: Portabilidad y Mantenibilidad

**Tipo:** Requerimiento no funcional
**Categoría:** Mantenibilidad / DevOps
**Fuente:** RFP-AgroInteligente-Colombia.md — Sección 6.5

## Descripción
La plataforma debe empaquetarse y desplegarse siguiendo prácticas modernas de DevOps que garanticen portabilidad entre entornos y facilidad de mantenimiento:

- **Contenedores Docker:** cada componente o microservicio debe estar empaquetado como imagen Docker.
- **Orquestación con Kubernetes:** escalado automático (HPA), alta disponibilidad mediante réplicas, despliegues controlados (rolling updates, blue/green o canary), aislamiento de recursos (CPU/memory requests y limits).
- **CI/CD:** pipeline de integración y despliegue continuo que automatice pruebas, construcción de imágenes, escaneo de seguridad y despliegue.
- **MLOps:** prácticas equivalentes para modelos de ML (versionado de modelos, validación automática, despliegue de modelos sin interrumpir el servicio).

## Criterio medible / restricción concreta
- Todo el software se despliega mediante contenedores Docker.
- Los despliegues en producción no deben causar tiempo de inactividad (zero-downtime deployments).
- El pipeline CI/CD debe ejecutarse en cada push a las ramas principales.
- No especificados en el RFP — definir: herramienta de CI/CD (GitHub Actions, GitLab CI, Jenkins), registro de contenedores (Docker Hub, ECR, ACR), entorno de staging antes de producción.

## Impacto en la arquitectura
- Dockerfile por cada microservicio, optimizado para tamaño y seguridad (multi-stage builds).
- Helm charts o Kustomize para definición de despliegues en Kubernetes.
- Estrategia de branching definida (trunk-based o GitFlow).
- Repositorio de modelos de ML con versionado (MLflow Model Registry o equivalente).
- Entornos: desarrollo, staging, producción.

## Notas del analista
- El RFP no especifica la herramienta de CI/CD. Para un proyecto con financiación pública/investigación, GitHub Actions es una buena opción (gratuito para repos públicos, integración nativa con GitHub).
- La práctica de MLOps es relativamente nueva para muchos equipos. Se recomienda mantener el pipeline de ML simple inicialmente (entrenamiento manual con scripts versionados, despliegue automatizado vía CI/CD) e ir sofisticándolo según madure el proyecto.
