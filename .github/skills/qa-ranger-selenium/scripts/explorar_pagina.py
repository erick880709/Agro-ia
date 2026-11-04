#!/usr/bin/env python3
"""
Inventario de elementos interactivos de una página real con localizadores sugeridos
(principio: explorar antes de automatizar; nunca inventar localizadores).

Uso:
  python explorar_pagina.py --url https://qa.app.com/transferencias/nueva \
      [--login-url https://qa.app.com/login --campo-usuario usuario --campo-clave clave --boton "Ingresar"] \
      [--headed] [--json]
Credenciales para el login: variables de entorno E2E_USER / E2E_PASSWORD.
Driver: Selenium Manager (o CHROMEDRIVER_PATH); navegador: el instalado (o CHROME_BINARY).

Para cada elemento sugiere un localizador según la jerarquía de la skill:
id estable > data-testid > name > CSS semántico > XPath por etiqueta/texto. Marca ids que parecen autogenerados.
"""
import argparse
import signal
import json
import os
import re
import sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

JS = r"""
const out = [];
const sel = 'a[href],button,input,select,textarea,[role=button],[role=link],[role=tab],[role=checkbox],[role=combobox],[role=alert],[role=dialog],[data-testid],h1,h2,table';
for (const el of document.querySelectorAll(sel)) {
  const r = el.getBoundingClientRect();
  const visible = !!(r.width || r.height) && getComputedStyle(el).visibility !== 'hidden';
  let label = '';
  if (el.id) { const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`); if (l) label = l.innerText.trim(); }
  if (!label && el.closest('label')) label = el.closest('label').innerText.replace(el.value || '', '').trim();
  out.push({
    tag: el.tagName.toLowerCase(), type: el.getAttribute('type') || '', id: el.id || '',
    name: el.getAttribute('name') || '', testid: el.getAttribute('data-testid') || '',
    role: el.getAttribute('role') || '', aria: el.getAttribute('aria-label') || '',
    label: label.split('\n')[0].slice(0, 60), text: (el.innerText || el.value || '').trim().split('\n')[0].slice(0, 60),
    visible, enShadow: false, iframe: false
  });
}
out.push({tag: '#meta', iframes: document.querySelectorAll('iframe').length,
          shadowHosts: [...document.querySelectorAll('*')].filter(e => e.shadowRoot).length});
return out;
"""

AUTOGEN = re.compile(r"(\d{3,}|^(ember|mat-|ng-|react-|:r|__)|[a-f0-9]{8,})", re.I)


def sugerir(e):
    q = lambda s: s.replace("'", "\\'")
    if e["id"] and not AUTOGEN.search(e["id"]):
        return f'By.id("{e["id"]}")'
    if e["testid"]:
        return f'By.cssSelector("[data-testid=\'{e["testid"]}\']")'
    if e["name"]:
        return f'By.name("{e["name"]}")'
    if e["tag"] in ("button", "a") and e["text"]:
        return f'By.xpath("//{e["tag"]}[normalize-space()=\'{q(e["text"])}\']")'
    if e["label"] and e["tag"] in ("input", "select", "textarea"):
        return f'By.xpath("//label[normalize-space()=\'{q(e["label"])}\']//{e["tag"]}") (o //{e["tag"]}[@id=//label[...]/@for])'
    if e["aria"]:
        return f'By.cssSelector("[aria-label=\'{q(e["aria"])}\']")'
    if e["role"]:
        return f'By.cssSelector("[role=\'{e["role"]}\']")'
    if e["tag"] in ("h1", "h2") and e["text"]:
        return f'By.xpath("//{e["tag"]}[normalize-space()=\'{q(e["text"])}\']")'
    return "⚠ sin atributo estable: pedir data-testid a desarrollo"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True)
    ap.add_argument("--login-url")
    ap.add_argument("--campo-usuario", default="usuario")
    ap.add_argument("--campo-clave", default="clave")
    ap.add_argument("--boton", default="Ingresar")
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    o = webdriver.ChromeOptions()
    if not a.headed:
        o.add_argument("--headless=new")
    o.add_argument("--window-size=1920,1080")
    if os.getenv("CHROME_BINARY"):
        o.binary_location = os.environ["CHROME_BINARY"]
    if os.getenv("CONTAINER") == "true":
        o.add_argument("--no-sandbox"); o.add_argument("--disable-dev-shm-usage")
    svc = Service(os.environ["CHROMEDRIVER_PATH"]) if os.getenv("CHROMEDRIVER_PATH") else Service()
    d = webdriver.Chrome(service=svc, options=o)
    try:
        w = WebDriverWait(d, 15)
        if a.login_url:
            u, c = os.getenv("E2E_USER"), os.getenv("E2E_PASSWORD")
            if not (u and c):
                sys.exit("Definir E2E_USER y E2E_PASSWORD para el login")
            d.get(a.login_url)
            w.until(EC.element_to_be_clickable((By.NAME, a.campo_usuario))).send_keys(u)
            d.find_element(By.NAME, a.campo_clave).send_keys(c)
            d.find_element(By.XPATH, f"//button[normalize-space()='{a.boton}']").click()
            w.until(EC.url_changes(a.login_url))
        d.get(a.url)
        w.until(lambda x: x.execute_script("return document.readyState") == "complete")
        datos = d.execute_script(JS)
        meta = datos.pop()
        for e in datos:
            e["sugerido"] = sugerir(e)
        if a.json:
            print(json.dumps({"url": d.current_url, "titulo": d.title, **meta, "elementos": datos}, ensure_ascii=False, indent=2))
            return
        print(f"# {d.title} — {d.current_url}")
        print(f"iframes: {meta['iframes']} · shadow hosts: {meta['shadowHosts']}  (requieren switchTo().frame / getShadowRoot)\n")
        print(f"{'vis':3} {'elemento':22} {'texto/label':32} localizador sugerido")
        for e in datos:
            desc = e["tag"] + (f"[{e['type']}]" if e["type"] else "") + (f"#{e['id']}" if e["id"] else "")
            info = e["label"] or e["text"] or e["aria"]
            print(f"{'✓' if e['visible'] else '·':3} {desc[:22]:22} {info[:32]:32} {e['sugerido']}")
        print("\n✓ visible · oculto (p. ej. secciones que aparecen tras una acción). Verifica cada localizador en DevTools antes de usarlo.")
    finally:
        d.quit()


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)  # salida limpia con | head
    main()
