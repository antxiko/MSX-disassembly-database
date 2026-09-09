#!/usr/bin/env python3
"""Recoge los datos de cada proyecto tal y como los PUBLICA la portada.

La portada de antxiko.github.io ya lleva, en `tools/make_index.py`, la ficha de
cada proyecto: titulo, ano, grupo, fabricante, y las URL del repositorio y de la
web. Es lo que la serie declara de cara afuera, asi que es la fuente de los
metadatos y no se vuelve a teclear aqui: se importa el modulo y se leen sus
listas. Si la portada cambia, esta base de datos cambia con ella.

Lo que la portada NO dice es en que directorio local vive cada repositorio. Eso
se resuelve al reves y sin suponer: se lee el `git remote` de cada directorio de
DES_ASM y se casa con la URL que declara la portada. Un proyecto de la portada
sin directorio local se marca; un directorio local que no esta en la portada,
tambien. Ni se inventa ni se empareja por parecido del nombre.

Uso: recoge_portada.py <raiz de DES_ASM> > datos/proyectos.json
"""
import html
import json
import os
import re
import subprocess
import sys

PORTADA = "ANTXIKO_GITHUB_IO"


def limpia(t):
    """Las fichas de la portada llevan entidades HTML y algo de marcado."""
    if not isinstance(t, str):
        return t
    return html.unescape(re.sub(r"<[^>]+>", "", t)).strip()


def remoto(d):
    """La URL del remote origin de un directorio, o None."""
    try:
        p = subprocess.run(["git", "remote", "get-url", "origin"], cwd=d,
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    return p.stdout.strip() or None


def normaliza(url):
    """github.com/usuario/repo, sin esquema, sin .git y en minusculas."""
    if not url:
        return None
    u = re.sub(r"^(https?://|git@)", "", url).replace("github.com:", "github.com/")
    return re.sub(r"\.git$", "", u).rstrip("/").lower()


def ficha(p, categoria):
    """Pasa una entrada de la portada a un registro plano."""
    return {"clave": p["clave"], "categoria": categoria,
            "grupo": p.get("grupo"), "titulo": limpia(p["titulo"]),
            "anio": p.get("anio"), "repo_url": p.get("repo"),
            "web_url": p.get("web"),
            "meta_en": limpia(p.get("meta", {}).get("en")),
            "meta_es": limpia(p.get("meta", {}).get("es"))}


def main():
    raiz = sys.argv[1]
    # La consola de Windows no es UTF-8: sin esto, un punto medio
    # del titulo de un juego sale roto en el JSON.
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    sys.path.insert(0, os.path.join(raiz, PORTADA, "tools"))
    import make_index

    fichas = ([ficha(p, "desensamblado") for p in make_index.DESENSAMBLADOS]
              + [ficha(p, "parche") for p in make_index.PARCHES])

    # Los directorios locales, por su remote.
    locales = {}
    for d in sorted(os.listdir(raiz)):
        ruta = os.path.join(raiz, d)
        if not os.path.isdir(os.path.join(ruta, ".git")):
            continue
        locales[d] = normaliza(remoto(ruta))

    usados = set()
    for f in fichas:
        objetivo = normaliza(f["repo_url"])
        casan = [d for d, u in locales.items() if u and u == objetivo]
        f["directorio"] = casan[0] if len(casan) == 1 else None
        f["aviso"] = None
        if not casan:
            f["aviso"] = "sin directorio local con ese remote"
        elif len(casan) > 1:
            f["aviso"] = "varios directorios con ese remote: %s" % ", ".join(casan)
        usados.update(casan)

    huerfanos = [{"directorio": d, "remote": u}
                 for d, u in locales.items() if d not in usados]

    json.dump({"proyectos": fichas, "sin_ficha_en_la_portada": huerfanos},
              sys.stdout, indent=1, ensure_ascii=False)
    print("portada: %d fichas | local: %d repos | sin ficha: %d"
          % (len(fichas), len(locales), len(huerfanos)), file=sys.stderr)


if __name__ == "__main__":
    main()
