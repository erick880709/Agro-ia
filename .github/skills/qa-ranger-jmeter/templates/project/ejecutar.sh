#!/usr/bin/env bash
# Uso: ./ejecutar.sh <ambiente> [propiedades -J extra...]   p. ej.: ./ejecutar.sh qa -Jusuarios=50
# Requiere: JMETER_HOME (o jmeter en el PATH) y la variable de entorno CLAVE_PRUEBAS.
set -euo pipefail
AMB="${1:?ambiente: local|qa|stg}"; shift || true
JM="${JMETER_HOME:+$JMETER_HOME/bin/}jmeter"
: "${CLAVE_PRUEBAS:?definir CLAVE_PRUEBAS}"
python3 scripts/lint_jmx.py plan.jmx
SAL="resultados/$(date +%Y%m%d-%H%M%S)-$AMB"; mkdir -p "$SAL"
"$JM" -n -t plan.jmx -q "env/$AMB.properties" -Jclave="$CLAVE_PRUEBAS" "$@" \
  -l "$SAL/resultados.jtl" -j "$SAL/jmeter.log" -f -e -o "$SAL/reporte"
ARGS=(--sla sla.json --excluir-inicio "$(grep -E '^rampa=' "env/$AMB.properties" | cut -d= -f2)" --solo-transacciones --md "$SAL/resumen.md" --junit "$SAL/junit-sla.xml")
[ -f "base/$AMB.jtl" ] && ARGS+=(--base "base/$AMB.jtl")
python3 scripts/analizar_jtl.py "$SAL/resultados.jtl" "${ARGS[@]}"
