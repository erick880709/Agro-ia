"""Sentinel local: no conexión remota; ejecutar deja evidencia local."""
from pathlib import Path
Path(__file__).with_name('APPLIED.txt').write_text('attempted', encoding='utf-8')
