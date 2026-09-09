#!/usr/bin/env python3
"""Que codigo comparten entre si los binarios de la serie.

Konami reutilizaba codigo entre sus cartuchos. Eso, si es cierto, tiene que
verse en el binario: las mismas rutinas dan los mismos bytes. Esto lo mide en
los cuarenta y nueve binarios, todos contra todos, en vez de suponerlo.

El metodo es el de `comun_konami.py`, que ya esta en la serie: se indexan los
trozos de doce bytes del primero y se recorre el segundo; cada coincidencia se
estira a los dos lados hasta donde llega. Salen tiras MAXIMALES y sin solapes.
El indice de cada binario se calcula UNA vez y se reusa contra los otros
cuarenta y ocho: sin eso, los 1.176 pares no salen a cuenta.

LO QUE ESTO VE Y LO QUE NO. Ve bytes identicos, asi que solo encuentra una
rutina compartida si ademas la ensamblaron en la MISMA direccion: en cuanto
cambia el mapa de memoria, la misma rutina da bytes distintos porque sus
direcciones lo son. Lo que se deja fuera lo caza `comun_normalizado.py` -pone a
cero los operandos de dieciseis bits y compara instrucciones-, pero eso exige
trazar cada ROM desde su INIT y saber su origen, y no esta hecho aqui.

Y hay que descartar lo que coincide por casualidad o por vacio:
  - la tira ha de tener al menos MINIMO bytes,
  - y al menos cuatro valores distintos, o el relleno 0x00 y las tablas de
    ceros lo llenarian todo.

CODIGO O DIBUJOS: LA PREGUNTA QUE HAY QUE HACERSE SIEMPRE. Lo primero que sale
al ordenar por cuantos cartuchos comparten un trozo son cuarenta y seis bytes
que estan en veintiseis Konami... y no son una rutina, son la TIPOGRAFIA:
3E 63 03 0E 03 63 3E dibuja un "3" y 7C 66 63 63 63 66 7C una "D". Konami
reusaba sus dibujos tanto como su codigo, y una matriz de bytes no distingue.

Aqui se distingue, y sin adivinar: el desensamblado de cada juego ya sabe que
bytes son codigo, porque su listado los lleva como instrucciones con la
direccion delante. Si la direccion de la tira aparece asi en el listado, es
codigo; si no, son datos. La direccion sale del ORG del Makefile mas el
desplazamiento.

Las cintas se comparan igual, avisando: un .tsx o un .cas lleva cabeceras y
tonos piloto que no son programa.

Uso: recoge_comun.py <raiz de DES_ASM> [minimo] > datos/comun.json
"""
import json
import os
import re
import sys
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")

K = 12                     # semilla: doce bytes iguales
MINIMO = 32                # por debajo de esto son coincidencias sueltas
GUARDA = 5                 # cuantas tiras se guardan por pareja


def origen(raiz, directorio):
    """El ORG que declara el Makefile del repositorio, o None."""
    mk = os.path.join(raiz, directorio, "Makefile")
    if not os.path.isfile(mk):
        return None
    m = re.search(r"^ORG\s*[:?]?=\s*(0x[0-9A-Fa-f]+)\s*$",
                  open(mk, encoding="utf-8", errors="replace").read(), re.M)
    return int(m.group(1), 16) if m else None


def direcciones_de_codigo(raiz, directorio, listados):
    """Las direcciones que el listado publica COMO INSTRUCCION.

    En estos listados cada instruccion lleva su direccion en un comentario
    `;xxxx`; los bloques de datos no. Asi que este conjunto es, literalmente, lo
    que el desensamblado afirma que es codigo.
    """
    dirs = set()
    for a in listados:
        ruta = os.path.join(raiz, directorio, a)
        if not os.path.isfile(ruta):
            continue
        with open(ruta, encoding="utf-8", errors="replace") as f:
            for ln in f:
                m = re.match(r"^\t.*;([0-9a-f]{4})", ln)
                if m:
                    dirs.add(int(m.group(1), 16))
    return dirs


def indexa(a):
    idx = defaultdict(list)
    for i in range(len(a) - K + 1):
        idx[a[i:i + K]].append(i)
    return idx


def tiras(a, idx, b, minimo):
    """Tiras maximales de a y b, sin solapes, con el indice de a ya hecho."""
    res, jb = [], 0
    while jb <= len(b) - K:
        cand = idx.get(b[jb:jb + K])
        if not cand:
            jb += 1
            continue
        mejor = (0, 0, 0)
        for ia in cand[:64]:              # un 12-grama muy repetido es relleno
            i, j = ia, jb
            while i > 0 and j > 0 and a[i - 1] == b[j - 1]:
                i -= 1
                j -= 1
            f1, f2 = ia + K, jb + K
            while f1 < len(a) and f2 < len(b) and a[f1] == b[f2]:
                f1 += 1
                f2 += 1
            if f1 - i > mejor[0]:
                mejor = (f1 - i, i, j)
        ln, ia, jbb = mejor
        if ln >= minimo and len(set(b[jbb:jbb + ln])) >= 4:
            res.append((ln, ia, jbb))
        jb = jbb + max(ln, 1)
    return res


def main():
    raiz = sys.argv[1]
    minimo = int(sys.argv[2]) if len(sys.argv) > 2 else MINIMO
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    with open(os.path.join(DATOS, "serie.json"), encoding="utf-8") as f:
        base = json.load(f)["proyectos"]

    juegos = []
    for p in base:
        b = p.get("binario")
        if not b:
            continue
        with open(os.path.join(raiz, b["fichero"]), "rb") as f:
            juegos.append({"clave": p["clave"], "titulo": p["titulo"],
                           "grupo": p.get("grupo"), "fichero": b["fichero"],
                           "sha256": b["sha256"],
                           "cinta": b["fichero"].lower().endswith((".tsx", ".cas")),
                           "org": origen(raiz, p["directorio"]),
                           "codigo": direcciones_de_codigo(raiz, p["directorio"],
                                                           p["listados"]),
                           "datos": f.read()})

    parejas = []
    for i, a in enumerate(juegos):
        idx = indexa(a["datos"])
        for b in juegos[i + 1:]:
            t = tiras(a["datos"], idx, b["datos"], minimo)
            if not t:
                continue
            t.sort(reverse=True)

            def clase(j, off, ln):
                """codigo / datos / desconocido, segun lo que diga su listado."""
                if j["org"] is None or not j["codigo"]:
                    return "desconocido"
                ini = j["org"] + off
                return ("codigo" if any(d in j["codigo"]
                                        for d in range(ini, ini + ln))
                        else "datos")

            detalle = []
            for ln, ia, jb in t[:GUARDA]:
                detalle.append({"bytes": ln, "en_a": "0x%04X" % ia,
                                "en_b": "0x%04X" % jb,
                                "es_en_a": clase(a, ia, ln),
                                "es_en_b": clase(b, jb, ln)})
            bytes_codigo = sum(d["bytes"] for d in detalle
                               if "codigo" in (d["es_en_a"], d["es_en_b"]))
            parejas.append({
                "a": a["clave"], "b": b["clave"],
                "tiras": len(t),
                "bytes_comunes": sum(x[0] for x in t),
                "la_mas_larga": t[0][0],
                "mismo_binario": a["sha256"] == b["sha256"],
                "bytes_de_codigo_en_las_guardadas": bytes_codigo,
                "mezcla_cinta_y_cartucho": a["cinta"] != b["cinta"],
                "detalle": detalle,
            })
        print("  %-24s hecho" % a["clave"], file=sys.stderr)

    parejas.sort(key=lambda x: -x["bytes_comunes"])
    print("parejas con algo en comun: %d de %d posibles"
          % (len(parejas), len(juegos) * (len(juegos) - 1) // 2), file=sys.stderr)
    json.dump({"minimo_bytes": minimo, "semilla": K, "juegos": len(juegos),
               "parejas": parejas}, sys.stdout, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
