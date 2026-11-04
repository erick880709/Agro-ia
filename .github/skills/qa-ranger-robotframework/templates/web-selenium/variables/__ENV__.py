"""Variables del ambiente __ENV__. Sin secretos: usuario y clave llegan por %{E2E_USER} y %{E2E_PASSWORD}."""
BASE_URL = "__BASE_URL__"
BROWSER = "headlesschrome"   # chrome para ver el navegador; headlessfirefox; Edge headless vía OPCIONES
OPCIONES = "add_argument('--window-size=1280,800')"
GRID_URL = None              # p. ej. "http://localhost:4444" (docker-selenium) o la URL de la nube
TIMEOUT = "10s"
