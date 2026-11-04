# Seguridad de IA: LLM, agentes, MCP y skills

Aplica cuando el código invoca modelos, construye prompts, expone herramientas a un
agente, usa RAG/memoria o cuando el objeto de análisis son skills/plugins/servidores MCP
(incluidas las del propio ecosistema: archi, builder, code-review, terragrunt-iac, aegis).
Si archi declaró `Aplicabilidad agentic: Sí`, la matriz `ASI01`–`ASI10` de `19.1` es el
contrato a verificar.

Inspirado en OWASP Top 10 LLM 2025, OWASP Agentic 2026, la temporada de agentes del
GitHub Secure Code Game y las auditorías `prompt-injection` y `agent-supply-chain-audit`.

## Tabla de contenido

1. Mapa de la superficie
2. Construcción del prompt (LLM01, LLM07)
3. Manejo de la salida (LLM05)
4. Herramientas y agencia (LLM06, ASI02, ASI03, ASI05)
5. Memoria, RAG y contexto (LLM04, LLM08, ASI06)
6. Multiagente y A2A (ASI07, ASI08)
7. Supervisión humana (ASI09) y contención (ASI10)
8. Consumo (LLM10)
9. Cadena de suministro de agentes: skills, plugins, MCP (LLM03, ASI04)
10. Pruebas defensivas

## 1. Mapa de la superficie

Para cada llamada a modelo: qué entra al contexto (usuario, documentos, web, salidas de
herramientas, memoria), con qué identidad actúa el agente, qué herramientas puede
invocar, qué efectos tienen (lectura, escritura, dinero, comunicación externa) y quién
aprueba. **Regla:** todo texto que el modelo lee y que un tercero pudo escribir es un
canal de instrucciones del atacante (inyección indirecta).

## 2. Construcción del prompt

- Entrada de usuario concatenada al system prompt sin separación; datos externos sin
  marcar como datos. Delimitar ayuda pero **no es un control de seguridad**: el control
  real es limitar lo que el modelo puede hacer con lo que lee.
- Secretos, credenciales, URLs internas o reglas de autorización en el system prompt
  (LLM07): el system prompt se filtra; la autorización no puede vivir ahí.
- Instrucciones ocultas en contenido (Unicode invisible, comentarios HTML, texto blanco,
  alt de imágenes): busca caracteres de formato (`U+200B`–`U+200F`, `U+2060`–`U+2064`,
  `U+E0000`–`U+E007F` tags) en archivos que alimentan agentes.

## 3. Manejo de la salida

Salida del modelo hacia `eval`, shell, SQL, plantillas, HTML/Markdown renderizado,
URLs (exfiltración vía imágenes/links con datos en query), deserialización o llamadas
HTTP → se trata como entrada no confiable: validación de esquema estricta (JSON Schema/
structured outputs), lista blanca de acciones, parametrización y sanitización.

## 4. Herramientas y agencia

- **Mínima agencia:** cada herramienta con el menor alcance posible; nada de "ejecutar
  comando" o "consulta SQL libre" cuando basta una operación específica.
- **Identidad:** la herramienta actúa con la identidad y permisos del **usuario final**
  (delegación con scopes acotados), no con una cuenta de servicio amplia (confused deputy).
- **Validación de argumentos** server-side, tipos estrictos, límites de tamaño, y
  autorización por recurso igual que en una API (BOLA aplica a tools).
- **Efectos irreversibles** (pagos, transferencias, borrados, envíos externos):
  confirmación humana con contexto suficiente, idempotencia y registro de auditoría.
- **Ejecución de código** (ASI05): sandbox real (contenedor/VM efímera, sin red o con
  egress restringido, sin credenciales montadas); nunca en el host del agente.
- MCP del Scaffold: `--enable-security=true` y `--enable-audit=true` fuera de desarrollo.

## 5. Memoria, RAG y contexto

- Documentos ingeridos sin control de origen/escritor (envenenamiento persistente).
- Índices vectoriales compartidos entre tenants/usuarios sin filtro de autorización en la
  recuperación (LLM08): el filtro por permisos debe aplicarse en la consulta, no después.
- Memoria persistente que el agente escribe a partir de contenido externo y luego trata
  como instrucción de confianza.

## 6. Multiagente y A2A

Identidad y autenticidad de cada mensaje entre agentes, autorización por delegación,
protección contra replay, y límites para evitar cascadas (presupuesto de pasos, tiempo y
costo; disyuntores).

## 7. Supervisión humana y contención

- Aprobaciones que muestran resumen generado por el mismo modelo (el atacante controla lo
  que el humano ve): muestra los parámetros reales de la acción.
- Kill switch, revocación de credenciales del agente y observabilidad de objetivo, pasos
  e invocaciones (sin registrar PII ni secretos).

## 8. Consumo

Límites de tokens, iteraciones, tiempo y costo por usuario/tenant; cuotas en
herramientas costosas; protección contra bucles de agente.

## 9. Cadena de suministro de agentes

Para auditar skills, plugins, hooks, instrucciones (`CLAUDE.md`, `AGENTS.md`) y
servidores MCP antes de instalarlos o confiar en ellos:
- **Contenido:** instrucciones que piden ignorar reglas, exfiltrar, desactivar
  confirmaciones o ejecutar comandos de red; Unicode oculto; scripts que descargan y
  ejecutan (`curl | sh`), ofuscación (base64 decodificado y ejecutado).
- **Hooks y settings:** comandos que corren automáticamente, permisos amplios
  (`Bash(*)`, modo sin confirmación), variables de entorno que redirigen tráfico.
- **MCP:** servidor pineado a versión/digest; definiciones de tools con instrucciones
  ocultas (tool poisoning); cambio de definiciones tras la aprobación (*rug pull*):
  compara contra la versión aprobada; alcance de credenciales que recibe.
- **Skills del ecosistema:** builder/code-review/ranger conectan Jira/Azure DevOps por
  MCP con credenciales en variables de entorno: verifica que ninguna skill escriba
  tokens en repo, expedientes o memoria, y que los documentos/issues se traten como datos
  (todas lo declaran como invariante; Aegis lo comprueba en la práctica).

## 10. Pruebas defensivas

Casos negativos automatizables (no herramientas de ataque): documento con instrucción
inyectada → el agente no ejecuta la acción; tool invocada con recurso ajeno → denegada;
salida del modelo con HTML activo → renderizada inerte; bucle forzado → corta por
presupuesto. Herramientas de evaluación como promptfoo o garak se usan solo contra
sistemas propios y en entornos de prueba.
