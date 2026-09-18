"""Seed del conjunto de parámetros semilla de costeo (AGC-COST · F1).

Ejecutar:
    python scripts/seed_costeo.py

Crea el conjunto publicado vigente con los valores ilustrativos del estudio
de tarifas (RFP §15): tarifa base $100.000, tramos 1–15/$15.000,
16–30/$10.000, 31+/$7.000 y factor de dificultad 0/15/30%. Idempotente.
"""

import asyncio
import os

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from agroia_backend.services.costeo_seed import asegurar_conjunto_semilla  # noqa: E402


async def main() -> None:
    resumen = await asegurar_conjunto_semilla()
    if resumen["creado"]:
        print(f"✅ Conjunto semilla de costeo creado: {resumen['conjunto_id']}")
    else:
        print(f"♻️  Conjunto semilla ya existía: {resumen['conjunto_id']}")


if __name__ == "__main__":
    asyncio.run(main())
