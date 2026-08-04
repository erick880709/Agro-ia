# RT-014: Pipeline CI/CD

**Tipo:** Requisito técnico
**Categoría:** Infraestructura / DevOps
**Fuente:** RFP-AgroInteligente-Colombia.md — Secciones 6.5, 7.3

## Descripción
La plataforma debe contar con un pipeline de integración y despliegue continuo (CI/CD) que automatice el ciclo de vida del software desde el código fuente hasta producción. El pipeline debe incluir:

**Integración continua (CI):**
- Ejecución automática en cada push a ramas principales (main, develop).
- Linting y análisis estático de código (ESLint para Angular, flake8/ruff para Python).
- Ejecución de tests unitarios y de integración.
- Escaneo de seguridad de dependencias (npm audit, pip-audit, safety).
- Construcción de imágenes Docker.
- Escaneo de vulnerabilidades en imágenes (Trivy, Snyk, Docker Scout).

**Despliegue continuo (CD):**
- Despliegue automático a entorno de staging tras CI exitoso.
- Despliegue a producción con aprobación manual (gate).
- Estrategia de despliegue sin tiempo de inactividad (rolling updates, blue/green).
- Rollback automático o simplificado en caso de fallo.

## Criterio medible / restricción concreta
- El pipeline completo (CI) debe ejecutarse en menos de 15 minutos.
- Bloquear merge a main si el pipeline falla (branch protection).
- No especificados en el RFP — definir: herramienta de CI/CD (GitHub Actions, GitLab CI, Jenkins), registro de contenedores (ECR, Docker Hub, GHCR), estrategia de versionado semántico o por commit SHA.

## Impacto en la arquitectura
- Cada microservicio tiene su propio pipeline, definido como código (GitHub Actions workflow, Jenkinsfile).
- Las imágenes Docker se versionan y publican en un registro de contenedores.
- Los manifiestos de Kubernetes (Helm charts) se actualizan con la nueva versión de la imagen en el paso de CD.

## Notas del analista
- GitHub Actions es la opción más simple si el código se aloja en GitHub: gratuito para repositorios públicos, buena integración, marketplace de actions.
- Para el frontend Angular, el pipeline incluye: npm ci → lint → test → build → Docker build → push.
- Para el backend Python: pip install → lint → test → Docker build → push.
- Para modelos ML: entrenamiento → validación → registro en MLflow → Docker build → push → deploy.
