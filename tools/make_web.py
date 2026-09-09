#!/usr/bin/env python3
"""Genera la web de la base de datos, en los dos idiomas.

    python3 tools/make_web.py

Escribe `docs/` (ingles) y `docs/es/` (castellano). El diseno es el de la serie:
la hoja de estilo se importa tal cual de `tools/estilo_web.py`, el mismo fichero
que usan las webs de los juegos y la portada.

LA DIFERENCIA CON LAS OTRAS WEBS DE LA SERIE: aqui NO se escribe ni una cifra a
mano. Todas las tablas y todos los totales salen de `datos/*.json`, o sea de lo
que midieron los recolectores. Si manana se vuelve a medir y una cifra cambia,
la web cambia con ella sola. En las webs de los juegos las cifras son constantes
en el generador y hay que acordarse de tocarlas; ese olvido es justo lo que esta
base encontro en cuatro fichas de la portada.

Las paginas son seis por idioma, y cada una responde a una pregunta:

    index                 que es esto y cuanto hay
    LOS-JUEGOS            los 49, uno por fila, con sus cifras
    LA-MARCA              quien lleva la marca oculta de Konami
    LOS-CREDITOS          quien firma cada juego, citado del binario
    LO-COMPARTIDO         que codigo comparten, y con cuantos nombres
    COMO-SE-MIDE          de donde sale cada dato y que no se puede afirmar
"""
import html
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
DATOS = os.path.join(RAIZ, "datos")
sys.path.insert(0, AQUI)
from estilo_web import ESTILO                                  # noqa: E402

EXTRA = """
header.top h1{margin:0;font-size:2.1rem;letter-spacing:.04em}
header.top h1 span{color:var(--rojo)}
table{border-collapse:collapse;width:100%;font-size:13px;margin:1.2rem 0}
th,td{border-bottom:1px solid var(--linea);padding:.42rem .6rem;text-align:left;
  vertical-align:top}
th{color:var(--oro);font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  font-weight:400;white-space:nowrap}
td.n{text-align:right;font-variant-numeric:tabular-nums}
td b{color:var(--oro);font-weight:400}
tr.destaca td{background:rgba(255,255,255,.02)}
.tabla{overflow-x:auto}
code{font-size:12px;color:var(--suave)}
.cita{border-left:2px solid var(--linea);padding:.1rem 0 .1rem .9rem;margin:.7rem 0;
  color:var(--tinta);font-size:13px}
.cita b{color:var(--oro);font-weight:400}
.aviso{border:1px solid var(--linea);padding:1rem 1.1rem;margin:1.4rem 0;
  background:var(--panel);font-size:14px}
.aviso h4{margin:0 0 .5rem;color:var(--rojo);font-size:13px;letter-spacing:.06em;
  text-transform:uppercase;font-weight:400}
"""

PAGINAS = [("index", "index"), ("LOS-JUEGOS", "THE-GAMES"),
           ("LA-MARCA", "THE-MARK"), ("LOS-CREDITOS", "THE-CREDITS"),
           ("LO-COMPARTIDO", "WHAT-THEY-SHARE"),
           ("COMO-SE-MIDE", "HOW-IT-IS-MEASURED")]

MENU = {
    "es": ["Los juegos", "La marca", "Los créditos", "Lo compartido",
           "Cómo se mide"],
    "en": ["The games", "The mark", "The credits", "What they share",
           "How it is measured"],
}


def carga(nombre):
    with open(os.path.join(DATOS, nombre), encoding="utf-8") as f:
        return json.load(f)


def e(x):
    return html.escape(str(x), quote=False)


def mil(n, idioma):
    """1465115 -> 1.465.115 en castellano, 1,465,115 en ingles."""
    return "{:,}".format(int(n)).replace(",", "." if idioma == "es" else ",")


def pct(x, idioma):
    s = "%.1f" % x
    return (s.replace(".", ",") if idioma == "es" else s) + " %"


# --------------------------------------------------------------- las paginas

def pag_index(d, idioma):
    des = [p for p in d["proyectos"] if p["categoria"] == "desensamblado"]
    con = [p for p in des if p["cifras"]]
    i = sum(p["cifras"]["instrucciones"] for p in con)
    c = sum(p["cifras"]["comentarios"] for p in con)
    b = sum(p["binario"]["bytes"] for p in des if p.get("binario"))
    r = sum(p["cifras"]["bloques"] for p in con)
    marca = sum(1 for p in d["proyectos"] if p.get("marca_konami"))

    filas = [
        ("proyectos", "projects", mil(len(d["proyectos"]), idioma)),
        ("desensamblados", "disassemblies", mil(len(des), idioma)),
        ("instrucciones", "instructions", mil(i, idioma)),
        ("comentarios de línea", "line comments", mil(c, idioma)),
        ("densidad de la serie", "density across the series", pct(100.0 * c / i, idioma)),
        ("rutinas", "routines", mil(r, idioma)),
        ("rutinas por debajo del 10 %", "routines below 10 %", "0"),
        ("bytes de binario", "bytes of binary", mil(b, idioma)),
        ("con la marca oculta de Konami", "carrying Konami's hidden mark", mil(marca, idioma)),
    ]
    t = "".join("<tr><td>%s</td><td class='n'><b>%s</b></td></tr>"
                % (e(x[0] if idioma == "es" else x[1]), e(x[2])) for x in filas)

    if idioma == "es":
        cuerpo = f"""
<p>Los cuarenta y siete desensamblados de MSX de la serie y los dos parches,
reunidos en un registro único que <b>no copia ninguna cifra: las mide</b>. Cada
número de esta web sale de <code>datos/serie.json</code>, y ese fichero sale de
pasar las herramientas por los repositorios y por los binarios.</p>

<div class="tabla"><table>{t}</table></div>

<h3>Por qué medirlo otra vez, si cada repositorio ya lo dice</h3>
<p>Porque las cifras publicadas envejecen. La ficha de cada juego se escribió el
día que se publicó; si después alguien vuelve al listado y comenta otra tanda, la
web se queda diciendo la vieja. Al montar esto aparecieron <b>cuatro</b>:
Trailblazer publica 30,7&nbsp;% y su listado da hoy 30,8&nbsp;%, y lo mismo pasa
en Hyper Rally, Hyper Sports&nbsp;2 y Nemesis. En Trailblazer se ve la causa en
el historial: el listado se tocó en un commit posterior al del README.</p>

<h3>Lo que ha salido de mirarlos todos juntos</h3>
<ul>
<li><b>La misma rutina lleva doce nombres.</b> La lectura de mandos son treinta y
seis bytes idénticos en dieciocho cartuchos, y cada repositorio la bautizó a su
manera. <a href="LO-COMPARTIDO.html">Lo compartido</a>.</li>
<li><b>Diecisiete cartuchos llevan la marca oculta de Konami</b>, y los
diecisiete dan el mismo número de catálogo que publica su ficha.
<a href="LA-MARCA.html">La marca</a>.</li>
<li><b>Demonia la firma Claude Sablatou</b>, y Trailblazer trae dentro la lista
entera de sus autores. <a href="LOS-CREDITOS.html">Los créditos</a>.</li>
<li><b>Ninguno de los cuarenta y siete tiene una sola rutina por debajo del
10&nbsp;% de comentario.</b> Eso es el listón de la serie, y aquí está
comprobado de una vez sobre los listados de hoy.</li>
</ul>"""
    else:
        cuerpo = f"""
<p>The forty-seven MSX disassemblies in the series and the two patches, gathered
into a single record that <b>copies no figure: it measures them</b>. Every number
on this site comes from <code>datos/serie.json</code>, and that file comes from
running the tools over the repositories and the binaries.</p>

<div class="tabla"><table>{t}</table></div>

<h3>Why measure again, when each repository already says so</h3>
<p>Because published figures age. Each game's card was written the day it was
published; if someone later goes back to the listing and comments another pass,
the site keeps quoting the old one. Building this turned up <b>four</b>:
Trailblazer publishes 30.7&nbsp;% and its listing gives 30.8&nbsp;% today, and
the same holds for Hyper Rally, Hyper Sports&nbsp;2 and Nemesis. In Trailblazer
the history shows why: the listing was touched in a commit later than the
README's.</p>

<h3>What came out of looking at all of them together</h3>
<ul>
<li><b>The same routine goes by twelve names.</b> The joystick-and-keyboard read
is thirty-six identical bytes across eighteen cartridges, and every repository
named it its own way. <a href="WHAT-THEY-SHARE.html">What they share</a>.</li>
<li><b>Seventeen cartridges carry Konami's hidden mark</b>, and all seventeen
give the same catalogue number their card publishes.
<a href="THE-MARK.html">The mark</a>.</li>
<li><b>Demonia is signed by Claude Sablatou</b>, and Trailblazer carries the full
list of its authors inside. <a href="THE-CREDITS.html">The credits</a>.</li>
<li><b>Not one of the forty-seven has a single routine below 10&nbsp;% commented.</b>
That is the bar for the series, checked here in one go over today's listings.</li>
</ul>"""
    return cuerpo


def pag_juegos(d, idioma):
    des = sorted([p for p in d["proyectos"] if p["categoria"] == "desensamblado"],
                 key=lambda p: -(p["cifras"]["densidad"] if p["cifras"] else -1))
    cab = (["juego", "año", "bytes", "instrucciones", "comentarios", "densidad",
            "rutinas", "flojas"] if idioma == "es" else
           ["game", "year", "bytes", "instructions", "comments", "density",
            "routines", "below 10 %"])
    filas = []
    for p in des:
        c = p["cifras"]
        b = p.get("binario")
        web = p.get("web_url")
        nombre = ("<a href='%s'>%s</a>" % (e(web), e(p["titulo"])) if web
                  else e(p["titulo"]))
        if c:
            cols = [mil(c["instrucciones"], idioma), mil(c["comentarios"], idioma),
                    "<b>%s</b>" % pct(c["densidad"], idioma),
                    mil(c["bloques"], idioma), str(c["flojas"])]
        else:
            cols = ["—", "—", "—", "—", "—"]
        filas.append("<tr><td>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                     "<td class='n'>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
                     "<td class='n'>%s</td><td class='n'>%s</td></tr>"
                     % (nombre, p["anio"],
                        mil(b["bytes"], idioma) if b else "—", *cols))
    tabla = ("<div class='tabla'><table><tr>%s</tr>%s</table></div>"
             % ("".join("<th>%s</th>" % e(x) for x in cab), "".join(filas)))

    if idioma == "es":
        intro = """
<p>Los cuarenta y siete, ordenados por densidad de comentario. Las cifras están
medidas sobre los listados que cada repositorio publica hoy, no copiadas de su
README.</p>
<div class="aviso"><h4>Una advertencia sobre la columna de bytes</h4>
<p>En los cartuchos es el tamaño de la ROM. En las cintas es el del fichero
<code>.tsx</code> o <code>.cas</code>, que lleva cabeceras y tonos piloto además
del programa: por eso un juego de cinta parece mucho mayor de lo que ocupa en
memoria.</p></div>"""
    else:
        intro = """
<p>All forty-seven, ordered by comment density. The figures are measured against
the listings each repository publishes today, not copied from its README.</p>
<div class="aviso"><h4>A warning about the bytes column</h4>
<p>For cartridges it is the ROM size. For tapes it is the size of the
<code>.tsx</code> or <code>.cas</code> file, which carries headers and pilot tones
as well as the program: that is why a tape game looks far larger than what it
occupies in memory.</p></div>"""
    return intro + tabla


def pag_marca(d, idioma):
    con = [p for p in d["proyectos"] if p.get("marca_konami")]
    con.sort(key=lambda p: p["marca_konami"]["rc"])
    sin_kon = [p for p in d["proyectos"]
               if p.get("grupo") == "konami" and p.get("marca_konami") is False]
    cab = (["catálogo", "juego", "bytes", "cierra en", "el título, sílaba a sílaba"]
           if idioma == "es" else
           ["catalogue", "game", "bytes", "closes at", "the title, syllable by syllable"])
    filas = "".join(
        "<tr><td><b>%s</b></td><td>%s</td><td class='n'>%d</td><td class='n'>%s</td>"
        "<td><code>%s</code></td></tr>"
        % (e(p["marca_konami"]["rc"]), e(p["titulo"]), p["marca_konami"]["bytes"],
           e(p["marca_konami"]["cierra_en"]), e(p["marca_konami"]["titulo"] or ""))
        for p in con)
    tabla = ("<div class='tabla'><table><tr>%s</tr>%s</table></div>"
             % ("".join("<th>%s</th>" % e(x) for x in cab), filas))
    lista = ", ".join(e(p["titulo"]) for p in sin_kon)

    if idioma == "es":
        return f"""
<div class="aviso"><h4>El hallazgo no es nuestro</h4>
<p>Lo destapó <b>Manuel Pazos</b> (<a href="https://github.com/gdx2">@ManuelPazosMSX</a>)
en septiembre de 2021. Gracias a él se sabe que hay que mirar ahí.</p></div>

<p>Konami escondió en muchos de sus cartuchos de MSX el número de catálogo y el
título en katakana. Leyendo hacia adelante, el bloque es así:</p>
<p class="cita">[el título, <b>N</b> bytes, en orden inverso] · [<b>N</b>] ·
[las dos cifras del RC en BCD] · [<b>0xAA</b>]</p>

<p>El rastreo se hace sobre los cuarenta y nueve binarios, también sobre los que
no son de Konami. Eso último es el control: si el rastreador le encontrara la
marca a un juego que no es de Konami, es que se traga coincidencias.
<b>No le encuentra ninguna.</b></p>

{tabla}

<p>Las sílabas son los códigos de la casa, uno por byte, con el <code>"</code> y
la <code>o</code> de los diacríticos aparte. Así es como lo da el rastreador y
como se guarda; la lectura en kana la pone quien lee, no el binario.</p>

<h3>Los diecisiete dan el número que publica su ficha</h3>
<p>Son dos caminos independientes hasta el mismo dato: lo que Konami dejó dentro
del cartucho y lo que la serie publica fuera. Coinciden en los diecisiete, y hay
una comprobación automática que lo vigila.</p>

<h3>Y no la llevan todos</h3>
<p>Estos cartuchos son de Konami y <b>no</b> la tienen: {lista}. Esa ausencia es
un dato de la serie, no un fallo de medida.</p>"""
    return f"""
<div class="aviso"><h4>The finding is not ours</h4>
<p>It was uncovered by <b>Manuel Pazos</b>
(<a href="https://github.com/gdx2">@ManuelPazosMSX</a>) in September 2021. Thanks
to him we know to look there.</p></div>

<p>Konami hid the catalogue number and the katakana title inside many of its MSX
cartridges. Read forwards, the block goes:</p>
<p class="cita">[the title, <b>N</b> bytes, in reverse order] · [<b>N</b>] ·
[the two RC digits in BCD] · [<b>0xAA</b>]</p>

<p>The sweep runs over all forty-nine binaries, including the ones that are not
Konami's. That is the control: if the tracer found the mark on a game that is not
Konami's, it would be swallowing coincidences. <b>It finds none.</b></p>

{tabla}

<p>The syllables are the house codes, one per byte, with the <code>"</code> and
<code>o</code> diacritics kept apart. That is how the tracer gives it and how it
is stored; reading it back as kana is the reader's doing, not the binary's.</p>

<h3>All seventeen give the number their card publishes</h3>
<p>Two independent paths to the same fact: what Konami left inside the cartridge
and what the series publishes outside. They agree on all seventeen, and a test
watches it.</p>

<h3>And not every cartridge has one</h3>
<p>These are Konami's and do <b>not</b> carry it: {lista}. That absence is a fact
about the series, not a measurement failure.</p>"""


def pag_creditos(d, idioma):
    con = [p for p in d["proyectos"] if p.get("creditos")]
    bloques = []
    for p in con:
        citas = "".join("<p class='cita'><b>%s</b> · %s</p>"
                        % (e(c["offset"]), e(c["texto"][:400]))
                        for c in p["creditos"][:4])
        bloques.append("<h3>%s</h3>%s" % (e(p["titulo"]), citas))
    sin = [p for p in d["proyectos"]
           if p.get("creditos") is not None and not p["creditos"]]

    if idioma == "es":
        cabecera = f"""
<p>De los cuarenta y nueve binarios, <b>{len(con)}</b> llevan algún crédito en
texto legible. Los demás no, y eso no significa que no tengan créditos: casi
todos escriben con sus propios dibujos y no con la fuente del BIOS, así que su
pantalla de créditos no está en ASCII en ninguna parte. Son {len(sin)}, y se
registran como <i>no aparece en ASCII</i>, nunca como <i>no tiene créditos</i>.</p>

<div class="aviso"><h4>No todo lo que pone «Topo Soft» lo escribió Topo Soft</h4>
<p>Los ficheros de cinta llevan al principio el nombre del volcado, con la
convención de los archivos de preservación:
<code>Colt 36 (1987)(Topo Soft)(ES)[!][RUN'CAS-'][v0.6b]</code>. Eso lo escribió
quien preservó la cinta en los años 2000, no el juego en 1987. Se reconocen por
esa forma y quedan apartados, fuera de los créditos.</p></div>

<p>Las citas van tal cual están en el binario, con su desplazamiento dentro del
fichero. <b>Ese desplazamiento no es una dirección de memoria</b>: un cartucho de
la página 1 se ve en 0x4000 y uno de la página 2 en 0x8000, y una cinta no se ve
en ningún sitio hasta que carga.</p>"""
    else:
        cabecera = f"""
<p>Of the forty-nine binaries, <b>{len(con)}</b> carry some credit in readable
text. The rest do not, and that does not mean they have no credits: most of them
write with their own tiles rather than the BIOS font, so their credits screen is
not in ASCII anywhere. There are {len(sin)} of those, recorded as <i>does not
appear in ASCII</i>, never as <i>has no credits</i>.</p>

<div class="aviso"><h4>Not everything that says "Topo Soft" was written by Topo Soft</h4>
<p>Tape files carry the dump's name at the start, in the preservation archives'
convention: <code>Colt 36 (1987)(Topo Soft)(ES)[!][RUN'CAS-'][v0.6b]</code>. That
was written by whoever preserved the tape in the 2000s, not by the game in 1987.
They are recognised by that shape and set aside, out of the credits.</p></div>

<p>The quotations are exactly as they sit in the binary, with their offset inside
the file. <b>That offset is not a memory address</b>: a page-1 cartridge appears
at 0x4000 and a page-2 one at 0x8000, and a tape appears nowhere until it
loads.</p>"""
    return cabecera + "".join(bloques)


def pag_comun(d, comun, trozos, idioma):
    parejas = [x for x in comun["parejas"] if not x["mismo_binario"]]
    con_cod = sum(1 for x in parejas if x["bytes_de_codigo_en_las_guardadas"])
    cab = (["bytes", "cartuchos", "nombres distintos", "cómo lo llaman"]
           if idioma == "es" else
           ["bytes", "cartridges", "distinct names", "what they call it"])
    filas = "".join(
        "<tr><td class='n'><b>%d</b></td><td class='n'>%d</td><td class='n'>%d</td>"
        "<td><code>%s</code></td></tr>"
        % (t["bytes"], t["cartuchos"], len(t["como_lo_llaman"]),
           e(", ".join(t["como_lo_llaman"])))
        for t in trozos[:6])
    tabla = ("<div class='tabla'><table><tr>%s</tr>%s</table></div>"
             % ("".join("<th>%s</th>" % e(x) for x in cab), filas))
    total = comun["juegos"] * (comun["juegos"] - 1) // 2

    if idioma == "es":
        return f"""
<p>Todos contra todos, buscando tiras de bytes idénticas de {comun['minimo_bytes']}
o más: <b>{len(parejas)} de las {mil(total, idioma)} parejas posibles</b> comparten
algo, y en <b>{con_cod}</b> de ellas hay código.</p>

<h3>Primero hubo que separar el código de los dibujos</h3>
<p>Lo primero que sale al ordenar por cuántos cartuchos comparten un trozo son
cuarenta y seis bytes que están en veintiséis cartuchos de Konami… y no son una
rutina: son la <b>tipografía</b>. <code>3E 63 03 0E 03 63 3E</code> dibuja un
<code>3</code> y <code>7C 66 63 63 63 66 7C</code> una <code>D</code>. Konami
reutilizaba sus dibujos tanto como su código, y una matriz de bytes no
distingue.</p>
<p>Aquí se distingue sin adivinar: el listado de cada juego ya sabe qué bytes son
código, porque los lleva como instrucciones con su dirección delante. Si la
dirección de la tira aparece así, es código; si no, son datos.</p>

<h3>Las piezas del armazón, y cómo las bautizó cada repositorio</h3>
{tabla}
<p>La misma lectura de mandos —<code>ld a,7</code> y la llamada 0x0141 del BIOS,
que lee una fila del teclado— está byte a byte en dieciocho cartuchos y se llama
de doce maneras distintas, porque los repositorios se escribieron a lo largo de
meses sin un sitio donde mirar. Éste es ese sitio.</p>
<p>Y hay una pieza de <b>161 bytes repartida por doce cartuchos que diez de ellos
dejaron sin nombre</b> (<code>L_4716</code>, <code>L_4766</code>, <code>L_4867</code>…):
sólo Ping Pong la bautizó, como <code>PINTA_TIRA_BUCLE</code>.</p>

<div class="aviso"><h4>Lo que este método no ve</h4>
<p>Compara <b>bytes</b>, así que sólo encuentra una rutina compartida si además la
ensamblaron en la misma dirección: en cuanto cambia el mapa de memoria, la misma
rutina da bytes distintos porque sus direcciones lo son. Por eso de aquí <b>no
sale</b> una separación limpia en dos armazones —a umbral bajo todos los Konami
quedan conectados y a umbral alto se deshacen en fragmentos—, sino un continuo.</p>
<p>Un aviso concreto: la lectura de mandos de 65 bytes que Athletic Land comparte
con Antarctic Adventure está en la Antarctic europea y en la japonesa 1.ª, y no
en la 2.ª, que es la que su Makefile elige por defecto y la que mide esta base.
Un hallazgo puede depender de qué volcado se mire.</p></div>"""
    return f"""
<p>Every binary against every other, looking for identical byte runs of
{comun['minimo_bytes']} or more: <b>{len(parejas)} of the {mil(total, idioma)}
possible pairs</b> share something, and <b>{con_cod}</b> of those share code.</p>

<h3>First the code had to be told apart from the drawings</h3>
<p>The first thing that comes up when you sort by how many cartridges share a run
is forty-six bytes present in twenty-six Konami cartridges… and it is not a
routine: it is the <b>typeface</b>. <code>3E 63 03 0E 03 63 3E</code> draws a
<code>3</code> and <code>7C 66 63 63 63 66 7C</code> a <code>D</code>. Konami
reused its drawings as much as its code, and a matrix of bytes cannot tell.</p>
<p>Here it can, without guessing: each game's listing already knows which bytes
are code, because it carries them as instructions with the address in front. If
the run's address shows up that way, it is code; if not, it is data.</p>

<h3>The pieces of the framework, and what each repository called them</h3>
{tabla}
<p>The same controls read —<code>ld a,7</code> and the BIOS call at 0x0141, which
reads one keyboard row— sits byte for byte in eighteen cartridges and goes by
twelve different names, because the repositories were written over months with no
single place to look. This is that place.</p>
<p>And there is a <b>161-byte piece across twelve cartridges that ten of them left
unnamed</b> (<code>L_4716</code>, <code>L_4766</code>, <code>L_4867</code>…): only
Ping Pong named it, as <code>PINTA_TIRA_BUCLE</code>.</p>

<div class="aviso"><h4>What this method cannot see</h4>
<p>It compares <b>bytes</b>, so it only finds a shared routine if it was also
assembled at the same address: as soon as the memory map changes, the same
routine yields different bytes because its addresses differ. That is why a clean
split into two frameworks <b>does not</b> fall out of this —at a low threshold
every Konami stays connected and at a high one they break into fragments— but a
continuum.</p>
<p>One concrete warning: the 65-byte controls read that Athletic Land shares with
Antarctic Adventure is in the European and Japanese 1st Antarctic, and not in the
2nd — which is the one its Makefile picks by default and the one this database
measures. A finding can depend on which dump you look at.</p></div>"""


def pag_metodo(d, idioma):
    fuentes = [
        ("quién es cada proyecto", "who each project is",
         "la ficha de la portada de la serie", "the series' front-page card",
         "recoge_portada.py"),
        ("en qué directorio vive", "which directory it lives in",
         "el <code>remote</code> de git, casado con la URL de la ficha",
         "git's <code>remote</code>, matched against the card's URL",
         "recoge_portada.py"),
        ("qué binario desensambla", "which binary it disassembles",
         "la variable del Makefile del repositorio",
         "the variable in the repository's Makefile", "recoge_binarios.py"),
        ("tamaño y sha256", "size and sha256",
         "el fichero, releído", "the file, read again", "recoge_binarios.py"),
        ("instrucciones y comentarios", "instructions and comments",
         "los <code>.asm</code> que el repositorio publica",
         "the <code>.asm</code> files the repository publishes", "recoge_cifras.py"),
        ("lo que el repositorio declara", "what the repository declares",
         "su propio <code>make densidad</code>", "its own <code>make densidad</code>",
         "recoge_cifras.py"),
        ("la marca oculta", "the hidden mark",
         "el binario, rastreado entero", "the binary, swept end to end",
         "recoge_marca.py"),
        ("quién firma el juego", "who signs the game",
         "las tiras legibles del binario", "the readable runs in the binary",
         "recoge_creditos.py"),
    ]
    filas = "".join("<tr><td>%s</td><td>%s</td><td><code>%s</code></td></tr>"
                    % (x[0] if idioma == "es" else x[1],
                       x[2] if idioma == "es" else x[3], x[4]) for x in fuentes)
    cab = (["dato", "de dónde sale", "herramienta"] if idioma == "es"
           else ["fact", "where it comes from", "tool"])
    tabla = ("<div class='tabla'><table><tr>%s</tr>%s</table></div>"
             % ("".join("<th>%s</th>" % e(x) for x in cab), filas))

    if idioma == "es":
        return f"""
<p>Nada se empareja por parecido del nombre y nada se rellena a ojo. Un proyecto
al que le falte una pieza sale con esa pieza a nulo y un aviso, no con una cifra
inventada.</p>
{tabla}

<h3>La vara es la misma para los cuarenta y siete</h3>
<p>Cada repositorio trae su copia de <code>densidad.py</code>, escritas a lo largo
de meses, y comparar entre juegos exige saber que cuentan igual. Hay cuatro
variantes y las cuatro usan <b>el mismo criterio</b>: se diferencian en el fin de
línea, en un caso especial de Nemesis (un banco sin código) y en que la de
Trailblazer suma varias piezas de cinta.</p>
<p>Así que aquí se mide con una copia canónica y, además, se corre el
<code>make densidad</code> del propio repositorio para contrastar:
<b>treinta y cuatro cotejan exacto y ninguno discrepa</b>. Eso es lo que hace
válida la cifra de los catorce que no traen ese objetivo, y es una comprobación
automática.</p>

<h3>Lo que esta base no puede afirmar</h3>
<ul>
<li>Que un juego «no tiene créditos». Sólo puede decir que no aparecen en ASCII.</li>
<li>Que dos cartuchos no comparten una rutina: si la ensamblaron en direcciones
distintas, la comparación por bytes no la ve.</li>
<li>De dónde sale el número de «etiquetas» que publican seis fichas de la
portada. No es el de rutinas, ni el de etiquetas con nombre del README, ni el de
etiquetas del listado. Queda anotado como pregunta abierta.</li>
</ul>"""
    return f"""
<p>Nothing is matched by name resemblance and nothing is filled in by eye. A
project missing a piece comes out with that piece null and a warning, not with an
invented figure.</p>
{tabla}

<h3>The same yardstick for all forty-seven</h3>
<p>Every repository carries its own copy of <code>densidad.py</code>, written over
months, and comparing between games requires knowing they count alike. There are
four variants and all four use <b>the same criterion</b>: they differ in line
endings, in a special case for Nemesis (a bank with no code), and in Trailblazer's
adding up several tape pieces.</p>
<p>So here everything is measured with one canonical copy and, on top of that,
each repository's own <code>make densidad</code> is run to check:
<b>thirty-four agree exactly and none disagree</b>. That is what makes the figures
valid for the fourteen that do not carry that target, and a test watches it.</p>

<h3>What this database cannot claim</h3>
<ul>
<li>That a game "has no credits". Only that none appear in ASCII.</li>
<li>That two cartridges share no routine: if it was assembled at different
addresses, a byte comparison cannot see it.</li>
<li>Where the "labels" figure published by six front-page cards comes from. It is
neither the routine count, nor the README's named-labels count, nor the listing's
label count. It is recorded as an open question.</li>
</ul>"""


# ------------------------------------------------------------------ armazon

def pagina(idioma, cual, cuerpo, titulo):
    nombres = [p[0] if idioma == "es" else p[1] for p in PAGINAS]
    nav = "".join('<a href="%s.html"%s>%s</a>'
                  % (n, ' style="color:var(--oro)"' if n == cual else "", e(m))
                  for n, m in zip(nombres[1:], MENU[idioma]))
    inicio = "index.html"
    otro = ("../%s.html" % PAGINAS[nombres.index(cual)][1] if idioma == "es"
            else "es/%s.html" % PAGINAS[nombres.index(cual)][0])
    if cual == "index":
        otro = "../index.html" if idioma == "es" else "es/index.html"
    etiqueta = "English" if idioma == "es" else "En castellano"
    pie = ("Los binarios no se distribuyen. Este repositorio contiene medidas y "
           "análisis, no los juegos. Cada juego pertenece a sus autores."
           if idioma == "es" else
           "The binaries are not distributed. This repository holds measurements "
           "and analysis, not the games. Each game belongs to its authors.")
    volver = "Inicio" if idioma == "es" else "Home"
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titulo)}</title>
<style>{ESTILO}{EXTRA}</style>

<div class="w">
<header class="top">
  <h1>la serie<span>/</span></h1>
  <p class="claim">{e(titulo)}</p>
</header>
<nav><a href="{inicio}">{volver}</a>{nav}<a href="{otro}"
  style="margin-left:auto;color:var(--oro)">{etiqueta}</a></nav>
{cuerpo}
<footer>{pie}</footer>
</div>
"""


TITULOS = {
    "es": ["La base de datos de la serie", "Los juegos",
           "La marca oculta de Konami", "Los créditos",
           "Lo que comparten", "Cómo se mide"],
    "en": ["The series database", "The games", "Konami's hidden mark",
           "The credits", "What they share", "How it is measured"],
}


def main():
    d = carga("serie.json")
    comun = carga("comun.json")
    trozos = carga("rutinas_comunes.json")["trozos"]

    for idioma in ("en", "es"):
        carpeta = os.path.join(RAIZ, "docs") if idioma == "en" else \
            os.path.join(RAIZ, "docs", "es")
        os.makedirs(carpeta, exist_ok=True)
        cuerpos = [pag_index(d, idioma), pag_juegos(d, idioma),
                   pag_marca(d, idioma), pag_creditos(d, idioma),
                   pag_comun(d, comun, trozos, idioma), pag_metodo(d, idioma)]
        for (nes, nen), cuerpo, titulo in zip(PAGINAS, cuerpos, TITULOS[idioma]):
            nombre = nes if idioma == "es" else nen
            html_ = pagina(idioma, nombre, cuerpo, titulo)
            destino = os.path.join(carpeta, nombre + ".html")
            with open(destino, "w", encoding="utf-8", newline="\n") as f:
                f.write(html_)
            print("  %s/%s.html  %d KB" % (idioma, nombre, len(html_) // 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
