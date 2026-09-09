#!/usr/bin/env python3
"""Los trozos de codigo que mas cartuchos comparten, y como llamo cada uno al suyo.

`recoge_comun.py` dice que dos binarios comparten N bytes en tales posiciones.
Esto da el paso siguiente y el interesante: coge los trozos de CODIGO que
reaparecen en mas cartuchos, los busca en los cuarenta y nueve binarios, y para
cada uno saca la etiqueta con la que su desensamblado lo bautizo.

Lo que se ve entonces es que la serie lleva meses poniendole nombres distintos a
la misma rutina. La lectura de mandos son treinta y seis bytes identicos en
dieciseis cartuchos, y en el listado de cada uno se llama de una manera.

Como se localiza el nombre: la direccion es el ORG del Makefile mas el
desplazamiento, y en el listado se busca la ultima etiqueta antes de esa
direccion. Un binario donde el trozo aparezca pero cuyo listado no lo tenga como
instruccion sale como "no es codigo ahi", que tambien es un dato: el mismo byte
puede ser rutina en un cartucho y dibujo en otro.

Uso: nombra_comunes.py <raiz de DES_ASM> [cuantos] > datos/rutinas_comunes.json
"""
import json
import os
import re
import sys
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")
CUANTOS = 10


def etiqueta_en(raiz, directorio, listados, direccion):
    """La ultima etiqueta antes de `direccion`, si ahi hay una instruccion."""
    for a in listados:
        ruta = os.path.join(raiz, directorio, a)
        if not os.path.isfile(ruta):
            continue
        et = None
        with open(ruta, encoding="utf-8", errors="replace") as f:
            for ln in f:
                m = re.match(r"^([A-Za-z_][A-Za-z_0-9]*):", ln)
                if m:
                    et = m.group(1)
                    continue
                m = re.match(r"^\t.*;([0-9a-f]{4})", ln)
                if m and int(m.group(1), 16) == direccion:
                    return et
    return None


def org_de(raiz, directorio):
    mk = os.path.join(raiz, directorio, "Makefile")
    if not os.path.isfile(mk):
        return None
    m = re.search(r"^ORG\s*[:?]?=\s*(0x[0-9A-Fa-f]+)\s*$",
                  open(mk, encoding="utf-8", errors="replace").read(), re.M)
    return int(m.group(1), 16) if m else None


def main():
    raiz = sys.argv[1]
    cuantos = int(sys.argv[2]) if len(sys.argv) > 2 else CUANTOS
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")

    with open(os.path.join(DATOS, "serie.json"), encoding="utf-8") as f:
        base = {x["clave"]: x for x in json.load(f)["proyectos"]}
    with open(os.path.join(DATOS, "comun.json"), encoding="utf-8") as f:
        parejas = [x for x in json.load(f)["parejas"] if not x["mismo_binario"]]

    # los trozos de codigo, por en cuantos cartuchos aparecen
    donde = defaultdict(set)
    for x in parejas:
        for t in x["detalle"]:
            if t["es_en_a"] == "codigo":
                donde[(x["a"], t["en_a"], t["bytes"])].add(x["b"])
            if t["es_en_b"] == "codigo":
                donde[(x["b"], t["en_b"], t["bytes"])].add(x["a"])

    # un mismo trozo sale nombrado desde varios juegos: quedarse con el mejor
    vistos, elegidos = set(), []
    for (clave, off, ln), otros in sorted(donde.items(),
                                          key=lambda y: (-len(y[1]), -y[0][2])):
        p = base[clave]
        with open(os.path.join(raiz, p["binario"]["fichero"]), "rb") as f:
            f.seek(int(off, 16))
            crudo = f.read(ln)
        if crudo in vistos:
            continue
        vistos.add(crudo)
        elegidos.append((clave, off, ln, crudo, otros))
        if len(elegidos) >= cuantos:
            break

    salida = []
    for clave, off, ln, crudo, otros in elegidos:
        apariciones = []
        for k, p in base.items():
            bi = p.get("binario")
            if not bi:
                continue
            with open(os.path.join(raiz, bi["fichero"]), "rb") as f:
                datos = f.read()
            pos = datos.find(crudo)
            if pos < 0:
                continue
            org = org_de(raiz, p["directorio"])
            et = (etiqueta_en(raiz, p["directorio"], p["listados"], org + pos)
                  if org is not None else None)
            apariciones.append({"juego": k, "titulo": p["titulo"],
                                "offset": "0x%04X" % pos,
                                "direccion": "0x%04X" % (org + pos) if org else None,
                                "se_llama": et,
                                "es_codigo_ahi": et is not None})
        nombres = sorted({a["se_llama"] for a in apariciones if a["se_llama"]})
        salida.append({"bytes": ln, "hallado_en": clave, "offset": off,
                       "cartuchos": len(apariciones),
                       "como_lo_llaman": nombres,
                       "primeros_bytes": " ".join("%02X" % c for c in crudo[:16]),
                       "apariciones": apariciones})
        print("  %4d bytes en %2d cartuchos, %d nombres distintos"
              % (ln, len(apariciones), len(nombres)), file=sys.stderr)

    json.dump({"trozos": salida}, sys.stdout, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
