# Contenedores y Kubernetes

## Tabla de contenido

1. Dockerfile e imagen
2. Manifiestos Kubernetes
3. RBAC y cuentas de servicio
4. Red y secretos en el clúster
5. Herramientas

## 1. Dockerfile e imagen

- Imagen base con `latest` o sin digest; base completa donde basta distroless/slim/
  Chainguard; paquetes del SO con CVE alcanzables (Trivy/Grype).
- `USER root` implícito: define un usuario no privilegiado (`USER 10001`).
- Secretos en `ARG`/`ENV`/`COPY` (quedan en capas aunque se borren después); usa
  `RUN --mount=type=secret`.
- `ADD` de URLs remotas sin verificación de checksum; `curl | sh` en build.
- Multi-stage: herramientas de build, compiladores y fuentes fuera de la imagen final.

## 2. Manifiestos Kubernetes

- `securityContext`: `runAsNonRoot: true`, `allowPrivilegeEscalation: false`,
  `readOnlyRootFilesystem: true`, `capabilities.drop: ["ALL"]`, `seccompProfile:
  RuntimeDefault`. `privileged: true`, `hostPID`, `hostNetwork`, `hostPath` → high salvo
  justificación de plataforma (DaemonSets de observabilidad documentados).
- Pod Security Standards: namespaces de aplicaciones en `restricted` (o `baseline` con
  justificación).
- `resources.limits` ausentes en servicios expuestos → DoS de nodo/vecinos.
- Imágenes por tag mutable; `imagePullPolicy` sin digest en prod.
- Probes que exponen endpoints de debug.

## 3. RBAC y cuentas de servicio

- `ClusterRole` con `*` en verbs/resources, `escalate`, `bind`, `impersonate`, acceso a
  `secrets` a nivel clúster; `cluster-admin` a cuentas de aplicación.
- `automountServiceAccountToken: true` (por defecto) en pods que no llaman a la API.
- Identidad cloud por pod (IRSA, Azure Workload Identity, GKE Workload Identity) en vez de
  llaves de nube montadas como secretos.

## 4. Red y secretos en el clúster

- Sin `NetworkPolicy` por defecto-denegar en namespaces con datos sensibles.
- `Secret` de Kubernetes es base64, no cifrado: exige cifrado en reposo de etcd/KMS del
  proveedor y preferir External Secrets/CSI driver con el gestor de secretos.
- Ingress sin TLS o con anotaciones que deshabilitan autenticación/WAF.

## 5. Herramientas

`trivy config`/`trivy k8s`, `kubesec`, `checkov -d manifests/`, `kube-bench` (CIS, solo
sobre clústeres propios y autorizados), Polaris/Kyverno/OPA Gatekeeper para políticas.
Si el equipo de soporte N1 opera el clúster, las recomendaciones deben incluir el
comando de verificación (`kubectl auth can-i`, `kubectl get pod -o jsonpath=...`).
