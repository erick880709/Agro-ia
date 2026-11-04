#!/usr/bin/env bash
# Crea, vía REST API de Azure DevOps, los objetos que el MCP oficial (@azure-devops/mcp) no
# expone ninguna herramienta para gestionar — verificado contra docs/TOOLSET.md del repo
# microsoft/azure-devops-mcp: Variable Groups, Environments y Branch Policies. Este es el
# comportamiento por defecto para platform/azure_devops (no requiere pedirlo explícitamente) —
# ver .claude/skills/vulcano-operador/references/azure-devops.md §Alternativas. La única
# excepción es que el arquitecto pida explícitamente el provider Terraform `microsoft/azuredevops`
# en su lugar — esa es una decisión de alcance de IaC que vuelve a vulcano, no algo que Bob decida.
#
# Idempotente: cada función comprueba primero si el objeto ya existe (por nombre) y lo omite si
# es así, en vez de fallar o duplicar — se puede volver a correr sin efectos secundarios.
#
# Uso:
#   AZDO_PAT=*** ./setup-azure-devops.sh \
#     --org <organizacion> --project <proyecto> --repository-id <guid-del-repo> \
#     --target-branch refs/heads/main \
#     --terraform-variables-file terraform-variables.json \
#     --application-variables-file application-variables.json
#
# Los dos archivos --*-variables-file son JSON con la forma exacta que espera la REST API de
# Variable Groups: {"nombreVariable": {"value": "...", "isSecret": false}, ...} — generarlos vos
# (o el owner de plataforma) a partir de infrastructure-as-code/03-naming-conventions.md; este
# script no inventa nombres de recursos reales, solo crea los objetos con los valores que le dan.
set -euo pipefail

ORG=""
PROJECT=""
REPOSITORY_ID=""
TARGET_BRANCH=""
TERRAFORM_VARIABLES_FILE=""
APPLICATION_VARIABLES_FILE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --org) ORG="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --repository-id) REPOSITORY_ID="$2"; shift 2 ;;
    --target-branch) TARGET_BRANCH="$2"; shift 2 ;;
    --terraform-variables-file) TERRAFORM_VARIABLES_FILE="$2"; shift 2 ;;
    --application-variables-file) APPLICATION_VARIABLES_FILE="$2"; shift 2 ;;
    *) echo "ERROR: argumento desconocido: $1" >&2; exit 1 ;;
  esac
done

: "${AZDO_PAT:?AZDO_PAT es obligatorio (Personal Access Token, con permisos Variable Groups + Environment + Code Read&manage).}"
[ -n "$ORG" ] || { echo "ERROR: --org es obligatorio." >&2; exit 1; }
[ -n "$PROJECT" ] || { echo "ERROR: --project es obligatorio." >&2; exit 1; }
[ -n "$REPOSITORY_ID" ] || { echo "ERROR: --repository-id es obligatorio (GUID, no el nombre)." >&2; exit 1; }
[ -n "$TARGET_BRANCH" ] || { echo "ERROR: --target-branch es obligatorio (ej. refs/heads/main)." >&2; exit 1; }
[ -n "$TERRAFORM_VARIABLES_FILE" ] || { echo "ERROR: --terraform-variables-file es obligatorio." >&2; exit 1; }
[ -n "$APPLICATION_VARIABLES_FILE" ] || { echo "ERROR: --application-variables-file es obligatorio." >&2; exit 1; }
[ -f "$TERRAFORM_VARIABLES_FILE" ] || { echo "ERROR: no existe $TERRAFORM_VARIABLES_FILE." >&2; exit 1; }
[ -f "$APPLICATION_VARIABLES_FILE" ] || { echo "ERROR: no existe $APPLICATION_VARIABLES_FILE." >&2; exit 1; }

AUTH="$(printf ':%s' "$AZDO_PAT" | base64 -w0 2>/dev/null || printf ':%s' "$AZDO_PAT" | base64)"
ORG_URL="https://dev.azure.com/${ORG}"
PROJECT_URL="${ORG_URL}/${PROJECT}"

azdo() {
  # azdo <method> <url> [json-body]
  local method="$1" url="$2" body="${3:-}" response_file http_code curl_status api_message
  local -a curl_args
  response_file="$(mktemp)"
  curl_args=(
    --silent --show-error --output "$response_file" --write-out '%{http_code}'
    -X "$method" "$url"
    -H "Authorization: Basic ${AUTH}"
    -H "Accept: application/json"
    -H "Content-Type: application/json"
  )
  if [ -n "$body" ]; then
    curl_args+=(--data-binary "$body")
  fi

  if http_code="$(curl "${curl_args[@]}")"; then
    :
  else
    curl_status=$?
    echo "ERROR: fallo de transporte llamando Azure DevOps: ${method} ${url} (curl=${curl_status})." >&2
    rm -f "$response_file"
    return "$curl_status"
  fi

  # Azure DevOps puede responder 203 + HTML de login cuando el PAT no autentica. Aunque sea 2xx,
  # no es una respuesta válida de la API y antes terminaba en silencio al fallar el grep posterior.
  if [[ ! "$http_code" =~ ^2[0-9][0-9]$ ]] || [ "$http_code" = "203" ]; then
    api_message="$(grep -oE '"message"[[:space:]]*:[[:space:]]*"[^"]*"' "$response_file" \
      | head -1 | sed -E 's/^"message"[[:space:]]*:[[:space:]]*"//; s/"$//' || true)"
    echo "ERROR: Azure DevOps rechazó ${method} ${url} (HTTP ${http_code})." >&2
    [ -z "$api_message" ] || echo "ERROR: ${api_message}" >&2
    if [ "$http_code" = "203" ] || [ "$http_code" = "401" ] || [ "$http_code" = "403" ]; then
      echo "ERROR: revisa que el PAT pertenezca a personalsoftsas, no esté expirado y tenga Variable Groups (Read, create & manage), Environment (Read & manage) y Code (Read & manage)." >&2
    fi
    rm -f "$response_file"
    return 22
  fi

  cat "$response_file"
  rm -f "$response_file"
}

# --- Variable Groups --------------------------------------------------------
# Ref: POST https://dev.azure.com/{org}/_apis/distributedtask/variablegroups?api-version=7.1
# (a nivel de organización; el scope a un proyecto se hace vía variableGroupProjectReferences,
# no vía la URL — verificado contra Microsoft Learn, no asumido)

variable_group_exists() {
  local name="$1"
  local response
  response="$(azdo GET "${PROJECT_URL}/_apis/distributedtask/variablegroups?groupName=${name}&api-version=7.1")" || return $?
  grep -Eq "\"name\"[[:space:]]*:[[:space:]]*\"${name}\"" <<< "$response"
}

create_variable_group() {
  local name="$1" description="$2" variables_file="$3"
  local exists_status
  if variable_group_exists "$name"; then
    echo "Variable Group '${name}' ya existe — omitido."
    return 0
  else
    exists_status=$?
    [ "$exists_status" -eq 1 ] || return "$exists_status"
  fi
  local project_id project_json variables_json body
  project_json="$(azdo GET "${ORG_URL}/_apis/projects/${PROJECT}?api-version=7.1")" || return $?
  project_id="$(printf '%s' "$project_json" | grep -o '"id": *"[^"]*"' | head -1 | cut -d'"' -f4 || true)"
  [ -n "$project_id" ] || {
    echo "ERROR: Azure DevOps no devolvió el id del proyecto '${PROJECT}'. Verifica el nombre del proyecto y el acceso del PAT." >&2
    return 1
  }
  variables_json="$(cat "$variables_file")"
  body=$(cat <<JSON
{
  "name": "${name}",
  "description": "${description}",
  "type": "Vsts",
  "variables": ${variables_json},
  "variableGroupProjectReferences": [
    { "name": "${name}", "description": "${description}", "projectReference": { "id": "${project_id}", "name": "${PROJECT}" } }
  ]
}
JSON
)
  azdo POST "${ORG_URL}/_apis/distributedtask/variablegroups?api-version=7.1" "$body" > /dev/null
  echo "Variable Group '${name}' creado."
}

# --- Environments ------------------------------------------------------------
# Ref: POST https://dev.azure.com/{org}/{project}/_apis/distributedtask/environments?api-version=7.1
# Devuelve { id, name, ... } — el id numerico es el que se carga como prodEnvironmentId* en el
# Variable Group de aplicación.

get_environment_id() {
  local name="$1"
  local response id
  response="$(azdo GET "${PROJECT_URL}/_apis/distributedtask/environments?name=${name}&api-version=7.1")" || return $?
  id="$(printf '%s' "$response" | grep -o '"id": *[0-9]*' | head -1 | grep -o '[0-9]*' || true)"
  [ -n "$id" ] || return 1
  printf '%s' "$id"
}

create_environment() {
  local name="$1" description="$2"
  local existing_id lookup_status
  if existing_id="$(get_environment_id "$name")"; then
    echo "Environment '${name}' ya existe (id=${existing_id}) — omitido." >&2
    printf '%s' "$existing_id"
    return 0
  else
    lookup_status=$?
    [ "$lookup_status" -eq 1 ] || return "$lookup_status"
  fi
  local body id
  body=$(cat <<JSON
{ "name": "${name}", "description": "${description}" }
JSON
)
  id="$(azdo POST "${PROJECT_URL}/_apis/distributedtask/environments?api-version=7.1" "$body" \
    | grep -o '"id": *[0-9]*' | head -1 | grep -o '[0-9]*')"
  [ -n "$id" ] || { echo "ERROR: Azure DevOps creó '${name}' pero no devolvió su id." >&2; return 1; }
  echo "Environment '${name}' creado (id=${id})." >&2
  printf '%s' "$id"
}

# --- Branch policy: minimum reviewers ---------------------------------------
# Ref: POST https://dev.azure.com/{org}/{project}/_apis/policy/configurations?api-version=7.1
# Type id fa4e907d-c16b-4a4c-9dfa-4906e5d171dd = "Minimum approval count" (verificado contra el
# ejemplo oficial de Microsoft Learn).

branch_policy_min_reviewers_exists() {
  local ref_name="$1"
  local response
  response="$(azdo GET "${PROJECT_URL}/_apis/policy/configurations?api-version=7.1")" || return $?
  grep -Eq "\"refName\"[[:space:]]*:[[:space:]]*\"${ref_name}\"" <<< "$response"
}

create_branch_policy_min_reviewers() {
  local ref_name="$1" minimum="$2"
  local exists_status
  if branch_policy_min_reviewers_exists "$ref_name"; then
    echo "Branch policy (minimum reviewers) para '${ref_name}' ya existe — omitida."
    return 0
  else
    exists_status=$?
    [ "$exists_status" -eq 1 ] || return "$exists_status"
  fi
  local body
  body=$(cat <<JSON
{
  "isEnabled": true,
  "isBlocking": true,
  "type": { "id": "fa4e907d-c16b-4a4c-9dfa-4906e5d171dd" },
  "settings": {
    "minimumApproverCount": ${minimum},
    "creatorVoteCounts": false,
    "scope": [
      { "repositoryId": "${REPOSITORY_ID}", "refName": "${ref_name}", "matchKind": "exact" }
    ]
  }
}
JSON
)
  azdo POST "${PROJECT_URL}/_apis/policy/configurations?api-version=7.1" "$body" > /dev/null
  echo "Branch policy (minimum ${minimum} reviewer(s)) creada para '${ref_name}'."
}

echo "== Variable Groups =="
create_variable_group "__TERRAFORM_VARIABLE_GROUP__" \
  "Backend Terraform: service connections por ambiente" \
  "$TERRAFORM_VARIABLES_FILE"
create_variable_group "__APPLICATION_VARIABLE_GROUP__" \
  "Pipelines de aplicacion: nombres reales, health checks, notificaciones, environment IDs" \
  "$APPLICATION_VARIABLES_FILE"

echo
echo "== Environments =="
# __ENVIRONMENT_CREATION_CALLS__

echo
echo "== Branch policy (minimo __MIN_REVIEWERS__ revisor(es)) =="
create_branch_policy_min_reviewers "$TARGET_BRANCH" __MIN_REVIEWERS__

echo
echo "== Listo. Cargar estos Environment id en __APPLICATION_VARIABLE_GROUP__ =="
# __ENVIRONMENT_ID_SUMMARY__
