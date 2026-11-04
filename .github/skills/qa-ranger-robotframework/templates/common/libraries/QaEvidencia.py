"""Evidencia QA Ranger para Robot Framework.

Organiza la evidencia real de cada caso en
``<QA_ROOT>/test-results/<QA_RUN_ID>/<CASE-ID>/attempt-<QA_ATTEMPT>/`` para que
``ctrf_from_robot.py`` (o ``attach-evidence.mjs``) la enlace al CTRF.
Solo usa la biblioteca estándar de Python: funciona en agentes sin dependencias extra.
"""
import os
import re
import shutil
import socket
import time
import zipfile
from pathlib import Path

from robot.api import logger
from robot.api.deco import keyword, library
from robot.libraries.BuiltIn import BuiltIn

CASO = re.compile(r"^((?:TC|SEC|FRAUD|API|A11Y|UT|PERF)-\d+)\b")
CASO_TAG = re.compile(r"^(?:TC|SEC|FRAUD|API|A11Y|UT|PERF)-\d+$", re.I)


def _usuario_del_sistema():
    """Usuario real del proceso. No usa getpass.getuser(): ese lee $USER y devolvería el valor inyectado."""
    try:
        import pwd
        return pwd.getpwuid(os.getuid()).pw_name
    except (ImportError, KeyError):
        try:
            return os.getlogin()
        except OSError:
            return None


@library(scope="GLOBAL", auto_keywords=False)
class QaEvidencia:
    """Keywords de evidencia y guardas de entorno de la familia QA Ranger."""

    def __init__(self, raiz=None, run_id=None):
        self.raiz = Path(raiz or os.environ.get("QA_ROOT") or Path.cwd() / "resources" / "qa").resolve()
        self.run_id = run_id or os.environ.get("QA_RUN_ID") or time.strftime("run-%Y%m%d-%H%M%S")
        self.intento = os.environ.get("QA_ATTEMPT", "0")

    @keyword("Id Del Caso Actual")
    def id_del_caso(self):
        """Devuelve el ID del caso (TC-01, API-03...) desde el nombre del test o sus tags."""
        bi = BuiltIn()
        nombre = bi.get_variable_value("${TEST NAME}", "")
        m = CASO.match(nombre or "")
        if m:
            return m.group(1)
        for tag in bi.get_variable_value("@{TEST TAGS}", []) or []:
            if CASO_TAG.match(tag):
                return tag.upper()
        raise AssertionError(f"El test '{nombre}' no tiene ID de caso (TC-01 [critical] ...): sin ID no hay trazabilidad de evidencia.")

    @keyword("Carpeta De Evidencia Del Caso")
    def carpeta(self):
        """Crea (si falta) y devuelve la carpeta absoluta de evidencia del caso e intento actuales."""
        destino = self.raiz / "test-results" / self.run_id / self.id_del_caso() / f"attempt-{self.intento}"
        destino.mkdir(parents=True, exist_ok=True)
        return str(destino)

    @keyword("Mover Video Al Caso")
    def mover_video(self, origen):
        """Mueve el video que grabó el navegador a ``video.<ext>`` en la carpeta del caso.

        El video existe solo después de cerrar el contexto. Sin video (navegador remoto o
        grabación deshabilitada) deja un aviso: el faltante se declara, no se inventa.
        """
        if not origen or not Path(origen).is_file():
            logger.warn(f"No hay video para {self.id_del_caso()}: la política de evidencia queda incompleta.")
            return ""
        destino = Path(self.carpeta()) / f"video{Path(origen).suffix or '.webm'}"
        shutil.move(origen, destino)
        return str(destino)

    @keyword("Guardar Traza Selenium")
    def traza_selenium(self):
        """Empaqueta en ``trace.zip`` el page source, la URL y los logs de consola de SeleniumLibrary.

        No es un trace de Playwright: es la traza diagnóstica disponible en WebDriver.
        """
        carpeta = Path(self.carpeta())
        try:
            driver = BuiltIn().get_library_instance("SeleniumLibrary").driver
        except Exception as error:  # sin navegador abierto no hay traza que guardar
            logger.warn(f"Sin sesión WebDriver para la traza: {error}")
            return ""
        archivo = carpeta / "trace.zip"
        with zipfile.ZipFile(archivo, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("url.txt", driver.current_url)
            z.writestr("page_source.html", driver.page_source)
            try:
                logs = driver.get_log("browser")
                z.writestr("console.log", "\n".join(f"{e.get('level')} {e.get('message')}" for e in logs))
            except Exception:
                z.writestr("console.log", "El driver no expone logs de consola.")
        return str(archivo)

    @keyword("Verificar Variables De Entorno")
    def verificar_entorno(self, *nombres):
        """Falla si alguna variable no existe, está vacía o conserva el valor del sistema operativo.

        En agentes Linux ``%{USER}`` y ``%{HOST}`` pueden existir aunque el pipeline no inyecte
        el secreto; entonces Robot usaría el usuario del agente sin fallar.
        """
        usuario = _usuario_del_sistema()
        sistema = {"USER": usuario, "USERNAME": usuario, "LOGNAME": usuario,
                   "HOST": socket.gethostname(), "HOSTNAME": socket.gethostname()}
        problemas = []
        for n in nombres:
            valor = os.environ.get(n)
            if valor is None or not valor.strip():
                problemas.append(f"{n}: no definida o vacía")
            elif n.upper() in sistema and valor == sistema[n.upper()]:
                problemas.append(f"{n}: tiene el valor del agente ({valor}); el pipeline no la inyectó")
        if problemas:
            raise AssertionError("Variables de entorno inválidas (nombres en MAYÚSCULA en Linux): " + "; ".join(problemas))
        logger.info("Variables verificadas: " + ", ".join(nombres))
