#!/usr/bin/env bash
# Notifica el resultado de un despliegue a Slack o Teams vía webhook entrante. El pipeline que
# invoca este script decide `PIPELINE_STATUS` explícitamente (dos steps/jobs condicionados a
# success/failure) en vez de que este script intente adivinar el resultado agregado de etapas
# previas — evita depender de expresiones de dependencia entre stages que varían por versión de
# plataforma. Ver references/dora-collector.md para el mismo criterio de detección de plataforma.
set -euo pipefail

: "${NOTIFICATION_CHANNEL:?NOTIFICATION_CHANNEL es obligatorio (slack|teams).}"
: "${NOTIFICATION_WEBHOOK_URL:?NOTIFICATION_WEBHOOK_URL es obligatorio.}"
: "${PIPELINE_STATUS:?PIPELINE_STATUS es obligatorio (success|failure).}"

case "$NOTIFICATION_CHANNEL" in
  slack|teams) ;;
  *) echo "ERROR: NOTIFICATION_CHANNEL debe ser slack o teams (recibido \"$NOTIFICATION_CHANNEL\")." >&2; exit 1 ;;
esac

case "$PIPELINE_STATUS" in
  success|failure) ;;
  *) echo "ERROR: PIPELINE_STATUS debe ser success o failure (recibido \"$PIPELINE_STATUS\")." >&2; exit 1 ;;
esac

detect_run_url() {
  if [ "${GITHUB_ACTIONS:-}" = "true" ]; then
    echo "${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-}/actions/runs/${GITHUB_RUN_ID:-}"
  elif [ "${GITLAB_CI:-}" = "true" ]; then
    echo "${CI_PROJECT_URL:-}/-/pipelines/${CI_PIPELINE_ID:-}"
  elif [ "${TF_BUILD:-}" = "True" ]; then
    echo "${SYSTEM_COLLECTIONURI:-}${SYSTEM_TEAMPROJECT:-}/_build/results?buildId=${BUILD_BUILDID:-}"
  else
    echo ""
  fi
}

repository_label="${BUILD_REPOSITORY_NAME:-${GITHUB_REPOSITORY:-${CI_PROJECT_NAME:-}}}"
run_url="$(detect_run_url)"

if [ "$PIPELINE_STATUS" = "success" ]; then
  summary="✅ Despliegue exitoso — ${repository_label}"
else
  summary="❌ Despliegue con fallo — ${repository_label}"
fi
if [ -n "$run_url" ]; then
  summary="${summary} (${run_url})"
fi

# Payload mínimo `{"text": "..."}` — válido tanto para Slack Incoming Webhooks como para el
# conector clásico de Teams (Office 365 Connector, esquema MessageCard con campo `text`). Si se
# necesita un formato enriquecido (color, secciones), extenderlo aquí sin cambiar el contrato de
# variables de entorno.
escaped_summary=$(printf '%s' "$summary" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g')
payload=$(printf '{"text": "%s"}' "$escaped_summary")

curl --fail --silent --show-error \
  -H 'Content-Type: application/json' \
  -d "$payload" \
  "$NOTIFICATION_WEBHOOK_URL"
