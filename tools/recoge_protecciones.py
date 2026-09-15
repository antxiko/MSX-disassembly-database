#!/usr/bin/env python3
"""Busca en cada listado las escrituras que el cartucho hace a su PROPIO espacio.

Es el patron de la proteccion anticopia de Konami, y lo identifico **Manuel
Pazos** en su desensamblado del RC-727 (`ReadKeys_AC` y `VRAM_writeAC`).

Como funciona la trampa. El cartucho ejecuta una instruccion que escribe dentro
de su propio rango de direcciones. Corriendo desde ROM la escritura no llega -la
ROM no admite escritura- y la instruccion parece codigo muerto. Pero un cartucho
pirateado es una copia cargada en RAM, y ahi si cuela: deja el juego tocado en
un sitio del que no se vuelve.

Que se mide aqui, y que NO. Se mide sobre el listado que cada repositorio
publica, no sobre el binario: hace falta saber que es codigo y que son datos, y
eso lo dice el trazado. De cada escritura se saca:

  - donde esta y a donde apunta
  - QUE INSTRUCCION hay en el destino, que es lo que dice si la escritura cae
    en el arranque de una rutina (letal) o dentro del operando de un salto
  - de donde sale el valor que escribe: muchas veces es un opcode que ya estaba
    en la ROM, y eso descarta la casualidad

NO se mide el efecto en RAM: eso pediria cargar una copia y jugarla, y aqui no
se distribuye ningun binario. Lo que se afirma es lo que se lee del listado.

SOLO tiene sentido en cartuchos. Un juego de cinta se carga entero en RAM y
escribir en su propio espacio es lo normal, no una trampa: los de cinta salen
con la marca `no_aplica`.

Uso: recoge_protecciones.py <raiz> > datos/protecciones.json
"""
import io
import json
import os
import re
import subprocess
import sys

RE_INS = re.compile(r"^\t(.*?)\s*;([0-9a-f]{4})(.*)$")
# ld (nnnn),reg -- escritura a una direccion absoluta
RE_ESC = re.compile(r"^ld\s+\((0[0-9a-f]{3,4}h|0x[0-9A-Fa-f]+)\)\s*,\s*(a|hl|bc|de|ix|iy)$",
                    re.I)


def num(s):
    s = s.strip()
    return int(s[:-1], 16) if s.lower().endswith("h") else int(s, 16)


# Lo que invalida la pareja: que el registro se recargue por el camino, o que
# el flujo se vaya a otra parte y ya no se pueda dar por bueno lo que lleva.
CORTA = re.compile(r"^(call|jp|jr|ret|rst|djnz|halt|ex\s+\(sp\))", re.I)
TOCA = {
    "hl": re.compile(r"^(ld\s+(hl|h|l)\s*,|inc\s+hl|dec\s+hl|add\s+hl|adc\s+hl|"
                     r"sbc\s+hl|pop\s+hl|ex\s+de\s*,\s*hl|ldir|ldi|ldd|lddr)", re.I),
    "de": re.compile(r"^(ld\s+(de|d|e)\s*,|inc\s+de|dec\s+de|pop\s+de|"
                     r"ex\s+de\s*,\s*hl)", re.I),
}


def pisa(ins, reg):
    return bool(CORTA.match(ins) or TOCA[reg].match(ins))


def listados(d):
    """Los .asm del juego que el repositorio publica."""
    try:
        fs = subprocess.check_output(["git", "-C", d, "ls-files", "*.asm"]).decode()
    except Exception:
        return []
    out = []
    for f in fs.split("\n"):
        f = f.strip()
        if not f or f.startswith("src/cartucho/") or f.startswith("src/parche/"):
            continue
        p = os.path.join(d, f)
        if os.path.exists(p):
            out.append((f, p))
    return out


def mira(ruta):
    """(rango, [escritura...]) de un listado."""
    lineas = io.open(ruta, encoding="utf-8", errors="replace").read().split("\n")
    porDir, orden = {}, []
    for ln in lineas:
        m = RE_INS.match(ln)
        if m:
            a = int(m.group(2), 16)
            porDir[a] = m.group(1).strip()
            orden.append(a)
    if not orden:
        return None, []
    lo, hi = min(orden), max(orden)
    dirs = sorted(porDir)
    fuera = []
    # Las instrucciones, en orden, con su direccion: hace falta mirar hacia
    # adelante para los dos patrones que no son un `ld (nnnn),reg` suelto.
    seq = [(int(m.group(2), 16), m.group(1).strip())
           for m in (RE_INS.match(x) for x in lineas) if m]
    porIdx = {a: k for k, (a, _) in enumerate(seq)}

    def apunta_al_propio(k):
        """Un destino cargado en un registro y usado despues para escribir.

        Son los dos que un `ld (nnnn),reg` no ve:
          ld hl,CONST ... ld (hl),algo     -escribe byte a byte-
          ld de,CONST ... ldir             -copia un bloque-
        Se mira solo tres instrucciones por delante: mas alla el registro ya
        no se puede dar por bueno sin seguir el flujo, y aqui no se supone.
        """
        a, ins = seq[k]
        m = re.match(r"^ld\s+(hl|de)\s*,\s*(0[0-9a-f]{3,4}h|0x[0-9A-Fa-f]+)$",
                     ins, re.I)
        if not m:
            return None
        reg, v = m.group(1).lower(), num(m.group(2))
        if not (lo <= v <= hi):
            return None
        for j in range(k + 1, min(k + 4, len(seq))):
            otra = seq[j][1].lower()
            if reg == "hl" and re.match(r"^ld\s+\(hl\)\s*,", otra):
                return v, seq[j][0], otra
            if reg == "de" and otra in ("ldir", "ldi"):
                return v, seq[j][0], otra
            # Si algo por el camino toca el registro o rompe el flujo, la
            # pareja ya no vale: el valor que llega a la escritura no es el
            # que se cargo. Sin esto salian falsos positivos a pares -una
            # carga legitima de HL emparejada con un `ld (hl)` de otra cosa-.
            if pisa(otra, reg):
                return None
        return None

    for k, (a, ins) in enumerate(seq):
        hallado = apunta_al_propio(k)
        if not hallado:
            continue
        v, donde_escribe, como = hallado
        cont = None
        for x in dirs:
            if x <= v:
                cont = x
            else:
                break
        fuera.append({
            "donde": "0x%04X" % donde_escribe,
            "instruccion": como,
            "carga": "%s  (en 0x%04X)" % (ins, a),
            "destino": "0x%04X" % v,
            "cae_en": "0x%04X" % cont if cont is not None else None,
            "instruccion_del_destino": porDir.get(cont) if cont is not None else None,
            "es_el_primer_byte": cont == v,
        })

    for i, ln in enumerate(lineas):
        m = RE_INS.match(ln)
        if not m:
            continue
        ins, a = m.group(1).strip(), int(m.group(2), 16)
        me = RE_ESC.match(ins)
        if not me:
            continue
        v = num(me.group(1))
        if not (lo <= v <= hi):
            continue
        # la instruccion anterior: de ahi sale el valor que escribe
        antes = ""
        for j in range(i - 1, max(-1, i - 3), -1):
            mm = RE_INS.match(lineas[j])
            if mm:
                antes = mm.group(1).strip()
                break
        # que instruccion CONTIENE el destino
        cont = None
        for x in dirs:
            if x <= v:
                cont = x
            else:
                break
        fuera.append({
            "donde": "0x%04X" % a,
            "instruccion": ins,
            "carga": antes,
            "destino": "0x%04X" % v,
            "cae_en": "0x%04X" % cont if cont is not None else None,
            "instruccion_del_destino": porDir.get(cont) if cont is not None else None,
            "es_el_primer_byte": cont == v,
        })
    return (lo, hi), fuera


def main(raiz):
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "datos", "serie.json")
    with io.open(base, encoding="utf-8") as f:
        proyectos = json.load(f)["proyectos"]

    filas, con = [], 0
    for p in proyectos:
        d = os.path.join(raiz, p["directorio"])
        # cartucho o cinta: lo dice la ficha, no el nombre del fichero
        meta = (p.get("meta_es") or "") + (p.get("meta_en") or "")
        cartucho = "cartucho" in meta or "cartridge" in meta
        fila = {"clave": p["clave"], "titulo": p["titulo"],
                "directorio": p["directorio"], "es_cartucho": cartucho,
                "escrituras": [], "nota": None}
        if not cartucho:
            fila["nota"] = ("no_aplica: se carga entero en RAM, escribir en su "
                            "propio espacio no es una trampa")
            filas.append(fila)
            continue
        for rel, ruta in listados(d):
            rango, fuera = mira(ruta)
            for e in fuera:
                e["listado"] = rel
                fila["escrituras"].append(e)
        if fila["escrituras"]:
            con += 1
        filas.append(fila)

    json.dump(filas, sys.stdout, indent=1, ensure_ascii=False)
    print("", file=sys.stderr)
    print("cartuchos mirados: %d | con escrituras a su propio espacio: %d"
          % (sum(1 for f in filas if f["es_cartucho"]), con), file=sys.stderr)


main(sys.argv[1] if len(sys.argv) > 1 else "..")
