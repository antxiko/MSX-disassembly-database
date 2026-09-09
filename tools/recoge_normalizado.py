#!/usr/bin/env python3
"""Que rutinas comparten los cartuchos, SIN QUE LAS DIRECCIONES ESTORBEN.

Por que hace falta esto habiendo ya `recoge_comun.py`. Aquel compara bytes, y
por eso solo ve una rutina compartida si ademas la ensamblaron en la MISMA
direccion. En cuanto cambia el mapa de memoria, la misma rutina da bytes
distintos -sus `call` y sus `ld hl,nn` apuntan a otro sitio- y desaparece de la
matriz. Con ese metodo no se puede contestar si Konami tenia uno o dos
armazones: sale un continuo.

Aqui cada instruccion se NORMALIZA poniendo a cero sus operandos de dieciseis
bits, que son los que llevan direcciones, y se comparan secuencias de
INSTRUCCIONES en vez de bytes. Un tramo largo de instrucciones iguales salvo las
direcciones es la misma rutina reensamblada en otro sitio.

DE DONDE SALE QUE ES CODIGO Y CUANTO MIDE CADA INSTRUCCION. No se traza nada: se
lee el listado que el desensamblado publica. Ahi cada instruccion lleva su
direccion en un comentario `;xxxx`, asi que las direcciones ordenadas SON el
codigo, y la longitud de cada instruccion es la distancia hasta la siguiente.
Eso es lo mas honrado que hay: es lo que ese desensamblado afirma, reensambla
byte a byte y esta comprobado por sus propios tests.

Cuando la distancia hasta la siguiente pasa de cuatro bytes -el maximo del
Z80- es que en medio hay datos: ahi se CORTA la tira, porque seguir seria pegar
dos trozos que no van juntos.

Uso: recoge_normalizado.py <raiz de DES_ASM> [minimo] > datos/normalizado.json
"""
import json
import os
import re
import sys
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")

# Opcodes cuyos dos ultimos bytes son una direccion o un inmediato de 16 bits.
# Es la lista de `comun_normalizado.py`, la herramienta de la serie.
ABS16 = ({0x01, 0x11, 0x21, 0x31, 0x22, 0x2A, 0x32, 0x3A, 0xC3, 0xCD}
         | {0xC2, 0xCA, 0xD2, 0xDA, 0xE2, 0xEA, 0xF2, 0xFA}
         | {0xC4, 0xCC, 0xD4, 0xDC, 0xE4, 0xEC, 0xF4, 0xFC})

K = 6           # semilla: seis instrucciones seguidas
MINIMO = 12     # por debajo de doce instrucciones son coincidencias sueltas


def normaliza(bs):
    """Pone a cero el operando de 16 bits, si lo lleva."""
    q = bytearray(bs)
    op = q[0]
    if op in ABS16 and len(q) >= 3:
        q[-2] = q[-1] = 0
    elif op in (0xDD, 0xFD) and len(q) >= 4 and q[1] in ABS16:
        q[-2] = q[-1] = 0
    elif op == 0xED and len(q) == 4:
        q[-2] = q[-1] = 0
    return bytes(q)


def tira(raiz, directorio, listados, rom, org):
    """La secuencia de instrucciones normalizadas del cartucho.

    Devuelve una lista de instrucciones y, en paralelo, su direccion. Un corte
    -donde el listado deja de ser contiguo- se marca con None para que ninguna
    coincidencia lo cruce.
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
    orden = sorted(dirs)
    instr, donde = [], []
    for i, a in enumerate(orden):
        if i + 1 >= len(orden):
            break
        n = orden[i + 1] - a
        off = a - org
        if not (1 <= n <= 4) or off < 0 or off + n > len(rom):
            instr.append(None)          # corte: en medio hay datos
            donde.append(None)
            continue
        instr.append(normaliza(rom[off:off + n]))
        donde.append(a)
    return instr, donde


def tramos(a, idx, b, minimo):
    """Tramos maximales de instrucciones comunes, sin solapes."""
    res, jb = [], 0
    while jb <= len(b) - K:
        clave = tuple(b[jb:jb + K])
        if None in clave:
            jb += 1
            continue
        cand = idx.get(clave)
        if not cand:
            jb += 1
            continue
        mejor = (0, 0, 0)
        for ia in cand[:64]:
            i, j = ia, jb
            while (i > 0 and j > 0 and a[i - 1] is not None
                   and a[i - 1] == b[j - 1]):
                i -= 1
                j -= 1
            f1, f2 = ia + K, jb + K
            while (f1 < len(a) and f2 < len(b) and a[f1] is not None
                   and a[f1] == b[f2]):
                f1 += 1
                f2 += 1
            if f1 - i > mejor[0]:
                mejor = (f1 - i, i, j)
        ln, ia, jbb = mejor
        if ln >= minimo:
            res.append((ln, ia, jbb))
        jb = jbb + max(ln, 1)
    return res


def org_de(raiz, directorio):
    mk = os.path.join(raiz, directorio, "Makefile")
    if not os.path.isfile(mk):
        return None
    m = re.search(r"^ORG\s*[:?]?=\s*(0x[0-9A-Fa-f]+)\s*$",
                  open(mk, encoding="utf-8", errors="replace").read(), re.M)
    return int(m.group(1), 16) if m else None


def main():
    raiz = sys.argv[1]
    minimo = int(sys.argv[2]) if len(sys.argv) > 2 else MINIMO
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    with open(os.path.join(DATOS, "serie.json"), encoding="utf-8") as f:
        base = json.load(f)["proyectos"]

    juegos, fuera = [], []
    for p in base:
        b = p.get("binario")
        org = org_de(raiz, p["directorio"]) if p.get("directorio") else None
        if not b or org is None or not p["listados"]:
            fuera.append({"clave": p["clave"],
                          "por": ("sin ORG en el Makefile" if b else
                                  "sin un binario unico")})
            continue
        with open(os.path.join(raiz, b["fichero"]), "rb") as f:
            rom = f.read()
        instr, donde = tira(raiz, p["directorio"], p["listados"], rom, org)
        utiles = sum(1 for x in instr if x is not None)
        if utiles < 100:
            fuera.append({"clave": p["clave"], "por": "muy poco codigo legible"})
            continue
        juegos.append({"clave": p["clave"], "titulo": p["titulo"],
                       "grupo": p.get("grupo"), "sha256": b["sha256"],
                       "org": org, "instrucciones": utiles,
                       "tira": instr, "donde": donde})
        print("  %-22s %5d instrucciones" % (p["clave"], utiles), file=sys.stderr)

    parejas = []
    for i, a in enumerate(juegos):
        idx = defaultdict(list)
        for k in range(len(a["tira"]) - K + 1):
            clave = tuple(a["tira"][k:k + K])
            if None not in clave:
                idx[clave].append(k)
        for b in juegos[i + 1:]:
            if a["sha256"] == b["sha256"]:
                continue
            t = tramos(a["tira"], idx, b["tira"], minimo)
            if not t:
                continue
            t.sort(reverse=True)
            parejas.append({
                "a": a["clave"], "b": b["clave"],
                "tramos": len(t),
                "instrucciones_comunes": sum(x[0] for x in t),
                "el_mayor": t[0][0],
                # cuanto de CADA uno es compartido: es lo que dice si son
                # parientes o si solo se rozan
                "porcentaje_de_a": round(100.0 * sum(x[0] for x in t)
                                         / a["instrucciones"], 1),
                "porcentaje_de_b": round(100.0 * sum(x[0] for x in t)
                                         / b["instrucciones"], 1),
                "detalle": [{"instrucciones": ln,
                             "en_a": "0x%04X" % a["donde"][ia],
                             "en_b": "0x%04X" % b["donde"][jb]}
                            for ln, ia, jb in t[:5]],
            })
        print("    (%d/%d)" % (i + 1, len(juegos)), file=sys.stderr)

    parejas.sort(key=lambda x: -x["instrucciones_comunes"])
    print("cartuchos: %d | parejas con algo: %d | fuera: %d"
          % (len(juegos), len(parejas), len(fuera)), file=sys.stderr)
    json.dump({"minimo_instrucciones": minimo, "semilla": K,
               "cartuchos": [{k: g[k] for k in
                              ("clave", "titulo", "grupo", "org", "instrucciones")}
                             for g in juegos],
               "fuera": fuera, "parejas": parejas},
              sys.stdout, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
