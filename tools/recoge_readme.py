#!/usr/bin/env python3
"""Extrae las cifras que declara el README en castellano de cada repositorio.

Es la tercera pata del cotejo. La portada toma sus numeros del README, el README
los tomo de la herramienta el dia que se escribio, y la herramienta se puede
volver a pasar hoy. Con las tres se ve si algo se quedo atras.

Los README de la serie no tienen un formato unico -los primeros llevan tabla de
markdown y los ultimos un bloque tabulado-, asi que cada cifra se busca por su
frase, no por su posicion. Lo que no aparezca se deja a nulo: aqui no se deduce
nada.

CUIDADO CON "ETIQUETAS". Los README distinguen dos cosas que no son la misma:

    rutinas / bloques      los que cuenta densidad.py (el denominador de las
                           rutinas flojas)
    etiquetas con nombre   las etiquetas del listado, que son mas o menos

En Hyper Sports 2 son 500 y 314. La portada publica unas veces una y otras la
otra, siempre bajo la palabra "etiquetas": por eso se recogen las dos.

Uso: recoge_readme.py <raiz de DES_ASM> > datos/readmes.json
"""
import json
import os
import re
import sys

# Cada cifra, por su frase, y SIEMPRE dentro de UNA linea: buscar en el texto
# entero hacia que Demonia -que no publica densidad- se llevara el "100%" de
# una frase suya sobre el debugger, doce lineas mas abajo.
NUM = r"([\d.,]+)"
# Las cuatro maneras de decir el 10 % en los README de la serie.
FLOJAS = r"(?:bloques|rutinas)\s+(?:por debajo del|bajo el|bajo)\s*10\s*%"
PATRONES = {
    # "densidad de comentario 3.062 de 7.405    41,4 %"   (los ultimos)
    # "densidad           3.236 de 8.774     36,9 %"      (Goonies, Boxing)
    # "45,5 %  del listado comentado"                     (King's Valley)
    # "| comentado | 828 comentarios de linea, 22,5 % |"  (los primeros)
    # "| Del listado comentado | **64,3 %** - 2.503 comentarios sobre ..."
    "densidad": [r"densidad(?: de comentario)?\s+[\d.,]+\s+de\s+[\d.,]+\s+" + NUM + r"\s*%",
                 NUM + r"\s*%\s+del listado comentado",
                 # "| densidad de comentarios | **50,2 %** |"
                 r"densidad de comentarios?\s*\|\s*\*{0,2}" + NUM + r"\s*%",
                 r"comentado\s*\|[^|]*?" + NUM + r"\s*%",
                 r"listado comentado\s*\|\s*\*\*" + NUM + r"\s*%"],
    "comentarios": [r"densidad(?: de comentario)?\s+" + NUM + r"\s+de\s+[\d.,]+",
                    r"comentado\s*\|\s*" + NUM + r"\s+comentarios de l[ií]nea",
                    r"\*\*[\d,]+\s*%\*\*\s*[-—]\s*" + NUM + r"\s+comentarios"],
    "instrucciones": [r"densidad(?: de comentario)?\s+[\d.,]+\s+de\s+" + NUM,
                      r"comentarios sobre\s+" + NUM + r"\s+instrucciones"],
    # "bloques por debajo del 10 %   0 de 1.000" / "rutinas bajo 10 %  0 de 475"
    "rutinas": [FLOJAS + r"\s*\|?\s*[\d.,]+\s+de\s+" + NUM,
                r"rutinas flojas[^|]*\|\s*[\d.,]+\s+de\s+" + NUM,
                # "| rutinas por debajo del 10 % comentado | **0 de 1.001** |"
                r"rutinas por debajo del 10 %[^|]*\|\s*\*{0,2}[\d.,]+\s+de\s+" + NUM,
                # "| rutinas | 200, **ninguna por debajo del 10 % comentada** |"
                r"\|\s*rutinas\s*\|\s*" + NUM + r"\s*,",
                NUM + r"\s+rutinas con nombre"],
    "flojas": [FLOJAS + r"\s*\|?\s*" + NUM + r"\s+de",
               r"rutinas flojas[^|]*\|\s*" + NUM + r"\s+de",
               r"rutinas por debajo del 10 %[^|]*\|\s*\*{0,2}" + NUM + r"\s+de"],
    "etiquetas_con_nombre": [r"etiquetas con nombre\s*\|\s*" + NUM],
    "tests": [r"^\s*tests\s+" + NUM, r"\|\s*tests[^|]*\|\s*" + NUM],
}


def numero(s):
    s = s.replace(".", "")
    return float(s.replace(",", ".")) if "," in s else int(s)


def busca(txt, patrones):
    """La primera linea que case, en el orden de los patrones. Nunca a caballo
    de dos lineas: eso es lo que producia cifras de otra cosa."""
    lineas = txt.splitlines()
    for p in patrones:
        rx = re.compile(p, re.I)
        for ln in lineas:
            m = rx.search(ln)
            if not m:
                continue
            try:
                return numero(m.group(1))
            except ValueError:
                continue
    return None


def main():
    raiz = sys.argv[1]
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    filas = []
    for repo in sorted(os.listdir(raiz)):
        if not os.path.isdir(os.path.join(raiz, repo, ".git")):
            continue
        ruta = None
        for nombre in ("README.es.md", "README.md"):
            cand = os.path.join(raiz, repo, nombre)
            if os.path.isfile(cand):
                ruta = cand
                break
        if not ruta:
            filas.append({"repo": repo, "readme": None})
            continue
        txt = open(ruta, encoding="utf-8", errors="replace").read()
        fila = {"repo": repo, "readme": os.path.basename(ruta)}
        for clave, pats in PATRONES.items():
            fila[clave] = busca(txt, pats)
        filas.append(fila)
    json.dump(filas, sys.stdout, indent=1, ensure_ascii=False)
    hay = sum(1 for f in filas if f.get("densidad") is not None)
    print("README leidos: %d | con densidad: %d" % (len(filas), hay),
          file=sys.stderr)


if __name__ == "__main__":
    main()
