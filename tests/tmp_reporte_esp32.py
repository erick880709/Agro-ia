"""Reporte demo: flujo completo con la trama real del ESP32 (sin BD)."""
import asyncio
import sys

sys.path.insert(0, "apps/shared")
sys.path.insert(0, "apps/backend")

from agroia_backend.seeds.reglas import REGLAS_POR_CULTIVO, REGLAS_UNIVERSALES
from agroia_backend.services.normalizacion_iot import normalizar_trama
from agroia_backend.services.rules_engine import RulesEngine

TRAMA_ESP32 = {
    "device_id": "esp32-npk-001",
    "humidity": 84.7,
    "temperature": 22.6,
    "conductivity": 44.0,
    "ph": 7.1,
    "nitrogen": 1.0,
    "phosphorus": 3.0,
    "potassium": 7.0,
    "rssi": -22,
    "uptime_s": 2048,
}


def _a_regla(r, cultivo_id):
    """Convierte seed (min/max) al formato interno de load_rules (umbral_min/max)."""
    return {
        "id": "r-demo",
        "variable": r["variable"],
        "umbral_min": r.get("min"),
        "umbral_max": r.get("max"),
        "accion": r["accion"],
        "prioridad": r["prioridad"],
        "fuente": r["fuente"],
        "version": 1,
        "cultivo_id": cultivo_id,
    }


REGLAS_DEMO = [_a_regla(r, None) for r in REGLAS_UNIVERSALES]
CULTIVO_IDS = {"Café": "c1", "Maíz": "c2", "Arroz": "c3", "Plátano": "c4", "Papa": "c5"}
for nombre, reglas in REGLAS_POR_CULTIVO.items():
    REGLAS_DEMO += [_a_regla(r, CULTIVO_IDS[nombre]) for r in reglas]


class DemoRulesEngine(RulesEngine):
    """RulesEngine real con reglas en memoria (misma lógica de evaluación)."""

    def __init__(self, reglas):
        super().__init__(db_session=None, redis_client=None)
        self._reglas = reglas

    async def load_rules(self, cultivo_id=None):
        return [
            r for r in self._reglas
            if r["cultivo_id"] is None or r["cultivo_id"] == cultivo_id
        ]


class FakeCultivo:
    def __init__(self, cid, nombre, icono):
        self.id, self.nombre, self.icono = cid, nombre, icono


async def main():
    from agroia_backend.services.aptitud import AptitudService

    engine = DemoRulesEngine(REGLAS_DEMO)

    # ── 1. Ingesta: normalizar la trama real ──
    payload, advertencias = normalizar_trama(TRAMA_ESP32)
    print("PAYLOAD CANÓNICO:", payload)
    print("ADVERTENCIAS NORMALIZACIÓN:", advertencias)
    print("CALIDAD LECTURA: npk_no_calibrado")
    print(f"COBERTURA: {len(payload)}/18 variables de suelo\n")

    # ── 2. UC2: diagnóstico para Café ──
    res_cafe = await engine.evaluate(payload, CULTIVO_IDS["Café"])
    print("UC2 - CAFÉ")
    print("  status:", res_cafe.status, "| violaciones:", len(res_cafe.violations),
          "| warnings:", len(res_cafe.warnings))
    for v in res_cafe.violations + res_cafe.warnings:
        estado = "EXCESO" if (v.valor_actual is not None and v.umbral_max is not None
                              and v.valor_actual > v.umbral_max) else "DEFICIT"
        print(f"  - {v.variable}: {v.valor_actual} fuera de [{v.umbral_min}-{v.umbral_max}] "
              f"→ {estado} ({v.prioridad}) → {v.accion[:60]}...")
    clasif = "No apta" if res_cafe.is_blocked else ("Moderadamente apta" if res_cafe.has_violations else "Apta")
    print("  Clasificación:", clasif)

    # ── 3. UC1: ¿qué sembrar? ──
    class AptFake(AptitudService):
        async def _cultivos_evaluables(self):
            return [
                (FakeCultivo(CULTIVO_IDS[n], n, "🌱"), len(REGLAS_POR_CULTIVO[n]))
                for n in REGLAS_POR_CULTIVO
            ]

    apt = AptFake(None, engine)
    sugerencias = await apt.recommend_crops(payload, top_n=5)
    print("\nUC1 - RANKING DE CULTIVOS (sin siembra)")
    for s in sugerencias:
        print(f"  {s['cultivo']:8s} score={s['score']:5} confianza={s['confianza']:.3f} "
              f"{s['clasificacion']:20s} ajustes={len(s['ajustes'])}")

    print("\nRESUMEN FINAL:")
    print("  - pH 7.1: OK universal (5.0-7.5), alto para cultivos específicos")
    print("  - CE 0.044 dS/m: OK (no salino)")
    print("  - NPK: lecturas sin calibrar → no confiables")
    print("  - Faltan: materia_organica, CIC, textura, micros")


if __name__ == "__main__":
    asyncio.run(main())
