#!/usr/bin/env python3
"""Agrupa los cartuchos por el armazon que comparten.

Sobre `datos/normalizado.json`, que ya dice que porcentaje del codigo de cada
cartucho aparece tambien en otro. Aqui se unen los que comparten lo bastante y
se mira que sale.

DE DONDE SALE EL UMBRAL, QUE ES LA UNICA DECISION DE ESTE PROGRAMA. Se une una
pareja cuando el codigo comun es al menos el N % de AMBOS -el minimo de los dos
porcentajes, no la media: que Road Fighter comparta el 10 % de lo suyo con
Soccer no significa nada si para Soccer es el 4 %-. Barriendo N de 2 a 10 se ve
que el reparto NO es arbitrario:

    N = 2 %   4 grupos: 28 + 2 + 1 + 1      todo pegado, el umbral no separa
    N = 4 %   6 grupos: 22 + 5 + 2 + ...
    N = 5 %   8 grupos: 20 + 5 + 2 + ...
    N = 6 %  12 grupos: 16 + 5 + 2 + ...
    N = 8 %  24 grupos:  5 + 3 + 2 + 2 ...  la familia grande ya se deshace

El grupo de cinco y el de dos son LOS MISMOS del 4 % al 8 %, mientras la familia
grande se va deshaciendo poco a poco. Eso es lo que distingue una familia de un
artefacto del umbral, y por eso se publica el 5 %: esta en mitad de la banda
donde los grupos pequenos aguantan.

CUIDADO AL LEERLO. Esto agrupa por CODIGO COMPARTIDO MEDIDO, y nada mas. Que dos
cartuchos caigan en la misma familia no dice que los escribiera el mismo equipo
ni que uno saliera del otro: dice que hoy tienen rutinas en comun. Y la familia
grande, con veinte cartuchos unidos por el 5 %, es mas un vecindario que una
familia: dentro hay parejas al 44 % y parejas que apenas se rozan.

Uso: familias.py [umbral] > datos/familias.json
"""
import json
import os
import sys
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")

UMBRAL = 5.0
BANDA = (2, 3, 4, 5, 6, 8, 10)     # el barrido que justifica el umbral


def agrupa(claves, parejas, umbral):
    padre = {k: k for k in claves}

    def raiz(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    aristas = 0
    for x in parejas:
        if min(x["porcentaje_de_a"], x["porcentaje_de_b"]) >= umbral:
            ra, rb = raiz(x["a"]), raiz(x["b"])
            if ra != rb:
                padre[ra] = rb
            aristas += 1
    g = defaultdict(list)
    for k in claves:
        g[raiz(k)].append(k)
    return sorted((sorted(v) for v in g.values()), key=lambda v: (-len(v), v[0])), aristas


def main():
    umbral = float(sys.argv[1]) if len(sys.argv) > 1 else UMBRAL
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    with open(os.path.join(DATOS, "normalizado.json"), encoding="utf-8") as f:
        d = json.load(f)
    # El ano sale del registro, para poder decir con datos si el reparto va por
    # ano o no. La serie tenia apuntado que no; aqui se comprueba.
    with open(os.path.join(DATOS, "serie.json"), encoding="utf-8") as f:
        anios = {p["clave"]: p["anio"] for p in json.load(f)["proyectos"]}
    kon = {c["clave"] for c in d["cartuchos"] if c["grupo"] == "konami"}
    par = [x for x in d["parejas"] if x["a"] in kon and x["b"] in kon]

    barrido = []
    for n in BANDA:
        gs, aristas = agrupa(kon, par, n)
        barrido.append({"umbral": n, "aristas": aristas,
                        "tamanos": [len(g) for g in gs]})

    grupos, aristas = agrupa(kon, par, umbral)
    salida = []
    for g in grupos:
        if len(g) == 1:
            continue
        dentro = [x for x in par if x["a"] in g and x["b"] in g
                  and min(x["porcentaje_de_a"], x["porcentaje_de_b"]) >= umbral]
        dentro.sort(key=lambda x: -min(x["porcentaje_de_a"], x["porcentaje_de_b"]))
        salida.append({
            "cartuchos": g,
            "cuantos": len(g),
            "anios": sorted({anios[k] for k in g if anios.get(k)}),
            "la_pareja_mas_estrecha": (
                {"a": dentro[0]["a"], "b": dentro[0]["b"],
                 "porcentaje_de_a": dentro[0]["porcentaje_de_a"],
                 "porcentaje_de_b": dentro[0]["porcentaje_de_b"]}
                if dentro else None),
            "parejas_por_encima_del_umbral": len(dentro),
        })
    sueltos = [g[0] for g in grupos if len(g) == 1]

    print("umbral %.0f%%: %d familias y %d sueltos"
          % (umbral, len(salida), len(sueltos)), file=sys.stderr)
    json.dump({"umbral": umbral, "cartuchos_konami": len(kon),
               "barrido_que_justifica_el_umbral": barrido,
               "familias": salida, "sueltos": sueltos},
              sys.stdout, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
