#!/usr/bin/env python3
"""Donde esta cada repo dentro de DES_ASM.

Desde el 2026-10-17 los repos no cuelgan de la raiz de DES_ASM sino de una
carpeta por tipo (desensamblados/, parches/, web/, comun/, archivo/). Los
datos de la base siguen nombrando cada repo por su carpeta ("3DGOLF_DISAM",
"3DGOLF_DISAM/3dgolf.rom"): estas dos funciones lo resuelven.
"""
import os

GRUPOS = ("desensamblados", "parches", "web", "comun", "archivo")


def en_des_asm(raiz, primero, *resto):
    """os.path.join(raiz, primero, *resto), buscando el primer trozo de la
    ruta (la carpeta del repo) en la raiz o en uno de los GRUPOS."""
    rel = os.path.join(primero, *resto) if resto else primero
    cabeza = rel.replace("\\", "/").split("/", 1)[0]
    if os.path.exists(os.path.join(raiz, cabeza)):
        return os.path.join(raiz, rel)
    for g in GRUPOS:
        if os.path.exists(os.path.join(raiz, g, cabeza)):
            return os.path.join(raiz, g, rel)
    return os.path.join(raiz, rel)


def repos_de(raiz):
    """Los nombres de carpeta de la raiz y de cada grupo, como os.listdir."""
    out = [d for d in os.listdir(raiz) if d not in GRUPOS]
    for g in GRUPOS:
        if os.path.isdir(os.path.join(raiz, g)):
            out += os.listdir(os.path.join(raiz, g))
    return out
