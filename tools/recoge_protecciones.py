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


def zona(v, lo, hi, mapper=None):
    """Donde cae un destino que no admite escritura en la maquina de verdad.

    "propio"  dentro del listado del propio cartucho
    "bios"    en la pagina 0, que en un MSX es la ROM de la BIOS

    La segunda hace falta por el RC-701: su guardian copia `jp 0000h` encima de
    0x0000, y una cuarta compilacion del mismo juego lleva ESA MISMA copia
    apuntada a su propio espacio. Pero una escritura a la BIOS no es proteccion
    por el hecho de serlo: se registra aparte y cada una se explica, o se dice
    que esta sin explicar.
    """
    if mapper is not None:
        # MegaROM: el cartucho es toda la ventana, menos sus registros
        if 0x4000 <= v <= 0xBFFF and not any(a <= v <= b for a, b in mapper):
            return "propio"
    elif lo <= v <= hi:
        return "propio"
    if v < 0x4000:
        return "bios"
    return None


# Los registros de los dos mappers de la casa. Escribir ahi NO es escribir en
# la ROM: es cambiar de banco, y en un MegaROM pasa cientos de veces.
MAPPER_KONAMI = [(0x6000, 0x6000), (0x8000, 0x8000), (0xA000, 0xA000)]
MAPPER_SCC = [(0x5000, 0x57FF), (0x7000, 0x77FF), (0x9000, 0x97FF),
              (0xB000, 0xB7FF), (0x9800, 0x9FFF)]   # el ultimo, el propio SCC


def mapper_de(textos):
    """Que mapper usa, deducido de a donde escribe. None si no es MegaROM.

    Un MegaROM se lista por bancos, un fichero por banco, y cada banco solo
    cubre su trozo de ventana: comprobando el destino contra el rango del
    propio fichero, una escritura a otro banco no se veia nunca. Asi se habian
    quedado Nemesis y F-1 Spirit con cero escrituras.
    """
    todo = "\n".join(textos)
    konami = len(re.findall(r"(?m)^\tld \(0[68a]000h\),a", todo))
    scc = len(re.findall(r"(?m)^\tld \(0[579b]000h\),a", todo))
    if not konami and not scc:
        return None
    return MAPPER_SCC if scc > konami else MAPPER_KONAMI


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


def mira(ruta, mapper=None):
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
        if zona(v, lo, hi, mapper) is None:
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
            "zona": zona(v, lo, hi, mapper),
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
        if zona(v, lo, hi, mapper) is None:
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
            "zona": zona(v, lo, hi, mapper),
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

    filas, con, bios = [], 0, 0
    for p in proyectos:
        d = os.path.join(raiz, p["directorio"])
        # cartucho o cinta: lo dice la ficha, no el nombre del fichero
        meta = (p.get("meta_es") or "") + (p.get("meta_en") or "")
        cartucho = any(x in meta for x in ("cartucho", "cartridge", "MegaROM"))
        fila = {"clave": p["clave"], "titulo": p["titulo"],
                "directorio": p["directorio"], "es_cartucho": cartucho,
                "escrituras": [], "nota": None}
        if not cartucho:
            fila["nota"] = ("no_aplica: se carga entero en RAM, escribir en su "
                            "propio espacio no es una trampa")
            filas.append(fila)
            continue
        ls = listados(d)
        mapper = (mapper_de([io.open(r, encoding="utf-8", errors="replace").read()
                             for _, r in ls])
                  if "MegaROM" in meta else None)
        fila["mapper"] = ("scc" if mapper is MAPPER_SCC else
                          "konami" if mapper is MAPPER_KONAMI else None)
        for rel, ruta in ls:
            rango, fuera = mira(ruta, mapper)
            for e in fuera:
                e["listado"] = rel
                fila["escrituras"].append(e)
        if any(e["zona"] == "propio" for e in fila["escrituras"]):
            con += 1
        if any(e["zona"] == "bios" for e in fila["escrituras"]):
            bios += 1
        filas.append(fila)

    json.dump(filas, sys.stdout, indent=1, ensure_ascii=False)
    print("", file=sys.stderr)
    print("cartuchos mirados: %d | a su propio espacio: %d | a la ROM de la BIOS: %d"
          % (sum(1 for f in filas if f["es_cartucho"]), con, bios), file=sys.stderr)


main(sys.argv[1] if len(sys.argv) > 1 else "..")
