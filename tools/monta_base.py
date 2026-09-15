#!/usr/bin/env python3
"""Une las tres recogidas en el registro unico de la serie.

Cada recolector mira una cosa y solo una:

    recoge_portada.py   quien es cada proyecto (lo que declara la portada)
    recoge_binarios.py  que binario desensambla de verdad (leido del Makefile)
    recoge_cifras.py    cuanto esta comentado (medido sobre los listados)
    recoge_marca.py     si lleva la marca oculta de Konami
    recoge_creditos.py  quien firma, en texto legible dentro del binario
    recoge_protecciones.py  las escrituras del cartucho a su propio espacio

Aqui se cruzan por el directorio local y sale `datos/serie.json`. Cada dato
lleva de donde sale, porque en esta serie el numero que se publica y el numero
que mide la herramienta no siempre han coincidido: la memoria de Twin Bee decia
24,6 % cuando su listado ya iba por el 41,4 %.

EL ORDEN IMPORTA, y es un punto fijo. Los dos ultimos recolectores necesitan
saber que binario mirar, y eso lo dice `serie.json`, que lo escribe este
programa. Asi que se monta una vez con lo que haya, se pasan esos dos y se
vuelve a montar. La segunda pasada da el mismo fichero que la tercera, porque de
`serie.json` solo leen la lista de binarios, que no cambia.

Un proyecto al que le falte una de las tres piezas sale igual, con esa pieza a
nulo y un aviso. No se rellena a ojo ni se descarta.

Uso: monta_base.py > datos/serie.json
"""
import datetime
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(os.path.dirname(AQUI), "datos")


def carga(nombre, si_falta=None):
    """Las recogidas de la capa 2 pueden no existir todavia."""
    ruta = os.path.join(DATOS, nombre)
    if si_falta is not None and not os.path.isfile(ruta):
        return si_falta
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def main():
    sys.stdout.reconfigure(encoding="utf-8", newline="\n")
    portada = carga("proyectos.json")
    binarios = {x["repo"]: x for x in carga("binarios.json")}
    cifras = {x["repo"]: x for x in carga("cifras.json")}
    marcas = {x["clave"]: x
              for x in carga("marcas.json", {"binarios": []})["binarios"]}
    creditos = {x["clave"]: x for x in carga("creditos.json", [])}
    protec = {x["clave"]: x for x in carga("protecciones.json", [])}

    salida, avisos = [], []
    for p in portada["proyectos"]:
        d = p["directorio"]
        reg = dict(p)
        del reg["aviso"]

        b = binarios.get(d) or {}
        hallados = b.get("binarios") or []
        if len(hallados) == 1:
            reg["binario"] = hallados[0]
        elif hallados:
            # Antarctic desensambla tres volcados; el Makefile los elige con
            # una variable. Se guardan todos y no se escoge uno.
            reg["binario"] = None
            reg["binarios"] = hallados
        else:
            reg["binario"] = None
            avisos.append("%s: sin binario localizado en su Makefile" % p["clave"])

        c = cifras.get(d) or {}
        reg["cifras"] = c.get("medido")
        reg["listados"] = c.get("listados", [])
        reg["cifras_del_repo"] = c.get("declarado")
        reg["coteja"] = c.get("coteja")
        if reg["cifras"] is None:
            avisos.append("%s: sin cifras (no publica listados en ensamblador)"
                          % p["clave"])
        if reg["coteja"] is False:
            avisos.append("%s: la cifra medida NO coincide con la del repo"
                          % p["clave"])

        # Capa 2: la firma de la casa y la firma de las personas.
        mk = marcas.get(p["clave"])
        reg["marca_konami"] = None
        if mk:
            reg["marca_konami"] = ({"rc": mk["rc"], "bytes": mk["bytes_titulo"],
                                    "cierra_en": mk["cierra_en"],
                                    "titulo": mk["titulo_en_kana"]}
                                   if mk["lleva_marca"] else False)
        cr = creditos.get(p["clave"])
        reg["creditos"] = cr["creditos"] if cr else None
        if cr and cr["metadatos_del_volcado"]:
            reg["metadatos_del_volcado"] = cr["metadatos_del_volcado"]
        # De QUE fichero salen esas citas. No siempre es `binario`: un proyecto
        # con varios -un parche, por ejemplo- no tiene binario unico, y sin
        # esto la cita se queda sin poder releerse, que es justo lo que la
        # separa de un recuerdo.
        if cr and cr.get("fichero"):
            reg["creditos_del_fichero"] = cr["fichero"]

        pr = protec.get(p["clave"])
        if pr is not None:
            reg["protecciones"] = (pr["escrituras"] if pr["es_cartucho"] else None)
            if not pr["es_cartucho"]:
                reg["protecciones_nota"] = pr["nota"]
            if pr.get("mapper"):
                reg["protecciones_mapper"] = pr["mapper"]

        reg["fuentes"] = {
            "identidad": "ANTXIKO_GITHUB_IO/tools/make_index.py",
            "binario": "el Makefile del repositorio",
            "cifras": "tools/densidad_canonica.py sobre git ls-files *.asm",
            "cifras_del_repo": "make densidad del repositorio, si tiene ese target",
            "marca_konami": "tools/marca_konami_canonica.py sobre el binario "
                            "(hallazgo de Manuel Pazos, 2021)",
            "creditos": "tiras ASCII del binario, filtradas por palabra clave",
            "creditos_del_fichero": "el binario concreto del que se leyeron",
            "protecciones": "tools/recoge_protecciones.py sobre el listado "
                            "(el patron lo identifico Manuel Pazos, RC-727)",
        }
        salida.append(reg)

    json.dump({"generado": datetime.date.today().isoformat(),
               "proyectos": salida,
               "sin_ficha_en_la_portada": portada["sin_ficha_en_la_portada"],
               "avisos": avisos},
              sys.stdout, indent=1, ensure_ascii=False)
    print("proyectos: %d | avisos: %d" % (len(salida), len(avisos)),
          file=sys.stderr)
    for a in avisos:
        print("  " + a, file=sys.stderr)


if __name__ == "__main__":
    main()
