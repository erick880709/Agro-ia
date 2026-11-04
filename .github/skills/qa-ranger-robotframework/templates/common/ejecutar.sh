#!/usr/bin/env bash
# Ejecuta la suite con el flujo QA Ranger: lint -> dry run -> robot -> reintento opcional -> CTRF + RTM.
# Uso: ./ejecutar.sh [ambiente] [opciones de robot...]     p. ej. ./ejecutar.sh qa --include smoke
# Variables: QA_RUN_ID (por defecto run-<fecha>), QA_ROOT (resources/qa), REINTENTOS (0|1).
set -euo pipefail
cd "$(dirname "$0")"
AMBIENTE="${1:-__ENV__}"; [ $# -gt 0 ] && shift
export QA_RUN_ID="${QA_RUN_ID:-run-$(date +%Y%m%d-%H%M%S)}"
export QA_ROOT="${QA_ROOT:-$PWD/resources/qa}"
export QA_ATTEMPT=0
if [ -f .env.qa ]; then set -a; . ./.env.qa; set +a; fi
SALIDA="$QA_ROOT/test-results/$QA_RUN_ID"
REPORTES="$QA_ROOT/reports/$QA_RUN_ID"
VARS=(__VARFILE_ARGS__)
mkdir -p "$SALIDA" "$REPORTES"

echo "== Lint (gate: bloqueantes detienen la ejecución)"
python tools/lint_robot.py __SUITES__ --rf __RF_MAJOR__

echo "== Dry run (keywords, imports y argumentos)"
python -m robot --dryrun --output NONE --report NONE --log NONE "${VARS[@]}" "$@" __TESTS__

echo "== Ejecución $QA_RUN_ID"
set +e
python -m robot --outputdir "$SALIDA" --xunit xunit.xml "${VARS[@]}" "$@" __TESTS__
RC=$?
OUTPUTS=(--output "$SALIDA/output.xml")
if [ "$RC" -ne 0 ] && [ "${REINTENTOS:-0}" = "1" ]; then
  echo "== Reintento de fallidos (se reporta como reintento, no se oculta)"
  QA_ATTEMPT=1 python -m robot --rerunfailed "$SALIDA/output.xml" --outputdir "$SALIDA" --output rerun1.xml \
    --log rerun1-log.html --report rerun1-report.html "${VARS[@]}" "$@" __TESTS__
  RC=$?
  OUTPUTS+=(--output "$SALIDA/rerun1.xml")
fi
set -e

echo "== CTRF y trazabilidad"
python tools/ctrf_from_robot.py "${OUTPUTS[@]}" --out "$REPORTES/ctrf.json" --evidencia "$SALIDA" __PROYECTO_ARG__ --project-root "$PWD"
python tools/rtm_from_robot.py "$SALIDA/output.xml" --out "$REPORTES/rtm.md"
echo "Resultados: $SALIDA (log.html, report.html, output.xml) · CTRF: $REPORTES/ctrf.json"
exit "$RC"
