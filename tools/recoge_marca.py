#!/usr/bin/env python3
"""Rastrea la marca oculta de Konami en los binarios de TODA la serie.

EL HALLAZGO NO ES NUESTRO: lo destapo **Manuel Pazos** (@ManuelPazosMSX) en
septiembre de 2021. Konami escondio en muchos de sus cartuchos de MSX el numero
de catalogo y el titulo en katakana, con el codigo de la casa y del reves:

    [titulo, N bytes, EN ORDEN INVERSO]  [N]  [las dos cifras del RC en BCD]  [0xAA]

Aqui se pasa por los cuarenta y siete binarios, no solo por los de Konami. Los
que no son de Konami sirven de control: si el rastreador les encontrara una
marca, es que se traga coincidencias.

El rastreador es `marca_konami_canonica.py`, copia de la version mas completa
que hay en la serie (la de Twin Bee). Hay tres variantes repartidas por los
repositorios y esa es superconjunto de las otras dos: acepta el digito ASCII con
el que Konami escribio el numero de Hyper Sports 3, y diez codigos de kana
despejados con titulos ya conocidos. Sus umbrales salen de marcas reales y de
los falsos positivos que aparecieron al aflojarlos -el "RC-791" de dos bytes que
salia en Athletic Land y Cabbage Patch, que ni existe ni es el suyo-.

Uso: recoge_marca.py <raiz de DES_ASM> > datos/marcas.json
"""
import json
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")
RASTREADOR = os.path.join(AQUI, "marca_konami_canonica.py")

# "  twinbee.rom      RC-740  6 bytes  cierra en 0xBFFF"
RE_MARCA = re.compile(r"RC-(\d+)\s+(\d+) bytes\s+cierra en 0x([0-9A-Fa-f]+)")


def main():
    raiz = sys.argv[1]
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    with open(os.path.join(DATOS, "serie.json"), encoding="utf-8") as f:
        base = json.load(f)["proyectos"]

    filas = []
    for p in base:
        ficheros = []
        if p.get("binario"):
            ficheros = [p["binario"]["fichero"]]
        elif p.get("binarios"):
            ficheros = [b["fichero"] for b in p["binarios"]]
        for rel in ficheros:
            ruta = os.path.join(raiz, rel)
            r = subprocess.run([sys.executable, RASTREADOR, ruta],
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
            salida = (r.stdout or "") + (r.stderr or "")
            m = RE_MARCA.search(salida)
            fila = {"clave": p["clave"], "titulo": p["titulo"],
                    "grupo": p.get("grupo"), "fichero": rel,
                    "lleva_marca": bool(m)}
            if m:
                # La linea siguiente a la de la marca es el titulo decodificado.
                lineas = [l.rstrip() for l in salida.splitlines() if l.strip()]
                i = next(i for i, l in enumerate(lineas) if RE_MARCA.search(l))
                fila.update(rc="RC-%s" % m.group(1), bytes_titulo=int(m.group(2)),
                            cierra_en="0x" + m.group(3).upper(),
                            titulo_en_kana=(lineas[i + 1].strip()
                                            if i + 1 < len(lineas) else None))
            filas.append(fila)

    con = [f for f in filas if f["lleva_marca"]]
    print("binarios mirados: %d | con marca: %d" % (len(filas), len(con)),
          file=sys.stderr)
    json.dump({"credito": "El hallazgo de la marca es de Manuel Pazos "
                          "(@ManuelPazosMSX), septiembre de 2021.",
               "binarios": filas}, sys.stdout, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
