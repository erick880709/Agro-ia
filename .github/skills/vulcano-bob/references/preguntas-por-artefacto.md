# Preguntas operativas por artefacto

Consultar únicamente lo que no pueda derivarse del manifiesto, documentos o repositorio. Si el
usuario pidió generar todo, no pausar entre artefactos por preguntas no bloqueantes: registrar un
`OP-NNN` y continuar donde sea seguro.

## Regla de decisión

- Si cambia arquitectura, SKU, topología, seguridad o dependencias: bloquear y devolver a
  Vulcano.
- Si es un identificador operativo que puede parametrizarse: crear `OP-NNN`, generar un parámetro
  requerido y continuar.
- Si falta un comando necesario para que un pipeline sea ejecutable: bloquear ese pipeline. Un
  comentario o placeholder no cuenta como implementación.
- Nunca preguntar si “sigue vigente” una decisión sin evidencia de drift.

## Bootstrap

- Suscripción/tenant/cuenta donde se ejecutará manualmente.
- Región y nombres solo cuando el documento no los determine.
- Confirmar si el script crea o reutiliza el Resource Group únicamente si la fuente es ambigua.

El script debe recibir los datos desconocidos como argumentos o variables de entorno obligatorias
y fallar si faltan. No insertar valores entre `<...>`.

## Módulos y ambientes

No hacer preguntas si inputs, outputs y valores por ambiente están definidos. Para un `PD-NNN`
abierto, preguntar solo si no puede representarse como variable requerida. Los nombres de Service
Connections no pertenecen a módulos Terraform.

Para observabilidad, bloquear si faltan receivers reales del Action Group o si una alerta no tiene
scope/condición suficientes. Los receivers pueden ser `OP-NNN`; severidad, umbral y ventana son
diseño y deben volver a Vulcano.

## Pipeline de IaC

- Nombres de Service Connections y Environments, si no están documentados: `OP-NNN` y parámetros
  de pipeline obligatorios.
- Mecanismo aprobado para instalar `terraform`, `tflint` y `trivy` (o `tfsec`/`checkov`) en el
  agente.
- Constraint aprobado de Terraform/providers, estándar `internal` o `avm`, acceso Registry/MCP y
  estrategia `plan_mock` o `plan_mock_and_integration`.
- Para módulos: escenarios y aserciones que deben cubrir los `.tftest.hcl`; no inventar pruebas
  apply dentro del flujo local de Bob.
- Ubicación exacta del pipeline solo cuando los documentos no la indiquen.

El transporte del plan entre jobs no es una pregunta: publicar y descargar el mismo artefacto es
un requisito técnico.

## Pipeline de aplicación

Antes de preguntar, inspeccionar `package.json`, scripts existentes y definición de CI/CD. Solo son
preguntas válidas:

- comando real de secret scanning si la definición no seleccionó uno;
- comando o task real de empaquetado/despliegue si no existe en el repositorio ni en la estrategia;
- nombres operativos de Service Connection/Environments.
- nombres reales de los App Services backend/frontend por ambiente, si no pueden derivarse de
  outputs Terraform publicados para el pipeline.

Si falta un comando de seguridad o despliegue obligatorio, el pipeline queda `conflict`; no usar
`TODO`, `<placeholder>` ni un comando inventado.
