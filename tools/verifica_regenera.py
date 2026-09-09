#!/usr/bin/env python3
"""El registro publicado tiene que salir otra vez de sus propias recogidas.

Un fichero de datos editado a mano es un fichero de datos en el que ya no se
puede confiar. Aqui se vuelve a montar `datos/serie.json` a partir de las cuatro
recogidas y se compara con el que hay guardado: si alguien tocara el registro
sin pasar por la herramienta, esto lo canta.

Lo que NO comprueba: que las recogidas esten al dia. Eso cuesta minutos -hay que
correr el `make densidad` de cuarenta y siete repositorios- y se hace a mano con
`recoge_cifras.py`.

Uso: verifica_regenera.py     (exit 1 si el registro no se reproduce)
"""
import json
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)


def main():
    guardado = os.path.join(RAIZ, "datos", "serie.json")
    with open(guardado, encoding="utf-8") as f:
        antes = json.load(f)

    p = subprocess.run([sys.executable, os.path.join(AQUI, "monta_base.py")],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", cwd=RAIZ)
    if p.returncode != 0:
        print("monta_base.py ha fallado:\n" + (p.stderr or ""))
        return 1
    ahora = json.loads(p.stdout)

    # La fecha cambia cada dia; lo que no puede cambiar es el contenido.
    antes.pop("generado", None)
    ahora.pop("generado", None)
    if antes != ahora:
        a = {x["clave"]: x for x in antes["proyectos"]}
        b = {x["clave"]: x for x in ahora["proyectos"]}
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                print("  no se reproduce: %s" % k)
        print("el registro guardado NO sale de sus recogidas")
        return 1
    print("el registro se reproduce desde sus recogidas: %d proyectos"
          % len(ahora["proyectos"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
