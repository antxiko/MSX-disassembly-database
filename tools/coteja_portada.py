#!/usr/bin/env python3
"""Cotejo: lo que la portada PUBLICA de cada juego contra lo que se MIDE hoy.

Para que sirve. Las cifras de la portada estan escritas a mano en la ficha de
cada juego, el dia que se publico. Si despues alguien vuelve al listado y comenta
otra tanda, la web se queda diciendo la cifra vieja. Pasa de verdad: Trailblazer
publica 30,7 % y su listado, tocado en un commit POSTERIOR al README, va por
30,8 %.

Tres numeros de la ficha se pueden cotejar, y cada uno tiene su trampa:

    bytes     contra el tamano del fichero que el Makefile desensambla. SOLO EN
              LOS CARTUCHOS: en las cintas ese fichero es un .tsx o un .cas con
              cabeceras y tonos piloto, y la ficha da los bytes del programa.
    densidad  el "comentado al N %". Este es el cotejo duro: si no cuadra, la
              web publica una cifra que su propio listado ya no da.
    etiquetas AQUI NO HAY COTEJO POSIBLE, y es un hallazgo de esta base. La
              portada usa esa palabra para tres magnitudes distintas segun el
              juego: las rutinas que cuenta densidad.py (Twin Bee, 1.000), las
              "etiquetas con nombre" del README (Hyper Sports 2, 314, que tiene
              500 rutinas), o las etiquetas del listado (War in Middle Earth,
              819). Y en siete juegos no es ninguna de las tres. Por eso las
              etiquetas se INFORMAN, con la magnitud que las explica cuando hay
              alguna, pero no tumban el cotejo.

Lo que la ficha dice y aqui no se mide (bytes de codigo y de datos, "0 sin
explicar", "reensambla byte a byte") no se toca: eso lo comprueba cada repo.

Uso: coteja_portada.py <raiz de DES_ASM>   (exit 1 si una cifra dura no cuadra)
"""
import json
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")

RE_BYTES = re.compile(r"^([\d.,]+) bytes")
RE_DENS = re.compile(r"comentado al ([\d,]+) %")
RE_BLOQUES = re.compile(r"([\d.,]+) (?:etiquetas|rutinas)")
CINTA = re.compile(r"\.(tsx|cas)$", re.I)
RE_ETIQUETA = re.compile(r"^([A-Za-z_][A-Za-z_0-9]*):")


def numero(s):
    """'32.768' -> 32768; '41,4' -> 41.4. La portada escribe en castellano."""
    s = s.replace(".", "")
    return float(s.replace(",", ".")) if "," in s else int(s)


def texto_ficha(p):
    """El texto en castellano de la ficha, sin marcado ni entidades."""
    d = p.get("datos", {}).get("es")
    if d is None:
        return None
    t = d("es") if callable(d) else d
    return re.sub(r"<[^>]+>", "", t).replace("&middot;", "·")


def etiquetas_del_listado(raiz, directorio, listados):
    """Cuantas etiquetas tiene el listado publicado, contadas a mano."""
    n = 0
    for a in listados:
        ruta = os.path.join(raiz, directorio, a)
        if not os.path.isfile(ruta):
            return None
        with open(ruta, encoding="utf-8", errors="replace") as f:
            n += sum(1 for ln in f if RE_ETIQUETA.match(ln))
    return n


def main():
    raiz = sys.argv[1]
    sys.path.insert(0, os.path.join(raiz, "ANTXIKO_GITHUB_IO", "tools"))
    import make_index

    with open(os.path.join(DATOS, "serie.json"), encoding="utf-8") as f:
        base = {x["clave"]: x for x in json.load(f)["proyectos"]}
    with open(os.path.join(DATOS, "readmes.json"), encoding="utf-8") as f:
        readmes = {x["repo"]: x for x in json.load(f)}

    fallos, avisos, revisados = [], [], 0
    for p in make_index.DESENSAMBLADOS:
        clave = p["clave"]
        reg = base.get(clave)
        if not reg:
            fallos.append("%s: esta en la portada y no en la base" % clave)
            continue
        t = texto_ficha(p)
        if not t:
            continue
        revisados += 1
        c, b = reg.get("cifras"), reg.get("binario")

        m = RE_BYTES.search(t)
        if m and b and not CINTA.search(b["fichero"]):
            if numero(m.group(1)) != b["bytes"]:
                fallos.append("%s: la ficha dice %s bytes y el binario tiene %d"
                              % (clave, m.group(1), b["bytes"]))

        m = RE_DENS.search(t)
        if m and c and abs(numero(m.group(1)) - c["densidad"]) > 0.05:
            fallos.append("%s: la ficha publica %s %% y su listado da hoy %.1f %%"
                          % (clave, m.group(1), c["densidad"]))

        m = RE_BLOQUES.search(t)
        if m and c:
            dice = numero(m.group(1))
            if dice == c["bloques"]:
                continue                          # las rutinas de densidad.py
            rm = readmes.get(reg["directorio"]) or {}
            etiq_readme = rm.get("etiquetas_con_nombre")
            etiq_listado = etiquetas_del_listado(raiz, reg["directorio"],
                                                 reg["listados"])
            if etiq_readme is not None and dice == etiq_readme:
                que = "son las %d 'etiquetas con nombre' de su README" % etiq_readme
            elif etiq_listado is not None and dice == etiq_listado:
                que = "son las %d etiquetas del listado" % etiq_listado
            else:
                que = ("no son sus %d rutinas, ni sus %s etiquetas con nombre, "
                       "ni las %s del listado: hoy no se sabe de donde sale"
                       % (c["bloques"], etiq_readme, etiq_listado))
            avisos.append("%s: publica %s y %s" % (clave, m.group(1), que))

    print("fichas cotejadas: %d" % revisados)
    if avisos:
        print("\n'etiquetas' no significa lo mismo en todas las fichas (%d):"
              % len(avisos))
        for a in avisos:
            print("  " + a)
    if fallos:
        print("\nNO CUADRA (%d):" % len(fallos))
        for f in fallos:
            print("  " + f)
        return 1
    print("\nlas cifras duras cuadran: bytes y densidad publicados = medidos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
