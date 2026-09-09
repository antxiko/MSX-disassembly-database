#!/usr/bin/env python3
"""Localiza el binario que cada repositorio de la serie desensambla de verdad.

No se adivina por el nombre: se lee la variable del Makefile (ROM, TSX, CAS...)
que el propio repo usa, se resuelve el fichero y se le saca el sha256. Un repo
cuyo binario no aparezca se marca, no se inventa.

Uso: recoge_binarios.py <raiz de DES_ASM> > datos/binarios.json
"""
import hashlib
import json
import os
import re
import sys

# Las variables con las que los Makefiles de la serie nombran su binario.
VARS = ("ROM", "TSX", "CAS", "BIN", "TAPE", "CART")


def lee_vars(makefile):
    """Devuelve {VAR: valor} de las asignaciones simples del Makefile."""
    out = {}
    try:
        txt = open(makefile, encoding="utf-8", errors="replace").read()
    except OSError:
        return out
    for m in re.finditer(r"^([A-Z][A-Z_0-9]*)\s*[:?]?=\s*(.+?)\s*$", txt, re.M):
        out[m.group(1)] = m.group(2)
    return out


def resuelve(raiz, repo, valor, variables):
    """Expande $(VAR) y busca el fichero en el repo."""
    for _ in range(5):
        nuevo = re.sub(r"\$[({]([A-Z_0-9]+)[)}]",
                       lambda m: variables.get(m.group(1), ""), valor)
        if nuevo == valor:
            break
        valor = nuevo
    valor = valor.strip()
    if not valor:
        return None
    cand = os.path.join(raiz, repo, valor)
    if os.path.isfile(cand):
        return os.path.relpath(cand, raiz).replace("\\", "/")
    # El Makefile puede nombrarlo sin carpeta; buscarlo por nombre de fichero.
    base = os.path.basename(valor)
    for sub in ("", "dump", "rom", "roms", "bin", "build"):
        cand = os.path.join(raiz, repo, sub, base)
        if os.path.isfile(cand):
            return os.path.relpath(cand, raiz).replace("\\", "/")
    return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for trozo in iter(lambda: f.read(65536), b""):
            h.update(trozo)
    return h.hexdigest()


def main():
    raiz = sys.argv[1]
    filas = []
    for repo in sorted(os.listdir(raiz)):
        if not os.path.isdir(os.path.join(raiz, repo, ".git")):
            continue
        mk = os.path.join(raiz, repo, "Makefile")
        variables = lee_vars(mk)
        hallados = []
        for v in VARS:
            if v not in variables:
                continue
            rel = resuelve(raiz, repo, variables[v], variables)
            if rel:
                p = os.path.join(raiz, rel)
                hallados.append({"var": v, "valor": variables[v],
                                 "fichero": rel, "bytes": os.path.getsize(p),
                                 "sha256": sha256(p)})
        filas.append({"repo": repo,
                      "makefile": os.path.isfile(mk),
                      "binarios": hallados,
                      "declaradas": [v for v in VARS if v in variables]})
    json.dump(filas, sys.stdout, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
