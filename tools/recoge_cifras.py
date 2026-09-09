#!/usr/bin/env python3
"""Recoge las cifras de comentado de cada desensamblado de la serie.

DE DONDE SALE CADA NUMERO, Y POR QUE DOS VECES. La serie lleva 47 repositorios
escritos a lo largo de meses, y cada uno se mide con SU copia de densidad.py.
Comparar entre juegos exige saber que la vara es la misma, asi que aqui cada
repositorio se mide DOS veces:

  medido    con la copia canonica de esta base de datos (tools/densidad_canonica.py)
            sobre los listados que el repo PUBLICA (git ls-files, no lo que
            haya suelto en el directorio), y
  declarado con el propio `make densidad` del repositorio, si tiene ese target.

Si las dos coinciden en todos los repositorios que traen la herramienta, queda
demostrado que la vara es la misma y la cifra de los que no la traen tambien
vale. Donde no coincidan, la discrepancia se registra: no se elige una.

Las cuatro variantes de densidad.py de la serie se cotejaron el 2026-09-09 y
cuentan IGUAL; se diferencian en el fin de linea, en un caso especial de Nemesis
(un banco sin codigo) y en que la de Trailblazer suma varias piezas de cinta.

Uso: recoge_cifras.py <raiz de DES_ASM> > datos/cifras.json
"""
import json
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CANONICA = os.path.join(AQUI, "densidad_canonica.py")

# El make de esta maquina no esta en el PATH por defecto.
MAKE = "C:/msys64/usr/bin/make.exe"

# Lo que imprime densidad.py al final. Hay DOS formatos en la serie: el de dos
# lineas sueltas, y el de tabla con fila TOTAL de los listados por piezas
# (Demonia, el Descubrimiento). Y un mismo `make densidad` puede imprimir el
# primero VARIAS veces, una por banco: Nemesis lo hace dieciseis veces. Por eso
# se suman todas las apariciones en vez de quedarse con la primera.
RE_FLOJAS = re.compile(r"----\s+(\d+) rutinas por debajo del 10 %, de (\d+)")
RE_TOTAL = re.compile(r"----\s+en total: (\d+) instrucciones, (\d+) comentarios")
RE_TABLA = re.compile(r"^\s*TOTAL\s+(\d+)\s+(\d+)\s+[\d.]+%\s+(\d+)\s+(\d+)\s*$",
                      re.M)


def suma_salida(salida):
    """Lee una salida de densidad.py, en cualquiera de los dos formatos."""
    m = RE_TABLA.search(salida)
    if m:
        return {"instrucciones": int(m.group(1)), "comentarios": int(m.group(2)),
                "bloques": int(m.group(3)), "flojas": int(m.group(4))}
    tot = RE_TOTAL.findall(salida)
    if not tot:
        return None
    fl = RE_FLOJAS.findall(salida)
    return {"instrucciones": sum(int(a) for a, _ in tot),
            "comentarios": sum(int(b) for _, b in tot),
            "flojas": sum(int(a) for a, _ in fl),
            "bloques": sum(int(b) for _, b in fl)}


def corre(orden, cwd, timeout=300):
    """Lanza una orden y devuelve (salida, codigo). No lanza excepcion."""
    try:
        p = subprocess.run(orden, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout, encoding="utf-8", errors="replace")
        return (p.stdout or "") + (p.stderr or ""), p.returncode
    except (OSError, subprocess.SubprocessError) as e:
        return "no se pudo ejecutar: %s" % e, None


def listados(raiz, repo):
    """Los .asm que el repositorio PUBLICA, segun git."""
    salida, cod = corre(["git", "ls-files", "*.asm"], os.path.join(raiz, repo))
    if cod != 0:
        return []
    return sorted(l.strip() for l in salida.splitlines() if l.strip())


def mide(raiz, repo, asms):
    """Mide los listados con la copia canonica y suma las piezas."""
    n = c = flojas = bloques = 0
    detalle, fallos = [], []
    for asm in asms:
        salida, cod = corre([sys.executable, CANONICA, asm],
                            os.path.join(raiz, repo))
        r = suma_salida(salida)
        if cod != 0 or not r:
            fallos.append({"asm": asm, "salida": salida.strip()[:400]})
            continue
        n += r["instrucciones"]
        c += r["comentarios"]
        flojas += r["flojas"]
        bloques += r["bloques"]
        detalle.append(dict(r, asm=asm))
    if not n:
        return None, detalle, fallos
    return {"instrucciones": n, "comentarios": c,
            "densidad": round(100.0 * c / n, 1),
            "flojas": flojas, "bloques": bloques}, detalle, fallos


def declarado(raiz, repo):
    """La cifra del propio repositorio, si tiene target `densidad`."""
    mk = os.path.join(raiz, repo, "Makefile")
    if not os.path.isfile(mk):
        return None
    txt = open(mk, encoding="utf-8", errors="replace").read()
    if not re.search(r"^densidad:", txt, re.M):
        return None
    salida, cod = corre([MAKE, "densidad"], os.path.join(raiz, repo))
    r = suma_salida(salida)
    if cod != 0 or not r:
        return {"error": salida.strip()[:400]}
    r["densidad"] = round(100.0 * r["comentarios"] / r["instrucciones"], 1)
    return r


def main():
    raiz = sys.argv[1]
    # La consola de Windows no es UTF-8: sin esto, un punto medio
    # del titulo de un juego sale roto en el JSON.
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    filas = []
    for repo in sorted(os.listdir(raiz)):
        if not os.path.isdir(os.path.join(raiz, repo, ".git")):
            continue
        asms = listados(raiz, repo)
        if not asms:
            filas.append({"repo": repo, "listados": [], "medido": None,
                          "declarado": None, "nota": "no publica ningun .asm"})
            continue
        medido, detalle, fallos = mide(raiz, repo, asms)
        fila = {"repo": repo, "listados": asms, "medido": medido,
                "por_listado": detalle, "declarado": declarado(raiz, repo)}
        if fallos:
            fila["fallos"] = fallos
        # El cotejo, calculado aqui para que no haya que rehacerlo al leer.
        d = fila["declarado"]
        if medido and d and "error" not in d:
            fila["coteja"] = (d["instrucciones"] == medido["instrucciones"]
                              and d["comentarios"] == medido["comentarios"])
        else:
            fila["coteja"] = None
        filas.append(fila)
        print("%-28s %s" % (repo, medido or "sin medir"), file=sys.stderr)
    json.dump(filas, sys.stdout, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
