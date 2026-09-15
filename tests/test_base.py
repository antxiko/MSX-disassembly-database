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


class LaMarcaDeKonami(unittest.TestCase):
    """La marca oculta: el numero de catalogo y el titulo en katakana que
    Konami escondio en muchos de sus cartuchos. El hallazgo es de Manuel Pazos
    (@ManuelPazosMSX), septiembre de 2021."""

    @classmethod
    def setUpClass(cls):
        cls.proyectos = carga("serie.json")["proyectos"]
        cls.con = [p for p in cls.proyectos if p.get("marca_konami")]

    def test_el_rc_de_la_marca_es_el_que_publica_la_ficha(self):
        """El numero que Konami escondio en el binario contra el que la serie
        publica. Son dos caminos independientes hasta el mismo dato."""
        import re
        mal = []
        for p in self.con:
            ficha = re.search(r"RC-\d+", p.get("meta_es") or "")
            if not ficha or ficha.group(0) != p["marca_konami"]["rc"]:
                mal.append((p["clave"], p["marca_konami"]["rc"],
                            ficha.group(0) if ficha else None))
        self.assertEqual(mal, [])
        self.assertGreaterEqual(len(self.con), 17)

    def test_solo_los_konami_llevan_marca(self):
        """El control del rastreador: si le encontrara marca a un juego que no
        es de Konami, es que se traga coincidencias."""
        intrusos = [p["clave"] for p in self.con if p.get("grupo") != "konami"]
        self.assertEqual(intrusos, [])

    def test_hay_konami_sin_marca_y_eso_no_es_un_fallo(self):
        """No la llevan todos: Time Pilot, Frogger o Athletic Land no la tienen,
        y esa ausencia es un dato de la serie, no un error de medida."""
        sin = [p["clave"] for p in self.proyectos
               if p.get("grupo") == "konami" and p.get("marca_konami") is False]
        self.assertIn("timepilot", sin)
        self.assertIn("athletic", sin)


class LosCreditos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proyectos = carga("serie.json")["proyectos"]

    def test_ningun_credito_es_el_nombre_del_volcado(self):
        """"Colt 36 (1987)(Topo Soft)(ES)[!]" lo escribio quien preservo la
        cinta, no el juego. No puede colarse entre los creditos."""
        import recoge_creditos
        colados = []
        for p in self.proyectos:
            for c in (p.get("creditos") or []):
                if recoge_creditos.VOLCADO.search(c["texto"]):
                    colados.append((p["clave"], c["texto"][:50]))
        self.assertEqual(colados, [])

    def test_las_cintas_de_topo_tienen_su_volcado_apartado(self):
        """Y que el apartado no se pierda: los cuatro Topo y los dos War."""
        con = [p["clave"] for p in self.proyectos if p.get("metadatos_del_volcado")]
        for clave in ("colt36", "stardust", "temptations", "alehop", "war"):
            self.assertIn(clave, con)

    def test_las_citas_salen_del_binario_tal_cual(self):
        """Cada cita tiene que estar, byte a byte, en el fichero que dice y en
        el desplazamiento que dice. Es lo que separa una cita de un recuerdo."""
        mirados = 0
        for p in self.proyectos:
            # De que fichero salieron: lo dice la propia base. No vale
            # suponer que es `binario`, porque un proyecto con varios no tiene
            # binario unico y ahi la cita se quedaba sin poder releerse.
            origen = p.get("creditos_del_fichero") or (
                p["binario"]["fichero"] if p.get("binario") else None)
            for c in (p.get("creditos") or []) + (p.get("metadatos_del_volcado") or []):
                self.assertIsNotNone(origen, "%s cita sin decir de donde" % p["clave"])
                ruta = os.path.join(DES_ASM, origen)
                with open(ruta, "rb") as f:
                    datos = f.read()
                off = int(c["offset"], 16)
                trozo = datos[off:off + len(c["texto"]) + 2]
                self.assertIn(c["texto"].encode("ascii"), trozo,
                              "%s %s" % (p["clave"], c["offset"]))
                mirados += 1
        self.assertGreater(mirados, 30)


class LoQueComparten(unittest.TestCase):
    """La matriz de bytes identicos entre binarios, y las rutinas que salen."""

    @classmethod
    def setUpClass(cls):
        cls.comun = carga("comun.json")
        cls.trozos = carga("rutinas_comunes.json")["trozos"]
        cls.base = {p["clave"]: p for p in carga("serie.json")["proyectos"]}

    def test_los_trozos_estan_de_verdad_donde_dicen(self):
        """Cada aparicion se relee del binario: mismos bytes, mismo sitio."""
        mirados = 0
        for t in self.trozos:
            patron = bytes(int(x, 16) for x in t["primeros_bytes"].split())
            for a in t["apariciones"]:
                ruta = os.path.join(DES_ASM,
                                    self.base[a["juego"]]["binario"]["fichero"])
                with open(ruta, "rb") as f:
                    f.seek(int(a["offset"], 16))
                    self.assertEqual(f.read(len(patron)), patron,
                                     "%s %s" % (a["juego"], a["offset"]))
                mirados += 1
        self.assertGreater(mirados, 50)

    def test_la_lectura_de_mandos_esta_en_muchos_y_es_la_del_bios(self):
        """El trozo mas repartido son 36 bytes en tres docenas largas de
        cartuchos, y empieza con la llamada 0x0141 del BIOS (SNSMAT), que es
        leer una fila del teclado. Si eso cambia, es que ya no es esa rutina."""
        t = max(self.trozos, key=lambda x: x["cartuchos"])
        self.assertGreaterEqual(t["cartuchos"], 16)
        b = t["primeros_bytes"].split()
        self.assertEqual(b[:5], ["3E", "07", "CD", "41", "01"])  # ld a,7; call 0141h

    def test_una_misma_rutina_lleva_nombres_distintos_por_la_serie(self):
        """El hallazgo que justifica esta capa: la serie lleva meses bautizando
        la misma rutina de maneras distintas en cada repositorio."""
        t = max(self.trozos, key=lambda x: x["cartuchos"])
        self.assertGreater(len(t["como_lo_llaman"]), 5)

    def test_las_parejas_del_mismo_binario_estan_marcadas(self):
        """Un parche que desensambla el cartucho original comparte el fichero
        entero con el. Eso no es reuso de codigo y no puede contar como tal."""
        for x in self.comun["parejas"]:
            a, b = self.base[x["a"]]["binario"], self.base[x["b"]]["binario"]
            self.assertEqual(x["mismo_binario"], a["sha256"] == b["sha256"],
                             "%s / %s" % (x["a"], x["b"]))

    def test_la_tipografia_no_cuenta_como_codigo(self):
        """Los 46 bytes que estan en mas cartuchos que ningun otro trozo son la
        fuente -3E 63 03 0E 03 63 3E dibuja un '3'-, y ningun listado los tiene
        como instruccion. Si salieran como codigo, la matriz estaria mintiendo
        sobre que comparten estos cartuchos."""
        fuente = bytes([0x3E, 0x63, 0x03, 0x0E, 0x03, 0x63, 0x3E])
        for t in self.trozos:
            patron = bytes(int(x, 16) for x in t["primeros_bytes"].split())
            self.assertNotIn(fuente, patron)


class LasFamilias(unittest.TestCase):
    """La comparacion normalizada: la que ve una rutina compartida aunque este
    en otra direccion, y el agrupamiento que sale de ella."""

    @classmethod
    def setUpClass(cls):
        cls.norm = carga("normalizado.json")
        cls.fam = carga("familias.json")
        cls.crudo = carga("comun.json")

    def test_la_normalizada_ve_lo_que_la_de_bytes_no_ve(self):
        """La razon de ser de esta capa, comprobada en un caso concreto: Super
        Cobra y Yie Ar Kung-Fu comparten mas de doscientas instrucciones y la
        matriz de bytes solo les encontraba treinta y nueve, porque la misma
        rutina esta ensamblada en otra direccion."""
        par = {(x["a"], x["b"]): x for x in self.norm["parejas"]}
        x = par.get(("supercobra", "yiearkungfu")) or par.get(("yiearkungfu", "supercobra"))
        self.assertIsNotNone(x)
        self.assertGreater(x["instrucciones_comunes"], 150)
        crudo = [c for c in self.crudo["parejas"]
                 if {c["a"], c["b"]} == {"supercobra", "yiearkungfu"}]
        self.assertTrue(crudo)
        self.assertLess(crudo[0]["bytes_comunes"], 100)

    def test_las_familias_pequenas_aguantan_todo_el_barrido(self):
        """Lo que separa una familia de un artefacto del umbral: el grupo de
        cinco y el de dos son los mismos del 4 % al 8 %, mientras la familia
        grande se va deshaciendo."""
        b = {x["umbral"]: x["tamanos"] for x in
             self.fam["barrido_que_justifica_el_umbral"]}
        for n in (4, 5, 6):
            self.assertIn(5, b[n], "al %d %% no hay grupo de cinco" % n)
            self.assertIn(2, b[n], "al %d %% no hay grupo de dos" % n)
        # y la grande si se deshace: al 8 % ya no queda ningun grupo de 15+
        self.assertTrue(all(t < 15 for t in b[8]))

    def test_el_reparto_no_va_por_ano(self):
        """La serie lo tenia apuntado; aqui se comprueba. Si fuera por ano, las
        familias no se solaparian en el tiempo, y se solapan."""
        rangos = [(min(f["anios"]), max(f["anios"])) for f in self.fam["familias"]
                  if f["anios"]]
        self.assertGreaterEqual(len(rangos), 2)
        solapan = any(a1 <= b2 and a2 >= b1
                      for i, (a1, a2) in enumerate(rangos)
                      for (b1, b2) in rangos[i + 1:])
        self.assertTrue(solapan)

    def test_los_dos_cartuchos_mas_parecidos_son_los_hyper_olympic(self):
        mayor = max(self.norm["parejas"],
                    key=lambda x: min(x["porcentaje_de_a"], x["porcentaje_de_b"]))
        self.assertEqual({mayor["a"], mayor["b"]},
                         {"hyperolympic1", "hyperolympic2"})
        self.assertGreater(min(mayor["porcentaje_de_a"],
                               mayor["porcentaje_de_b"]), 50)

    def test_los_que_se_quedan_fuera_dicen_por_que(self):
        """Doce no se pueden medir asi -las cintas y las MegaROM no declaran un
        ORG unico-. Eso se declara, no se disimula."""
        self.assertTrue(self.norm["fuera"])
        for x in self.norm["fuera"]:
            self.assertTrue(x["por"])
        claves = {x["clave"] for x in self.norm["fuera"]}
        for esperado in ("nemesis", "f1spirit", "stardust"):
            self.assertIn(esperado, claves)

    def test_cada_familia_sale_de_parejas_que_existen(self):
        medidos = {c["clave"] for c in self.norm["cartuchos"]}
        for f in self.fam["familias"]:
            for k in f["cartuchos"]:
                self.assertIn(k, medidos)


class LaWeb(unittest.TestCase):
    """La web se genera de los datos, y estas comprobaciones lo atan.

    El defecto que esta base encontro en cuatro fichas de la portada es
    exactamente este: una cifra escrita a mano el dia de publicar, que se queda
    vieja cuando el listado sigue creciendo. Aqui no puede pasar, y se comprueba.
    """

    @classmethod
    def setUpClass(cls):
        cls.docs = os.path.join(RAIZ, "docs")
        cls.base = carga("serie.json")

    def lee(self, rel):
        with open(os.path.join(self.docs, rel), encoding="utf-8") as f:
            return f.read()

    def test_estan_las_doce_paginas(self):
        import make_web
        for nes, nen in make_web.PAGINAS:
            self.assertTrue(os.path.isfile(os.path.join(self.docs, nen + ".html")),
                            nen)
            self.assertTrue(os.path.isfile(os.path.join(self.docs, "es",
                                                        nes + ".html")), nes)

    def test_la_portada_publica_los_totales_que_hoy_se_miden(self):
        # Solo los desensamblados: los dos parches desensamblan el mismo
        # binario que su juego base, asi que sumarlos contaria dos veces las
        # 9.755 instrucciones de Soccer o las 6.844 de War in Middle Earth.
        con = [p for p in self.base["proyectos"]
               if p.get("cifras") and p["categoria"] == "desensamblado"]
        i = sum(p["cifras"]["instrucciones"] for p in con)
        c = sum(p["cifras"]["comentarios"] for p in con)
        es = self.lee(os.path.join("es", "index.html"))
        self.assertIn("{:,}".format(i).replace(",", "."), es)
        self.assertIn("{:,}".format(c).replace(",", "."), es)
        en = self.lee("index.html")
        self.assertIn("{:,}".format(i), en)

    def test_la_tabla_lleva_todos_los_desensamblados(self):
        """Todos los que haya en la base, no un numero clavado.

        Antes aqui habia un `assertEqual(len(des), 47)`, y lo unico que hizo
        fue ponerse en rojo el dia que entro el desensamblado numero cuarenta
        y ocho. Lo que importa no es cuantos son sino que no falte ninguno, y
        eso lo comprueba el bucle de abajo. La cota es solo para que la prueba
        no pase en verde con la base vacia.
        """
        es = self.lee(os.path.join("es", "LOS-JUEGOS.html"))
        des = [p for p in self.base["proyectos"]
               if p["categoria"] == "desensamblado"]
        self.assertGreaterEqual(len(des), 40)
        for p in des:
            self.assertIn(p["titulo"].split(" — ")[0][:14], es, p["clave"])

    def test_se_cita_a_manuel_pazos_en_los_dos_idiomas(self):
        """La marca oculta es hallazgo suyo y hay que decirlo siempre."""
        self.assertIn("Manuel Pazos", self.lee("THE-MARK.html"))
        self.assertIn("Manuel Pazos", self.lee(os.path.join("es", "LA-MARCA.html")))

    def test_las_dos_lenguas_tienen_las_mismas_paginas(self):
        import make_web
        self.assertEqual(len(make_web.PAGINAS), len(make_web.TITULOS["es"]))
        self.assertEqual(len(make_web.TITULOS["es"]), len(make_web.TITULOS["en"]))


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


class LasProtecciones(unittest.TestCase):
    """Las escrituras que un cartucho hace a su PROPIO espacio.

    El patron lo identifico Manuel Pazos en el RC-727. Aqui no se comprueba
    que "funcionen" -eso pediria correr una copia en RAM, y no se distribuye
    ningun binario-, sino que cada escritura registrada este de verdad en el
    listado que dice, en la direccion que dice.
    """

    @classmethod
    def setUpClass(cls):
        cls.base = carga("serie.json")["proyectos"]

    def test_cada_escritura_esta_en_su_listado(self):
        import re
        mirados = 0
        for p in self.base:
            for e in p.get("protecciones") or []:
                ruta = os.path.join(DES_ASM, p["directorio"], e["listado"])
                if not os.path.exists(ruta):
                    continue
                dire = e["donde"][2:].lower()
                with open(ruta, encoding="utf-8", errors="replace") as f:
                    texto = f.read()
                self.assertRegex(
                    texto, r"(?m)^\t%s\s*;%s\b" % (re.escape(e["instruccion"]), dire),
                    "%s: %s no esta en %s" % (p["clave"], e["donde"], e["listado"]))
                mirados += 1
        if not mirados:
            self.skipTest("no hay listados al lado")
        self.assertGreater(mirados, 15)

    def test_el_destino_cae_dentro_del_propio_listado(self):
        """Si el destino no estuviera en el cartucho no seria una trampa."""
        for p in self.base:
            for e in p.get("protecciones") or []:
                self.assertIsNotNone(e["cae_en"], "%s %s" % (p["clave"], e["donde"]))
                self.assertLessEqual(int(e["cae_en"], 16), int(e["destino"], 16))

    def test_las_cintas_quedan_fuera(self):
        """En una cinta escribir en su propio espacio es lo normal, no una trampa."""
        cintas = [p for p in self.base if p.get("protecciones_nota")]
        self.assertGreater(len(cintas), 3)
        for p in cintas:
            self.assertIsNone(p.get("protecciones"), p["clave"])

    def test_la_pagina_cita_a_manuel_pazos(self):
        for f in ("THE-PROTECTIONS.html", os.path.join("es", "LAS-PROTECCIONES.html")):
            ruta = os.path.join(RAIZ, "docs", f)
            with open(ruta, encoding="utf-8") as fh:
                self.assertIn("Manuel Pazos", fh.read(), f)
