#!/usr/bin/env python3
"""Las rutinas que comparten los desensamblados Konami de la serie, todos
contra todos, instruccion por instruccion.

La firma de una rutina es la lista de sus instrucciones desde su etiqueta
hasta el primer `ret`, `jp` o `jr` sin condicion, con los operandos de 16 bits
y los nombres tapados: en otro cartucho las direcciones cambian; los
registros, los valores de un byte y los saltos relativos no (es la firma de
PENNANTRACE2_DISAM/tools/cruza.py). Se mira desde cada etiqueta, con nombre
o L_XXXX (los listados nuevos dejan muchas rutinas comentadas sin bautizar),
con al menos MIN instrucciones y PROPIAS que no sean call, jp ni ret. Una
etiqueta de dentro de una rutina compartida da una cola que tambien casa:
de las que acaban en la misma instruccion solo cuenta la mas larga.

Dos juegos comparten una rutina si su firma sale en los dos listados; la
cuenta es de firmas distintas (una rutina que un cartucho lleva repetida
cuenta una vez), asi que es la misma vista desde los dos lados.

Uso: codigo_comun.py                 la matriz, de mas a menos
     codigo_comun.py --raiz <dir> ...  con los repositorios clonados en <dir>
     codigo_comun.py <clave>          con quien comparte ese juego, y que
     codigo_comun.py --json [fich]    todo, para las webs (datos/codigo_comun.json)
"""
import glob
import json
import os
import re
import sys
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
# donde estan los desensamblados: DES_ASM/desensamblados en la maquina de la
# serie, o --raiz <dir> con los repositorios clonados uno al lado de otro
DES = os.path.join(os.path.dirname(os.path.dirname(RAIZ)), "desensamblados")

MIN = 6
PROPIAS = 3
EXTENDIDAS = 15

# clave de la portada, carpeta local, repositorio y listados (en el orden de
# los bancos). Las
# carpetas con dos ROM usan una: Antarctic la japonesa 1, King's Valley II la
# de MSX (con sus bancos comunes), Yie Ar Kung-Fu la facil.
JUEGOS = [
    ("timepilot", "TIMEPILOT", "TimePilot-disassembly", ["src/timepilot.asm"]),
    ("frogger", "FROGGER", "Frogger-disassembly", ["src/frogger.asm"]),
    ("supercobra", "SUPERCOBRA", "SuperCobra-disassembly", ["src/supercobra.asm"]),
    ("athletic", "ATHLETIC", "AthleticLand-disassembly", ["src/athletic.asm"]),
    ("antarctic", "ANTARCTIC", "AntarcticAdventure-disassembly", ["src/jap1/antarctic.asm"]),
    ("monkey", "MONKEY", "MonkeyAcademy-disassembly", ["src/monkey.asm"]),
    ("billiards", "BILLIARDS", "KonamisBilliards-disassembly", ["src/billiards.asm"]),
    ("mahjong", "MAHJONG", "KonamisMahjongDojo-disassembly", ["src/mahjong.asm"]),
    ("hyperolympic1", "HYPEROLYMPIC1", "HyperOlympic1-disassembly", ["src/hyperolympic1.asm"]),
    ("hyperolympic2", "HYPEROLYMPIC2", "HyperOlympic2-disassembly", ["src/hyperolympic2.asm"]),
    ("circus", "CIRCUS", "CircusCharlie-disassembly", ["src/circus.asm"]),
    ("magicaltree", "MAGICALTREE", "MagicalTree-disassembly", ["src/magicaltree.asm"]),
    ("comicbakery", "COMICBAKERY", "ComicBakery-disassembly", ["src/comicbakery.asm"]),
    ("hyperrally", "HYPERRALLY", "HyperRally-disassembly", ["src/hyperrally.asm"]),
    ("skyjaguar", "SKYJAGUAR", "SkyJaguar-disassembly", ["src/skyjaguar.asm"]),
    ("golf", "GOLF", "KonamisGolf-disassembly", ["src/golf.asm"]),
    ("mopiranger", "MOPIRANGER", "MopiRanger-disassembly", ["src/mopiranger.asm"]),
    ("roadfighter", "ROADFIGHTER", "RoadFighter-disassembly", ["src/roadfighter.asm"]),
    ("pingpong", "PINGPONG", "KonamisPingPong-disassembly", ["src/pingpong.asm"]),
    ("soccer", "SOCCER", "KonamisSoccer-disassembly", ["src/soccer.asm"]),
    ("kingsvalley", "KINGSVALLEY", "KingsValley-disassembly", ["src/kingsvalley.asm"]),
    ("baseball", "BASEBALL", "KonamisBaseball-disassembly", ["src/baseball.asm"]),
    ("knightmare", "KNIGHTMARE", "Knightmare-disassembly", ["src/knightmare.asm"]),
    ("penguinadventure", "PENGUINADVENTURE", "PenguinAdventure-disassembly", ["src/penguinadventure_p??.asm"]),
    ("vampirekiller", "VAMPIREKILLER", "VampireKiller-disassembly", ["src/vampirekiller_p??.asm"]),
    ("goemon", "GOEMON", "GanbareGoemon-disassembly", ["src/goemon_p??.asm"]),
    ("synthesizer", "SYNTHESIZER", "KonamiSynthesizer-disassembly", ["src/synth.asm"]),
    ("nemesis2", "NEMESIS2", "Nemesis2-disassembly", ["src/nemesis2_p??.asm"]),
    ("usas", "USAS", "TreasureOfUsas-disassembly", ["src/usas_p??.asm"]),
    ("shalom", "SHALOM", "Shalom-disassembly", ["src/shalom_p??.asm"]),
    ("metalgear", "METALGEAR", "MetalGear-disassembly", ["src/metalgear_p??.asm"]),
    ("galious", "GALIOUS", "MazeOfGalious-disassembly", ["src/galious_p??.asm"]),
    ("kingkong2", "KINGKONG2", "KingKong2-disassembly", ["src/kingkong2_p??.asm"]),
    ("qbert", "QBERT", "Qbert-disassembly", ["src/qbert.asm"]),
    ("hinotori", "HINOTORI", "Hinotori-disassembly", ["src/hinotori_p??.asm"]),
    ("twinbee", "TWINBEE", "TwinBee-disassembly", ["src/twinbee.asm"]),
    ("boxing", "BOXING", "Boxing-disassembly", ["src/boxing.asm"]),
    ("yiearkungfu2", "YIEARKUNGFU2", "YieArKungFu2-disassembly", ["src/yiear2.asm"]),
    ("yiearkungfu", "YIEARKUNGFU", "YieArKungFu-disassembly", ["src/yiear.asm"]),
    ("tennis", "TENNIS", "KonamisTennis-disassembly", ["src/tennis.asm"]),
    ("hypersports1", "HYPERSPORTS1", "HyperSports1-disassembly", ["src/hypersports1.asm"]),
    ("hypersports2", "HYPERSPORTS2", "HyperSports2-disassembly", ["src/hypersports2.asm"]),
    ("hypersports3", "HYPERSPORTS3", "HyperSports3-disassembly", ["src/hypersports3.asm"]),
    ("gamemaster", "GAMEMASTER", "GameMaster-disassembly", ["src/gamemaster.asm"]),
    ("gamemaster2", "GAMEMASTER2", "GameMaster2-disassembly", ["src/gamemaster2_p??.asm"]),
    ("pennantrace", "PENNANTRACE", "PennantRace-disassembly", ["src/pennantrace_p??.asm"]),
    ("pennantrace2", "PENNANTRACE2", "PennantRace2-disassembly", ["src/pennantrace2_p??.asm"]),
    ("kingsvalley2", "KINGSVALLEY2", "KingsValley2-disassembly", ["src/msx1/*.asm", "src/comun/*.asm"]),
    ("parodius", "PARODIUS", "Parodius-disassembly", ["src/parodius_p??.asm"]),
    ("nemesis3", "NEMESIS3", "Nemesis3-disassembly", ["src/nemesis3_p??.asm"]),
    ("majutsushi", "MAJUTSUSHI", "Majutsushi-disassembly", ["src/majutsushi_p??.asm"]),
    ("contra", "CONTRA", "Contra-disassembly", ["src/contra_p??.asm"]),
    ("salamander", "SALAMANDER", "Salamander-disassembly", ["src/salamander_p??.asm"]),
    ("goonies", "GOONIES", "Goonies-disassembly", ["src/goonies.asm"]),
    ("cabbagepatch", "CABBAGEPATCH", "CabbagePatchKids-disassembly", ["src/cabbagepatch.asm"]),
    ("pippols", "PIPPOLS", "Pippols-disassembly", ["src/pippols.asm"]),
    ("nemesis", "NEMESIS", "Nemesis-disassembly", ["src/nemesis_p??.asm"]),
    ("f1spirit", "F1SPIRIT", "F1Spirit-disassembly", ["src/f1spirit_p??.asm"]),
    ("spacemanbow", "SPACEMANBOW", "SpaceManbow-disassembly", ["src/spacemanbow_p??.asm"]),
    ("metalgear2", "METALGEAR2", "MetalGear2-disassembly", ["src/metalgear2_p??.asm"]),
    ("quarth", "QUARTH", "Quarth-disassembly", ["src/quarth_p??.asm"]),
    ("sparkie", "SPARKIE", "Sparkie-disassembly", ["src/sparkie.asm"]),
    ("junofirst", "JUNOFIRST", "JunoFirst-disassembly", ["src/junofirst.asm"]),
]

LINEA = re.compile(r"^\t(\S[^;]*?)\s*;([0-9a-f]{4})\b")
ETIQ = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):")
H16 = re.compile(r"\b0[0-9a-f]{4}h\b|\b[0-9a-f]{4}h\b")
BANCO = re.compile(r"_p(\d\d)\.asm$")


def lee(ruta):
    """Lista de (direccion, etiqueta o None, instruccion)."""
    res, etq = [], None
    for ln in open(ruta, encoding="utf-8", errors="replace"):
        m = ETIQ.match(ln)
        if m:
            etq = m.group(1)
            continue
        m = LINEA.match(ln)
        if not m:
            continue
        res.append((int(m.group(2), 16), etq, re.sub(r"\s+", " ", m.group(1).strip())))
        etq = None
    return res


def tapa(ins):
    op, _, arg = ins.partition(" ")
    if op in ("defb", "defw", "defm", "defs", "db", "dw", "ds"):
        return None
    arg = H16.sub("NN", arg)
    if op in ("jr", "djnz"):
        arg = re.sub(r"[A-Za-z_][A-Za-z0-9_]*$", "R", arg)
    elif op in ("call", "jp"):
        arg = re.sub(r"(?<![(])\b[A-Za-z_][A-Za-z0-9_]*$", "NN", arg) if "(" not in arg else arg
    else:
        arg = re.sub(r"\b(?:L_[0-9A-F]{4}|[a-z_][a-z0-9_]{3,})\b", "NN", arg)
    return op + " " + arg


def firma(ins, k):
    f = []
    for j in range(k, min(k + 80, len(ins))):
        t = tapa(ins[j][2])
        if t is None:
            return None
        f.append(t)
        op, _, arg = ins[j][2].partition(" ")
        if op in ("ret", "reti", "retn") and not arg:
            return tuple(f)
        if op in ("jp", "jr") and "," not in arg:
            return tuple(f)
    return None


def propias(f):
    return sum(1 for t in f if not t.startswith(("call", "jp", "ret")))


def rutinas(clave, carpeta, repo, globs):
    """firma -> [(banco, direccion, nombre, final)]; final = (fichero, indice
    de su ultima instruccion), lo que comparten una rutina y sus colas."""
    por_firma = defaultdict(list)
    ficheros = []
    for dir_ in (carpeta + "_DISAM", repo):
        for g in globs:
            ficheros += sorted(glob.glob(os.path.join(DES, dir_, g)))
        if ficheros:
            break
    if not ficheros:
        sys.exit("sin listados: " + clave)
    for n, r in enumerate(ficheros):
        m = BANCO.search(r)
        b = int(m.group(1)) if m else None
        ins = lee(r)
        for k, (a, etq, _) in enumerate(ins):
            if not etq:
                continue
            f = firma(ins, k)
            if f and len(f) >= MIN and propias(f) >= PROPIAS:
                por_firma[f].append((b, a, etq, (n, k + len(f) - 1)))
    return por_firma


def donde(b, a):
    return ("p%02d:%04X" % (b, a)) if b is not None else ("0x%04X" % a)


def calcula():
    tabla = {c: rutinas(c, d, r, g) for c, d, r, g in JUEGOS}
    unicas = {c: {f: v[0] for f, v in t.items()} for c, t in tabla.items()}
    # en cuantos juegos sale cada firma
    juegos_de = defaultdict(set)
    for c, u in unicas.items():
        for f in u:
            juegos_de[f].add(c)
    pares = {}
    claves = [j[0] for j in JUEGOS]
    for i, a in enumerate(claves):
        for b in claves[i + 1:]:
            comun = set(unicas[a]) & set(unicas[b])
            # de las que acaban en el mismo sitio (en cualquiera de los dos),
            # la mas larga: las otras son colas de la misma rutina
            larga = {}
            for f in comun:
                for lado in (a, b):
                    fin = (lado, unicas[lado][f][3])
                    if fin not in larga or len(f) > len(larga[fin]):
                        larga[fin] = f
            comun = [f for f in comun
                     if larga[(a, unicas[a][f][3])] is f and larga[(b, unicas[b][f][3])] is f]
            if comun:
                pares[(a, b)] = sorted(comun, key=lambda f: unicas[a][f][:2])
    return claves, unicas, juegos_de, pares


def main(argv):
    global DES
    if "--raiz" in argv:
        i = argv.index("--raiz")
        DES = argv[i + 1]
        del argv[i:i + 2]
    claves, unicas, juegos_de, pares = calcula()
    if len(argv) > 1 and argv[1] == "--json":
        fich = argv[2] if len(argv) > 2 else os.path.join(RAIZ, "datos", "codigo_comun.json")
        out = {"min": MIN, "propias": PROPIAS, "juegos": {}}
        for c in claves:
            vec = []
            for (a, b), fs in pares.items():
                if c not in (a, b):
                    continue
                o = b if a == c else a
                vec.append({
                    "con": o,
                    "rutinas": len(fs),
                    "instrucciones": sum(len(f) for f in fs),
                    "lista": [[unicas[c][f][2], donde(*unicas[c][f][:2]),
                               unicas[o][f][2], donde(*unicas[o][f][:2]), len(f),
                               len(juegos_de[f])] for f in fs],
                })
            vec.sort(key=lambda v: (-v["rutinas"], v["con"]))
            out["juegos"][c] = {"comparte": vec}
        # los bloques que salen en mas cartuchos; una cola que va en los mismos
        # cartuchos que la rutina entera de la que sale no se cuenta aparte
        elegidas = []
        for f in sorted(juegos_de, key=lambda f: (-len(juegos_de[f]), -len(f))):
            if len(juegos_de[f]) < 2 or len(elegidas) == EXTENDIDAS:
                break
            if any(len(g) > len(f) and g[-len(f):] == f and juegos_de[g] >= juegos_de[f]
                   for g in elegidas):
                continue
            elegidas.append(f)
        out["extendidas"] = [{
            "instrucciones": len(f),
            "juegos": [c for c in claves if c in juegos_de[f]],
            "nombres": sorted({unicas[c][f][2] for c in juegos_de[f]
                               if not unicas[c][f][2].startswith("L_")}),
            "sin_nombre": sum(1 for c in juegos_de[f] if unicas[c][f][2].startswith("L_")),
            "codigo": list(f),
        } for f in elegidas]
        out["parejas"] = len(claves) * (len(claves) - 1) // 2
        out["con_algo"] = len(pares)
        with open(fich, "w", encoding="utf-8", newline=chr(10)) as fh:
            json.dump(out, fh, ensure_ascii=False, indent=1)
            fh.write(chr(10))
        print("escrito", fich)
        return
    if len(argv) > 1:
        c = argv[1]
        for (a, b), fs in sorted(pares.items(), key=lambda x: -len(x[1])):
            if c in (a, b):
                o = b if a == c else a
                print("%-18s %4d rutinas" % (o, len(fs)))
                if "-v" in argv:
                    for f in fs:
                        print("    %-28s %-9s = %-28s %-9s %3d instr, en %d juegos" % (
                            unicas[c][f][2], donde(*unicas[c][f][:2]),
                            unicas[o][f][2], donde(*unicas[o][f][:2]), len(f), len(juegos_de[f])))
        return
    for (a, b), fs in sorted(pares.items(), key=lambda x: -len(x[1])):
        print("%-18s %-18s %4d" % (a, b, len(fs)))


if __name__ == "__main__":
    main(sys.argv)
