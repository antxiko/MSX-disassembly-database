#!/usr/bin/env python3
"""Busca en cada binario los textos que dicen quien hizo el juego.

Como. Se sacan todas las tiras de caracteres imprimibles del fichero y se
quedan las que llevan una palabra de credito -PROGRAM, SOUND, DESIGN, (C),
COPYRIGHT...-. De cada una se guarda la cita LITERAL y su posicion.

DOS AVISOS QUE HAY QUE LEER ANTES DE USAR ESTO:

1. LA POSICION ES UN DESPLAZAMIENTO EN EL FICHERO, no una direccion de memoria.
   Un cartucho de la pagina 1 se ve en 0x4000 y uno de la pagina 2 en 0x8000, y
   una cinta no se ve en ningun sitio hasta que carga. Sumar el origen exige
   saber el de cada juego, y eso lo sabe su repositorio, no esta herramienta.

2. QUE NO SALGA NADA NO SIGNIFICA QUE NO HAYA CREDITOS. La mayoria de estos
   juegos no escriben con la fuente del BIOS sino con sus propios dibujos, y
   entonces el texto de la pantalla de creditos NO esta en ASCII en ninguna
   parte: son numeros de tile. Antarctic Adventure es el caso conocido -se
   buscaron sus iniciales en las cuatro ROM y no estan en ASCII-. Por eso el
   resultado de un juego sin coincidencias es "no aparece en ASCII", que es un
   dato, y no "no tiene creditos", que seria inventar.

3. NO TODO LO QUE PONE "TOPO SOFT" LO ESCRIBIO TOPO SOFT. Los ficheros de cinta
   llevan al principio el nombre del volcado, con la convencion de los archivos
   de preservacion: "Colt 36 (1987)(Topo Soft)(ES)[!][RUN'CAS-'][v0.6b]". Eso lo
   escribio quien preservo la cinta en los anos 2000, no el juego en 1987, y
   citarlo como credito seria falso. Se reconocen por esa forma -ano entre
   parentesis y corchetes de etiqueta- y salen marcados como metadato del
   volcado, aparte de los creditos de verdad.

Uso: recoge_creditos.py <raiz de DES_ASM> > datos/creditos.json
"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")

MINIMO = 5                                   # tiras mas cortas son ruido
RE_TIRA = re.compile(rb"[\x20-\x7e]{%d,}" % MINIMO)

# Las palabras por las que se reconoce un credito. En mayusculas: casi todos
# estos juegos escriben en mayusculas.
CLAVES = [
    "PROGRAM", "PROGRAMM", "PROGRAMA", "SOUND", "MUSIC", "DESIGN", "GRAPHIC",
    "COPYRIGHT", "(C)", "PRESENTED", "PRODUCED", "DIRECT", "STAFF", "CREATED",
    "DEVELOP", "SOFTWARE", "KONAMI", "HUDSON", "ACTIVISION", "CASIO", "GREMLIN",
    "MELBOURNE", "TOPO", "T&E", "HAL ", "ASCII", "MICROIDS", "AUTHOR",
    "WRITTEN", "CONVER", "VERSION", "REALIZ", "IDEA",
]
# Ruido conocido: la cabecera de un cartucho MSX y las llamadas del BIOS.
RUIDO = re.compile(r"^(AB|[\x00-\x1f]*)$")
# El nombre del volcado, no del juego: "Titulo (1987)(Editor)(ES)[!][RUN'CAS-']".
VOLCADO = re.compile(r"\(\d{4}\)\(.+?\)|\[!\]|RUN'CAS|BLOAD'CAS|\[GoodMSX\]"
                     r"|\[RC-\d+\]|\bv\d+\.\d+b\b")


def tiras(datos):
    for m in RE_TIRA.finditer(datos):
        yield m.start(), m.group().decode("ascii")


def main():
    raiz = sys.argv[1]
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    with open(os.path.join(DATOS, "serie.json"), encoding="utf-8") as f:
        base = json.load(f)["proyectos"]

    filas = []
    for p in base:
        ficheros = ([p["binario"]["fichero"]] if p.get("binario")
                    else [b["fichero"] for b in p.get("binarios", [])])
        for rel in ficheros:
            with open(os.path.join(raiz, rel), "rb") as f:
                datos = f.read()
            hallados, delvolcado, total = [], [], 0
            for off, t in tiras(datos):
                total += 1
                limpio = t.strip()
                casan = [c for c in CLAVES if c in limpio.upper()]
                if not casan or RUIDO.match(limpio):
                    continue
                # El desplazamiento tiene que apuntar a la cita que se guarda,
                # no al principio de la tira: si se recortan los espacios de
                # delante, hay que correrlo lo mismo. Casio World Open empieza
                # con cuatro.
                fila = {"offset": "0x%04X" % (off + (len(t) - len(t.lstrip()))),
                        "texto": limpio, "por": casan}
                (delvolcado if VOLCADO.search(limpio) else hallados).append(fila)
            filas.append({"clave": p["clave"], "titulo": p["titulo"],
                          "fichero": rel, "tiras_legibles": total,
                          "creditos": hallados,
                          "metadatos_del_volcado": delvolcado,
                          "nota": None if hallados else
                                  "no aparece ningun credito en ASCII"})

    con = sum(1 for f in filas if f["creditos"])
    print("binarios: %d | con texto de credito en ASCII: %d" % (len(filas), con),
          file=sys.stderr)
    json.dump(filas, sys.stdout, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
