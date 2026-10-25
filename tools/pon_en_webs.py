#!/usr/bin/env python3
"""Escribe en la web de cada desensamblado Konami la seccion del codigo que
comparte con los demas, sacada de datos/codigo_comun.json (codigo_comun.py).

Va al final de la pagina del codigo (THE-CODE.md y es/EL-CODIGO.md, o
UNDER-THE-HOOD.md y es/POR-DENTRO.md en las webs de tres bloques). Si la
seccion ya esta, se cambia entera: se puede volver a correr tras medir otra vez.
Los titulos y las webs salen de la lista de la portada (make_index.py).

Uso: pon_en_webs.py [clave ...]      sin claves, los 58
"""
import html
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
DES_ASM = os.path.dirname(os.path.dirname(RAIZ))
sys.path.insert(0, AQUI)
from codigo_comun import JUEGOS  # noqa: E402

PORTADA = os.path.join(DES_ASM, "web", "ANTXIKO_GITHUB_IO", "tools", "make_index.py")
BASE = "https://antxiko.github.io/MSX-disassembly-database/"
HERRAMIENTA = "https://github.com/antxiko/MSX-disassembly-database/blob/main/tools/codigo_comun.py"

TITULO = {"en": "## Code shared with other Konami cartridges",
          "es": "## Código compartido con otros cartuchos de Konami"}
PAGINAS = {"en": ("THE-CODE.md", "UNDER-THE-HOOD.md"),
           "es": ("es/EL-CODIGO.md", "es/POR-DENTRO.md")}

# filas: los que comparten al menos FILA_MIN bloques, hasta FILAS_MAX; y si
# no llegan a FILAS_MIN, los FILAS_MIN primeros aunque compartan menos
FILA_MIN, FILAS_MAX, FILAS_MIN = 5, 10, 3


def fichas():
    s = open(PORTADA, encoding="utf-8").read()
    blk = s[s.index("DESENSAMBLADOS = ["):s.index("GRUPOS = [")]
    res = {}
    for m in re.finditer(r'clave="([^"]+)",\s*grupo="konami",\s*titulo="([^"]+)".*?web="([^"]+)"', blk, re.S):
        res[m.group(1)] = (html.unescape(m.group(2)), m.group(3))
    return res


def mil(n, idioma):
    return "{:,}".format(n).replace(",", "," if idioma == "en" else ".")


def lado(nombre, sitio):
    return sitio if nombre.startswith("L_") else "`%s` (%s)" % (nombre, sitio)


def ejemplo(lista):
    def peso(x):
        a, _, b, _, n, _ = x
        return (not a.startswith("L_") and not b.startswith("L_"),
                not a.startswith("L_") or not b.startswith("L_"), n)
    a, da, b, db, n, _ = max(lista, key=peso)
    return "%s = %s" % (lado(a, da), lado(b, db))


def seccion(clave, d, fich, idioma):
    otros = len(JUEGOS) - 1
    vec = d["juegos"][clave]["comparte"]
    filas = [v for v in vec if v["rutinas"] >= FILA_MIN][:FILAS_MAX]
    if len(filas) < FILAS_MIN:
        filas = vec[:FILAS_MIN]
    ln = [TITULO[idioma], ""]
    if idioma == "en":
        ln += ["This disassembly has been compared, instruction by instruction, with",
               "every other Konami one in the series. A block counts when the same",
               "instructions, at least six of them from a label to its `ret` or its",
               "unconditional jump, are in both cartridges; the addresses are left",
               "aside, because they change from one cartridge to the next. Of the",
               "other %d, **%d** have at least one block in common with this one;" % (otros, len(vec)),
               "these are the ones that share the most:", "",
               "| Cartridge | Blocks | Instructions | For example (here = there) |",
               "|---|---:|---:|---|"]
        web = lambda w: w
    else:
        ln += ["Este desensamblado se ha comparado, instrucción por instrucción, con",
               "todos los demás de Konami de la serie. Cuenta un bloque cuando las",
               "mismas instrucciones, al menos seis desde una etiqueta hasta su `ret`",
               "o su salto sin condición, están en los dos cartuchos; las direcciones",
               "no se miran, porque cambian de un cartucho a otro. De los otros %d," % otros,
               "**%d** tienen al menos un bloque en común con este; estos son los" % len(vec),
               "que más comparten:", "",
               "| Cartucho | Bloques | Instrucciones | Por ejemplo (aquí = allí) |",
               "|---|---:|---:|---|"]
        web = lambda w: w + "es/"
    for v in filas:
        t, w = fich[v["con"]]
        ln.append("| [%s](%s) | %d | %s | %s |" % (t, web(w), v["rutinas"],
                                                 mil(v["instrucciones"], idioma), ejemplo(v["lista"])))
    ln.append("")
    if idioma == "en":
        ln += ["The whole matrix, the 58 cartridges against each other, is on",
               "[The routines](%sTHE-ROUTINES.html) in the series database, and it" % BASE,
               "is measured with [`codigo_comun.py`](%s)." % HERRAMIENTA]
    else:
        ln += ["La matriz entera, los 58 cartuchos entre sí, está en",
               "[Las rutinas](%ses/LAS-RUTINAS.html) de la base de datos de la" % BASE,
               "serie, y se mide con [`codigo_comun.py`](%s)." % HERRAMIENTA]
    return "\n".join(ln) + "\n"


def pon(ruta, texto, idioma):
    s = open(ruta, encoding="utf-8", newline="").read()
    nl = "\r\n" if "\r\n" in s else "\n"
    s = s.replace("\r\n", "\n")
    i = s.find("\n" + TITULO[idioma] + "\n")
    if i >= 0:
        j = s.find("\n## ", i + 1)
        s = s[:i + 1] + texto + (("\n" + s[j + 1:]) if j >= 0 else "")
    else:
        s = s.rstrip("\n") + "\n\n" + texto
    open(ruta, "w", encoding="utf-8", newline="").write(s.replace("\n", nl))


def main(argv):
    d = json.load(open(os.path.join(RAIZ, "datos", "codigo_comun.json"), encoding="utf-8"))
    fich = fichas()
    quiero = set(argv[1:])
    for clave, carpeta, _, _ in JUEGOS:
        if quiero and clave not in quiero:
            continue
        docs = os.path.join(DES_ASM, "desensamblados", carpeta + "_DISAM", "docs")
        for idioma in ("en", "es"):
            rutas = [os.path.join(docs, p) for p in PAGINAS[idioma] if os.path.exists(os.path.join(docs, p))]
            if len(rutas) != 1:
                sys.exit("%s: no se cual es la pagina del codigo (%s)" % (clave, idioma))
            pon(rutas[0], seccion(clave, d, fich, idioma), idioma)
        print(clave, "ok")


if __name__ == "__main__":
    main(sys.argv)
