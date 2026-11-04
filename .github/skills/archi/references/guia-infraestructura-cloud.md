# Guía: Infraestructura base cloud — organización, red, conectividad e infraestructura de entrega

Dueña de `17.6-Infraestructura-Base_<Proyecto>.md` y de sus diagramas `17.6.x`. Complementa `17-Vista-de-Despliegue.md`: `17` mapea contenedores a servicios; `17.6` describe la plataforma sobre la que esos servicios viven (cuentas/suscripciones/proyectos, red, conectividad híbrida, inspección, DNS, identidad de máquinas, registro central e infraestructura de CI/CD).

## Tabla de Contenido

1. [Cuándo aplica](#1-cuándo-aplica)
2. [Intake con niveles y reporte de banderas](#2-intake-con-niveles-y-reporte-de-banderas)
3. [Organización y cuentas](#3-organización-y-cuentas)
4. [Identidad de máquinas y acceso entre cuentas](#4-identidad-de-máquinas-y-acceso-entre-cuentas)
5. [Topología de red y conectividad](#5-topología-de-red-y-conectividad)
6. [AWS Cloud WAN: reglas de diseño](#6-aws-cloud-wan-reglas-de-diseño)
7. [Inspección, egress, híbrido y DNS](#7-inspección-egress-híbrido-y-dns)
8. [Registro, detección y gobierno central](#8-registro-detección-y-gobierno-central)
9. [Infraestructura de entrega: runners de CI/CD](#9-infraestructura-de-entrega-runners-de-cicd)
10. [Vínculo con Well-Architected](#10-vínculo-con-well-architected)
11. [Contenido mínimo de `17.6`](#11-contenido-mínimo-de-176)
12. [Fuentes](#12-fuentes)

## 1. Cuándo aplica

Genera `17.6` cuando se cumpla al menos una condición:

- La solución vive en más de una cuenta/suscripción/proyecto, o depende de una landing zone corporativa.
- Hay conectividad híbrida (on-premise, Direct Connect/ExpressRoute/Interconnect, VPN, SD-WAN) o entre regiones.
- Existe red compartida (Transit Gateway, Cloud WAN, Virtual WAN, hub-spoke, Shared VPC) o inspección centralizada.
- El sector es regulado (banca, seguros, salud) y la segmentación, egress o registro forman parte de los controles.
- El pipeline necesita runners con acceso a red privada o con identidad propia en la nube.

Si la plataforma ya existe y la gobierna otro equipo, **no la rediseñes**: regístrala como restricción (`RT-Dxx` en `03`), documenta en `17.6` solo los puntos de contacto (cuenta destino, segmento/spoke asignado, CIDR, rutas, DNS, roles) y deja las brechas en `12`/`21`. En Caso B deriva todo de IaC y configuración observada siguiendo `references/guia-terraform-a-diagrama.md`; nunca completes la topología por intuición.

## 2. Intake con niveles y reporte de banderas

Pregunta en términos de red y operación estándar; traduce tú a constructos del proveedor. Cada pregunta tiene un nivel que decide qué pasa si no se responde:

| Nivel | Significado | Si falta la respuesta |
|---|---|---|
| **[Crucial]** | Un supuesto deja el diseño estructuralmente mal | Pregunta con opciones concretas; solo continúa si el usuario lo autoriza y marca la sección 🔴 |
| **[Importante]** | Existe un default conservador | Pregunta una vez; si no responde, aplica el default y marca 🟡 |
| **[Deseable]** | Existe un default seguro | Aplica el default sin insistir y marca 🟢 |

| Tema | Pregunta | Nivel | Default si aplica |
|---|---|---|---|
| Regiones | ¿En qué regiones opera la solución? ¿Hay requisito de residencia de datos? | Crucial | — |
| Direccionamiento | ¿Hay o puede haber CIDR solapados con on-premise u otras cuentas? | Crucial | — (si el solapamiento es estructural: PrivateLink/VPC Lattice o NAT, no enrutamiento IP) |
| Segmentación | ¿Qué dominios de ruteo existen (ambientes, unidades de negocio, PCI/no PCI) y cuáles no deben comunicarse? | Crucial | — |
| Cuentas | ¿Existe landing zone? ¿Qué cuentas/suscripciones recibirán la carga? | Crucial | — |
| Inspección | ¿Se exige inspección de egress (north-south) y/o este-oeste? | Importante | Egress inspeccionado centralmente en producción |
| Híbrido | ¿Qué conectividad on-premise existe (DX/ExpressRoute/VPN), qué ASN usa y qué prefijos anuncia? | Importante | VPN redundante como respaldo de un enlace dedicado |
| IPv6 | ¿Solo IPv4 o dual-stack? | Importante | Planear dual-stack desde el inicio |
| DNS | ¿Quién resuelve nombres privados y cómo se integra con el DNS corporativo? | Importante | Zonas privadas centralizadas + resolvers híbridos |
| Identidad | ¿Cómo se autentican las cargas y pipelines (roles, identidades administradas, federación OIDC)? | Importante | Sin credenciales de larga duración |
| Registro | ¿Dónde se centralizan auditoría, flow logs y hallazgos de seguridad? | Importante | Cuenta/suscripción de log archive dedicada |
| CI/CD | ¿Los pipelines necesitan alcanzar recursos privados? ¿Qué plataforma (GitHub, Azure DevOps, GitLab)? | Importante | Runners efímeros dentro de la red, con identidad OIDC |
| Crecimiento | ¿Se esperan más regiones/cuentas en 12-24 meses? | Deseable | Reservar rangos CIDR y ASN holgados |

**Reporte de banderas.** Cuando un default sustituya una respuesta, `17.6` incluye una tabla `Sección | Bandera | Supuesto | Quién confirma`. Las banderas marcan **secciones**, no el documento. Cada 🔴 abre una incertidumbre en `12` y bloquea el cierre de `17.6`; cada 🟡 es un `SUP-Dxx` en `04`; los 🟢 quedan listados para revisión.

## 3. Organización y cuentas

| Concepto | AWS | Azure | GCP |
|---|---|---|---|
| Jerarquía | Organizations + OUs (Control Tower si hay landing zone gestionada) | Management Groups (Azure Landing Zones) | Organización → carpetas → proyectos |
| Guardrails | SCP/RCP, Control Tower controls, Config | Azure Policy, initiatives | Organization Policy |
| Cuentas típicas | management, log archive, audit/security, network, shared services, workloads por ambiente | platform (identity, management, connectivity) + landing zones de aplicación | proyectos host de Shared VPC, seguridad, logging y servicio |

Reglas:

- Un ambiente productivo nunca comparte cuenta/suscripción con no productivos cuando hay datos regulados.
- Los artefactos compartidos (registro de imágenes, artefactos, AMIs) viven en una cuenta de servicios compartidos y se consumen entre cuentas con permisos explícitos (política de recurso + rol), no copiando credenciales.
- Documenta en `17.6` la tabla `Cuenta/Suscripción | Propósito | Ambiente | Owner | Guardrails | Cargas (CT-xx)`.

## 4. Identidad de máquinas y acceso entre cuentas

Patrón de referencia (laboratorio `arquitecto-java/java-letters-api`): una instancia en la cuenta de cargas obtiene imágenes de un registro privado en otra cuenta mediante **perfil de instancia → rol → asunción de rol con confianza explícita en la cuenta origen**, sin llaves en la máquina. Generaliza así:

- Cómputo con identidad nativa: rol de tarea ECS/instance profile/IRSA o Pod Identity (AWS), Managed Identity (Azure), Service Account con Workload Identity (GCP).
- Acceso entre cuentas: política de recurso del servicio destino (p. ej. política del repositorio ECR) **más** rol con relación de confianza acotada; registra ambos lados.
- Pipelines: federación OIDC hacia roles separados de *plan* (lectura) y *apply* (escritura, solo rama protegida/ambiente aprobado).
- Hallazgos típicos en Caso B (van a `21`): llaves de acceso en servidores, `assume-role` manual por SSH, imágenes `latest`, roles con `*`.

## 5. Topología de red y conectividad

| Necesidad | AWS | Azure | GCP | Cuándo no |
|---|---|---|---|---|
| Pocas redes, sin crecimiento | VPC peering | VNet peering | VPC peering | Más de unas pocas redes o necesidad de transitividad |
| Hub de ruteo regional | Transit Gateway | Hub-spoke con firewall / Virtual WAN | Network Connectivity Center | Requisito global policy-driven multi-región (ver Cloud WAN) |
| Red global declarativa multi-región/multi-cuenta | Cloud WAN | Virtual WAN (multi-hub) | NCC + Cloud Interconnect | Dos VPC sin crecimiento |
| Exponer un servicio, CIDR solapados | PrivateLink | Private Link / Private Endpoint | Private Service Connect | Conectividad IP general |
| Servicio a servicio con autenticación por identidad | VPC Lattice | — (API Management/Private Link) | — (PSC + Service Directory) | Tráfico no HTTP/gRPC/TCP soportado |
| Red compartida centralmente | VPC sharing (RAM) | — | Shared VPC | Equipos que requieren autonomía de red |

Son **capas complementarias, no alternativas excluyentes**: una red madura usa un backbone (TGW/Cloud WAN/vWAN) con PrivateLink/Lattice y peering puntual encima.

Plan de direccionamiento: tabla `Red | Cuenta | Región | CIDR | Segmento | Propósito`, sin solapamientos, con reserva para crecimiento (IPAM cuando exista). Subredes por capa (pública, aplicación, datos, endpoints, inspección) y por zona de disponibilidad.

## 6. AWS Cloud WAN: reglas de diseño

Fuente: `aws-samples/aws-cloud-wan-blueprints` (`SKILLS.md`, `policy/`, `infra/`). Aplica cuando AWS es el proveedor y la red cruza cuentas o regiones.

**Cuándo recomendarlo.** Greenfield multi-cuenta: es el default recomendado por AWS aunque se empiece en una región (agregar regiones es un cambio de política). Brownfield con Transit Gateway funcionando: solo con disparador real — segmentación que debe ser consistente en toda la red, decenas/cientos de cuentas, onboarding de adjuntos por política o varios TGW multi-región difíciles de mantener. La migración es incremental: peering TGW↔Cloud WAN, extender tablas de ruteo a segmentos, mover adjuntos y retirar TGW.

**Flujo de diseño.**

1. Define primero el modelo de segmentación (ambiente, unidad de negocio o geografía). Los segmentos son dominios de ruteo, **no aplicaciones**.
2. Por segmento decide si sus adjuntos se comunican entre sí; usa aislado para servicios compartidos o cuando el tráfico intra-segmento deba inspeccionarse.
3. Declara regiones (`edge-locations`) y un rango ASN que no choque con on-premise ni con políticas de ruteo.
4. Declara la conectividad entre segmentos con `share` explícitos; el compartir **no es transitivo**: dibuja el grafo y declara cada arista.
5. Inspección: egress con `send-to`; este-oeste con `send-via` (`dual-hop` exige inspección en cada región participante; `single-hop` requiere matriz de regiones). Habilita *appliance mode* en las VPC de inspección.
6. Políticas de adjunto por etiqueta (`tag-value-of-key`) en vez de listas largas; reglas explícitas para adjuntos híbridos y para VPC de inspección.
7. Políticas de ruteo solo con requisito real.
8. Planea el borde híbrido: tipo de adjunto (VPN, DX gateway, Connect), segmento destino, qué anuncia y qué recibe.
9. Despliega como versión de política y revisa el *change set* antes de ejecutar.
10. Valida con el estado de ruteo posterior a políticas (`get-network-routes`), no con `list-core-network-routing-information`.

**Restricciones que suelen romper diseños.** Un adjunto pertenece a un segmento **o** a un grupo de funciones de red, no a ambos. Las políticas de ruteo no aplican a inspección (filtra en el adjunto antes). Los adjuntos VPC no modifican atributos BGP. La sumarización solo es saliente y en adjuntos con BGP. Cloud WAN **no resuelve CIDR solapados**. El plano de control vive en `us-west-2`. Cada región declarada factura por hora aunque no tenga tráfico: no listes regiones especulativas. Las cuotas se consultan en la documentación vigente, nunca de memoria.

**Separa política e infraestructura.** La política de red es un artefacto propio con su ciclo de revisión; registra en `17.6` su ubicación, versión y owner, y en `17.7` el módulo IaC que la aplica.

## 7. Inspección, egress, híbrido y DNS

- **Egress**: centralizado (VPC/VNet de egress con NAT + firewall) o distribuido (NAT por VPC). Centralizado reduce superficie y costo de firewall pero agrega dependencia y costo de transferencia; regístralo como `DA-xxx`.
- **Inspección**: AWS Network Firewall/Gateway Load Balancer, Azure Firewall/NVA, Cloud NGFW. Simetría de retorno obligatoria (appliance mode o equivalente).
- **Ingreso**: CDN/WAF/DDoS en el borde; balanceadores públicos solo en subred pública; resto privado.
- **Híbrido**: enlace dedicado + VPN de respaldo, BGP con ASN documentado, prefijos anunciados/recibidos, sumarización y failover probado.
- **DNS**: zonas privadas centralizadas, reenvío condicional hacia/desde on-premise (Route 53 Resolver endpoints, Azure DNS Private Resolver, Cloud DNS forwarding).
- **Endpoints privados** a servicios administrados (VPC endpoints, Private Endpoints, PSC) cuando el dato no debe salir a Internet.

## 8. Registro, detección y gobierno central

Tabla `Control | Servicio | Alcance | Destino | Retención | Owner`: auditoría de API (CloudTrail organizacional, Activity Log, Cloud Audit Logs), configuración (Config, Azure Policy, Asset Inventory), flow logs, detección (GuardDuty, Defender for Cloud, Security Command Center), postura (Security Hub). `19.1` define los requisitos `SEC-xxx`; `17.6` muestra dónde viven; Vulcano decide la operación continua.

## 9. Infraestructura de entrega: runners de CI/CD

Cuando el pipeline despliega o prueba contra recursos privados, el runner es parte de la arquitectura de despliegue: tiene red, identidad, costo y superficie de ataque.

| Opción | Cómo funciona | Fortalezas | Cuidados |
|---|---|---|---|
| Runners hospedados por la plataforma (GitHub-hosted, Microsoft-hosted, GitLab SaaS) | VM efímera del proveedor | Cero operación | Sin acceso a red privada salvo opciones de red privada de la plataforma; egress no controlado |
| AWS CodeBuild como runner administrado de GitHub Actions | Proyecto CodeBuild conectado a GitHub por webhook de *workflow job*; el job usa `runs-on: codebuild-<proyecto>-${{ github.run_id }}-${{ github.run_attempt }}` | Efímero por job, se ejecuta en la VPC, identidad por rol de servicio IAM, pago por minuto, sin flota que mantener | Límites de concurrencia del proyecto, imagen/tamaño por etiqueta, permisos del rol acotados por repo/ambiente |
| Runners autoescalados en contenedores (ECS/Fargate, AKS, GKE) | Webhook → función/cola → tarea efímera que se registra como runner y termina al acabar | Escala a cero, imagen controlada en registro privado, red privada | Construir imágenes Docker dentro de Fargate no está soportado (usar tipo EC2 o builders remotos); tokens de registro con GitHub App; operación propia |
| Actions Runner Controller (ARC) en Kubernetes | Controlador que crea pods runner por job | Escala fina, multi-equipo | Requiere operar el clúster; aislamiento entre equipos |
| Azure DevOps Managed DevOps Pools / VMSS agents | Pools administrados con inyección en VNet o escalado con VMSS | Acceso privado en Azure, identidad administrada | Sizing y cuotas; imágenes |
| VM self-hosted persistente | Agente instalado en una VM | Simple | Estado residual entre jobs, parcheo, riesgo de persistencia; evitar en banca |

Reglas: runners **efímeros** (un job por runner), en subredes privadas con egress controlado, identidad federada OIDC sin secretos, separación de runners por ambiente/criticidad, imágenes versionadas desde registro privado y registro de auditoría. El diseño del pipeline (stages, escáneres, aprobaciones) pertenece a Vulcano; `17.6` solo fija dónde y con qué identidad corre.

> Nota de fuentes: las entradas de CodeBuild y ECS se basan en la documentación y blogs de AWS indicados en la sección 12. Verifica sintaxis de etiquetas, límites y precios vigentes antes de cerrar el artefacto.

## 10. Vínculo con Well-Architected

`17.6` aporta evidencia directa a estas preguntas de `references/guia-well-architected.md`: REL 2 (topología de red), REL 10 (aislamiento de fallos), REL 13 (DR), SEC 1 (operación segura y cuentas), SEC 2-3 (identidades y permisos de máquinas), SEC 4 (detección), SEC 5 (protección de red), OPS 5-6 (flujo a producción y riesgo de despliegue), COST 8 (transferencia de datos) y SUS 1 (selección de región). Enlaza la fila `08` correspondiente en lugar de repetir el análisis.

## 11. Contenido mínimo de `17.6`

1. Alcance, plataforma existente vs. diseñada y reporte de banderas.
2. Organización y cuentas (tabla de la sección 3) con guardrails.
3. Identidad de máquinas y accesos entre cuentas (ambos lados de cada confianza).
4. Topología de red: patrón elegido con `DA-xxx`, plan de direccionamiento, segmentación y matriz de comunicación permitida/prohibida entre segmentos.
5. Inspección, egress, ingreso, híbrido y DNS.
6. Registro y detección central.
7. Runners de CI/CD (si aplica).
8. Diagramas `17.6.1-Red_<Proveedor>_<Proyecto>.drawio` (un proveedor por archivo) que cumplen `references/drawio-iconos-nube.md` y ambos validadores en modo estricto.
9. Riesgos y costos: cargos fijos de red (CNE, TGW attachments, NAT, firewall, endpoints) incluidos en `17.4.1`.
10. `## Criterios de cierre`.

Criterios de cierre de `17.6`:

- [ ] Cada cuenta/suscripción/proyecto tiene propósito, ambiente, owner y guardrails.
- [ ] Cada `CT-xx` desplegado aparece ubicado en una cuenta y red concretas de `17`.
- [ ] El plan de direccionamiento no tiene solapamientos o el solapamiento está resuelto con PrivateLink/NAT y `DA-xxx`.
- [ ] La matriz de comunicación entre segmentos es explícita y coincide con la política/configuración de red.
- [ ] Toda confianza entre cuentas documenta política de recurso y rol; no hay credenciales de larga duración.
- [ ] Inspección, egress, híbrido y DNS tienen decisión o `No aplica` con motivo.
- [ ] Runners de CI/CD tienen red, identidad y aislamiento definidos, o `No aplica`.
- [ ] No quedan banderas 🔴 abiertas; las 🟡 están en `04` con owner.
- [ ] Los cargos de red están en `17.4.1`.
- [ ] Los `.drawio` `17.6.x` superan `validate_drawio_catalog.py --strict` y `validate_drawio_layout.py --strict`.

## 12. Fuentes

- `aws-samples/aws-cloud-wan-blueprints` — `SKILLS.md`, `policy/`, `infra/` (básico, inspección, Transit Gateway, híbrido, multi-cuenta).
- `arquitecto-java/java-letters-api` — despliegue IaaS con acceso cruzado a ECR mediante perfil de instancia y asunción de rol.
- AWS DevOps Blog: *AWS CodeBuild managed self-hosted GitHub Action runners*; AWS Blog en español: *Escalar las acciones de GitHub con ejecutantes autoalojados en Amazon ECS*.
- AWS Networking Best Practices; AWS Organizations/Control Tower; Azure Landing Zones; Google Cloud resource hierarchy.
