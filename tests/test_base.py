#!/usr/bin/env python3
"""Comprobaciones sobre la base de datos de la serie.

Lo que se comprueba aqui NO es que los ficheros existan, sino que lo que dicen
se sostiene: que el binario que cada repositorio declara esta donde dice y tiene
el sha256 que dice, que la cifra medida coincide con la que da la herramienta
del propio repositorio, y que los lectores de texto no se inventan numeros.

Ese ultimo grupo hace falta porque el primer lector de README que se escribio
le saco a Demonia un 100 % de densidad de una frase suya sobre el debugger que
estaba doce lineas mas abajo. Un patron que cruza lineas no lee: adivina.
"""
import hashlib
import json
import os
import sys
import unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
DATOS = os.path.join(RAIZ, "datos")
DES_ASM = os.path.dirname(RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "tools"))


def carga(nombre):
    with open(os.path.join(DATOS, nombre), encoding="utf-8") as f:
        return json.load(f)


class LaBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = carga("serie.json")
        cls.proyectos = cls.base["proyectos"]

    def test_hay_un_registro_por_ficha_de_la_portada(self):
        """La base no puede tener mas ni menos proyectos que la portada."""
        sys.path.insert(0, os.path.join(DES_ASM, "ANTXIKO_GITHUB_IO", "tools"))
        import make_index
        esperados = len(make_index.DESENSAMBLADOS) + len(make_index.PARCHES)
        self.assertEqual(len(self.proyectos), esperados)

    def test_cada_proyecto_tiene_su_directorio_local(self):
        """Casados por el remote de git, no por parecido del nombre."""
        sin = [p["clave"] for p in self.proyectos if not p["directorio"]]
        self.assertEqual(sin, [])

    def test_las_claves_no_se_repiten(self):
        claves = [p["clave"] for p in self.proyectos]
        self.assertEqual(len(claves), len(set(claves)))

    def test_todo_binario_declarado_existe_y_tiene_su_sha(self):
        """El sha256 se vuelve a calcular; no se cree el que hay escrito."""
        mirados = 0
        for p in self.proyectos:
            for b in ([p["binario"]] if p.get("binario") else p.get("binarios", [])):
                ruta = os.path.join(DES_ASM, b["fichero"])
                self.assertTrue(os.path.isfile(ruta), b["fichero"])
                self.assertEqual(os.path.getsize(ruta), b["bytes"], b["fichero"])
                h = hashlib.sha256()
                with open(ruta, "rb") as f:
                    for trozo in iter(lambda: f.read(65536), b""):
                        h.update(trozo)
                self.assertEqual(h.hexdigest(), b["sha256"], b["fichero"])
                mirados += 1
        self.assertGreater(mirados, 40)

    def test_la_densidad_es_la_division_que_dice_ser(self):
        for p in self.proyectos:
            c = p.get("cifras")
            if not c:
                continue
            esperada = round(100.0 * c["comentarios"] / c["instrucciones"], 1)
            self.assertAlmostEqual(c["densidad"], esperada, places=1,
                                   msg=p["clave"])

    def test_la_vara_canonica_mide_como_la_del_propio_repositorio(self):
        """El cotejo que sostiene toda la base: donde el repositorio trae su
        `make densidad`, tiene que dar exactamente lo mismo que se mide aqui."""
        cotejados = [p for p in self.proyectos if p["coteja"] is not None]
        self.assertGreater(len(cotejados), 30)
        malos = [p["clave"] for p in cotejados if not p["coteja"]]
        self.assertEqual(malos, [])

    def test_ningun_desensamblado_tiene_rutinas_flojas(self):
        """El liston de la serie, comprobado sobre los listados de hoy."""
        con_flojas = [(p["clave"], p["cifras"]["flojas"]) for p in self.proyectos
                      if p.get("cifras") and p["cifras"]["flojas"]]
        self.assertEqual(con_flojas, [])

    def test_solo_3dgolf_se_queda_sin_cifras(self):
        """Es el unico escrito en MSX-BASIC: no tiene listado en ensamblador."""
        sin = sorted(p["clave"] for p in self.proyectos if not p.get("cifras"))
        self.assertEqual(sin, ["3dgolf"])


class LosLectoresDeTexto(unittest.TestCase):
    """Que no adivinen: sobre textos de formato conocido, cifra exacta o nada."""

    def setUp(self):
        import recoge_readme
        self.r = recoge_readme

    def test_lee_el_formato_tabulado(self):
        txt = ("    explicado             32.768 de 32.768   100 %\n"
               "    densidad de comentario 3.062 de 7.405    41,4 %\n"
               "    bloques por debajo del 10 %   0 de 1.000\n")
        self.assertEqual(self.r.busca(txt, self.r.PATRONES["densidad"]), 41.4)
        self.assertEqual(self.r.busca(txt, self.r.PATRONES["rutinas"]), 1000)
        self.assertEqual(self.r.busca(txt, self.r.PATRONES["flojas"]), 0)
        self.assertEqual(self.r.busca(txt, self.r.PATRONES["comentarios"]), 3062)

    def test_lee_la_tabla_de_markdown(self):
        txt = ("| rutinas | 200, **ninguna por debajo del 10 % comentada** |\n"
               "| densidad de comentarios | **50,2 %** |\n")
        self.assertEqual(self.r.busca(txt, self.r.PATRONES["densidad"]), 50.2)
        self.assertEqual(self.r.busca(txt, self.r.PATRONES["rutinas"]), 200)

    def test_no_cruza_lineas(self):
        """El fallo real de Demonia: un README SIN densidad, con un 100 % que
        habla de otra cosa unas lineas mas abajo. Tiene que devolver nada."""
        txt = ("# Demonia (MSX, 1986) - desensamblado comentado\n"
               "\n" * 10 +
               "  sobrevive el 100% del codigo original - ver debugger/\n")
        self.assertIsNone(self.r.busca(txt, self.r.PATRONES["densidad"]))

    def test_el_numero_se_lee_en_castellano(self):
        self.assertEqual(self.r.numero("32.768"), 32768)
        self.assertEqual(self.r.numero("41,4"), 41.4)
        self.assertEqual(self.r.numero("1.091"), 1091)


if __name__ == "__main__":
    unittest.main()
