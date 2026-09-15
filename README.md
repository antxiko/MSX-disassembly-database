# La base de datos de la serie de desensamblados MSX

Los cuarenta y ocho desensamblados y los dos parches de la serie, reunidos en
un registro único que **no copia ninguna cifra**: las mide.

    proyectos                 50   (48 desensamblados y 2 parches)
    instrucciones            256.997
    comentarios de línea      84.435        32,9 % del total
    rutinas                   31.916
    rutinas por debajo del 10 %    0        en toda la serie
    bytes de binario       1.497.883

Medido el 2026-09-15 sobre los listados que cada repositorio publica.

## Por qué se vuelve a medir todo

Porque las cifras publicadas envejecen. La ficha de cada juego en la portada se
escribió el día que se publicó; si después alguien vuelve al listado y comenta
otra tanda, la web sigue diciendo la vieja. Pasó de verdad, y esta base lo
encontró a la primera. El 2026-09-15 había **cinco** fichas desfasadas:

| juego | publicaba | medía |
|---|---|---|
| Hole in One | 41,9 % | 42,0 % |
| Hyper Rally | 22,1 % | 22,7 % |
| Hyper Sports 2 | 22,5 % | 22,7 % |
| Nemesis | 23,3 % | 23,4 % |
| Trailblazer | 30,7 % | 30,8 % |

En Trailblazer se veía la causa en el historial: el `.asm` se tocó en un commit
posterior al del README. Las cinco están **corregidas** en la ficha, en los
README y en la web de cada repositorio, y la portada tiene desde entonces una
comprobación que mide los listados y no deja publicar otra cifra.

Y no solo pasa en las webs: la memoria de trabajo de **Twin Bee** daba 24,6 %
cuando el listado ya iba por 41,4 %, porque se había escrito a mitad de la tanda
de comentarios.

## De dónde sale cada dato

| dato | fuente | herramienta |
|---|---|---|
| quién es cada proyecto | la ficha de la portada | `recoge_portada.py` |
| en qué directorio vive | el `remote` de git, casado con la URL de la ficha | `recoge_portada.py` |
| qué binario desensambla | la variable del Makefile del repositorio | `recoge_binarios.py` |
| tamaño y sha256 | el fichero, releído | `recoge_binarios.py` |
| instrucciones, comentarios, rutinas | los `.asm` que el repo publica (`git ls-files`) | `recoge_cifras.py` |
| lo que el repositorio declara | su propio `make densidad` | `recoge_cifras.py` |
| lo que el README dice | el README en castellano | `recoge_readme.py` |
| la marca oculta de Konami | el binario, rastreado entero | `recoge_marca.py` |
| quién firma el juego | las tiras legibles del binario | `recoge_creditos.py` |
| si el cartucho se defiende | las escrituras a su propio espacio, en el listado | `recoge_protecciones.py` |

Nada se empareja por parecido del nombre y nada se rellena a ojo: un proyecto al
que le falte una pieza sale con esa pieza a nulo y un aviso.

### La vara es la misma para los cuarenta y ocho

Cada repositorio trae su copia de `densidad.py`, escritas a lo largo de meses, y
comparar entre juegos exige saber que cuentan igual. Hay cuatro variantes, y las
cuatro usan **el mismo criterio**: se diferencian en el fin de línea, en un caso
especial de Nemesis (un banco sin código) y en que la de Trailblazer suma varias
piezas de cinta. Así que aquí se mide con una copia canónica, y además se corre
el `make densidad` del propio repositorio para contrastar:

**34 repositorios cotejan exacto y ninguno discrepa.** Eso es lo que hace válida
la cifra de los 14 que no traen ese target, y es un test (`test_base.py`).

## Un hallazgo, ya corregido: "etiquetas" no significaba lo mismo

La portada publicaba un número de "etiquetas" por juego, y eran tres magnitudes
distintas según el juego:

- las **rutinas** que cuenta `densidad.py` — Twin Bee, 1.000;
- las **directivas `L` del `.notes`**, que son las rutinas bautizadas a mano —
  Hyper Sports 2, 314, que tiene 500 rutinas;
- las **etiquetas del listado** — Mahjong, 1.091, que tiene 1.001 rutinas.

Y en siete fichas (Billiards, Yie Ar Kung-Fu II, Demonia, F-1 Spirit, Stardust,
Temptations y War in Middle Earth) la cifra no era ninguna de las tres: se
escribió el día de publicar y el listado la dejó atrás. Las más desviadas eran
Temptations, que publicaba 137 de sus 548 rutinas, y Stardust, 335 de 1.148.

**Corregido el 2026-09-15**: las cuarenta y cuatro fichas que dan esa cifra
publican ahora las **rutinas** que cuenta `densidad.py`, y la palabra en la
ficha es "rutinas", no "etiquetas". Es la magnitud que se mide igual en todos
los proyectos y la que sostiene el *"ninguna por debajo del 10 %"* que la propia
ficha publica al lado. Diecisiete fichas cambiaron de cifra.

Una de ellas se contradecía con su propio repositorio: la ficha de **Nemesis**
daba 916 rutinas —las directivas `L`— mientras el README del repositorio decía
*"ni una de las 1.540 rutinas está por debajo del 10 %"*.

Para que no vuelva a pasar, la portada tiene ahora dos comprobaciones
(`ANTXIKO_GITHUB_IO/tests/test_web.py`, clase `LasCifrasSonLasMedidas`) que
miden los `.asm` de cada repositorio y exigen que la ficha publique **esa**
cifra de rutinas y **ese** porcentaje de comentario. Si los repositorios no
están al lado, se saltan solas.

## La firma de la casa: la marca oculta de Konami

El hallazgo **no es nuestro**: lo destapó **Manuel Pazos** (@ManuelPazosMSX) en
septiembre de 2021. Konami escondió en muchos de sus cartuchos el número de
catálogo y el título en katakana, del revés y con el código de la casa. Aquí se
rastrea en los cincuenta y un binarios, también en los que no son de Konami:
**la llevan 17, y ninguno de los que no son de Konami da un falso positivo.**

    RC-701  Antarctic Adventure   KE tsu KI yo KU  NA N KI yo KU  TA " I HO " U KE N
    RC-724  Konami's Baseball     YA KI yu U
    RC-727  King's Valley         O U KE NO TA NI
    RC-731  Konami's Ping Pong    KO NA MI  NO  HI o N HO o N
    RC-735  Game Master           1 0  HA " I  TA NO SI MU  KA - TO RI tsu SI "
    RC-740  Twin Bee              TU I N HI " -
    ... y once más

Así, en sílabas, es como lo da el rastreador y como se guarda: son los códigos
de la casa, uno por byte, con el `"` y el `o` de los diacríticos aparte. Leídos
son ケッキョク ナンキョク ダイボウケン, ヤキュウ, オウケノタニ, コナミノピンポン,
10バイ タノシムカートリッジ y ツインビー — pero esa lectura la pone quien lee, no
el binario, y por eso va fuera de los datos.

**Los diecisiete dan el mismo número que publica su ficha.** Son dos caminos
independientes hasta el mismo dato —lo que Konami dejó dentro del binario y lo
que la serie publica fuera—, y es un test.

No la llevan todos: Time Pilot, Frogger, Super Cobra, Athletic Land, Monkey
Academy, Billiards, Mahjong, los dos Hyper Olympic, Sky Jaguar, Golf, Yie Ar
Kung-Fu, Tennis, Hyper Sports 1 y 2, Cabbage Patch y F-1 Spirit no la tienen. Esa
ausencia es un dato de la serie, no un fallo de medida.

## Los cartuchos que se defienden solos

Un cartucho que escribe **dentro de su propio espacio** no está haciendo nada:
la ROM no admite escritura, así que esa instrucción parece código muerto. No lo
es. Un cartucho pirateado es una copia cargada en **RAM**, y ahí la escritura sí
cuela y deja el juego roto en un sitio del que no se vuelve.

El patrón lo identificó **Manuel Pazos** en su desensamblado de King's Valley
(RC-727), donde llamó a las dos rutinas `ReadKeys_AC` y `VRAM_writeAC`. Aquí se
busca ese mismo patrón en los cuarenta cartuchos: **trece escriben en su propio
espacio, y los trece son de Konami**.

Y la familia repite siempre las mismas dos, en las mismas dos rutinas del
arranque:

- una deja un `pop hl` y un `ret` encima de un **`djnz`** de la cadena de
  presentación;
- la otra deja un cero en el **operando de un `jp`**, que en memoria lo
  convierte en `jp 00000h` —un reinicio en seco—.

Que el destino sea **siempre** un `djnz` o el operando de un salto, y nunca un
hueco de datos, es lo que descarta que sean escrituras sueltas.

**Uno más escribe en la ROM de la BIOS**, que tampoco admite escritura, y va
aparte porque ir a la BIOS no convierte una escritura en protección:
**Antarctic Adventure** copia `jp 0000h` encima de la entrada de la BIOS. Es un
guardián, y lo demuestra una cuarta compilación del juego idéntica salvo en dos
bytes: los que mandan esa misma copia a `DESPACHA`, dentro del cartucho.

Hubo un segundo, en Hyper Rally, y **no era una escritura**: dieciocho bytes de
datos -dos tablas de nueve a las que se llega por un puntero empujado a la pila,
no por un retorno- que el trazado había leído como código, y uno de ellos salía
como `ld (02f2fh),a`. Corregido en su listado, que sigue reensamblando byte a
byte. Es justo lo que esta sección no deja pasar sin explicar.

**Y lo que no la lleva también es un dato.** De Konami, veinte cartuchos no
escriben ni en su espacio ni en la BIOS. Ninguno de los seis que no son de
Konami lleva nada de esto, y ese es el control: si el rastreador se tragara
coincidencias, saldrían ahí.

**Las dos MegaROM se quedaron fuera la primera vez**, y por dos motivos. Su
ficha dice "MegaROM" y no "cartucho", así que se tomaron por cintas; y aun
metiéndolas, cada escritura se comprobaba contra el rango de su propio fichero,
que en un MegaROM es un solo banco. Ahora el espacio propio es la ventana entera,
`0x4000`–`0xBFFF`, descontando los registros del mapper, que se deducen de sus
propias escrituras. Nemesis escribe 78 veces en su mapper y F-1 Spirit 30 en el
suyo y en el SCC, y ninguna fuera.

Lo que esto **no** dice: qué pasa de verdad al correr una copia en RAM no está
medido —pediría cargar una copia y jugarla, y aquí no se distribuye ningún
binario—. Y no están todas: el rastreador ve las escrituras a dirección fija y
las que pasan por `HL` o `DE` cargados justo antes; una que calculase el destino
sobre la marcha se le escaparía.

## La firma de las personas: quién hizo cada juego

De los cincuenta y un binarios, **21 llevan algún crédito en texto legible**.
Los demás no: casi todos escriben con sus propios dibujos y no con la fuente del
BIOS, así que su pantalla de créditos no está en ASCII en ninguna parte. Eso se
registra como *no aparece en ASCII*, que es un dato, y nunca como *no tiene
créditos*, que sería inventar.

Lo que dicen, citado tal cual y con su posición:

- **Demonia** — `AUTEUR:CLAUDE SABLATOU` y `COPYRIGHT 1986 MICROIDS`, en 0x0AAF.
- **Trailblazer** — la lista entera: `written by SHAUN HOLLINGWORTH, COLIN
  DOOLEY, PETER HARRAP, CHRIS KERRY and GREG HOLMES`, con el original de
  `Shaun Southern on the Commodore`. En el mismo texto, los autores escriben
  `There may be a Cheat mode but I doubt it` — y en ese desensamblado ya estaba
  medido que al modo de trampas no se puede llegar.
- **Hole in One** — `HAL 1984 PRODUCED BY F>NAKAMURA`.
- **3D Golf Simulation** — `"Copyright 1983 By T&E SOFT"`.
- **Casio World Open** — `COPYRIGHT 1985 @ CASIO`.
- **War in Middle Earth** — `Programado por C.J.Pink. Conversión por ANIMAGIC`.
- **Colt 36** — `"TOPO0SOFTWARE"` y `"00MUSICA^GOMINOLAS"`.
- **Athletic Land** — `PROGRAM` y `SOUND`, las etiquetas de su pantalla de
  créditos; los nombres van en tiles y no en ASCII.

### No todo lo que pone "Topo Soft" lo escribió Topo Soft

Los ficheros de cinta llevan al principio el nombre del volcado, con la
convención de los archivos de preservación: `Colt 36 (1987)(Topo Soft)(ES)[!]
[RUN'CAS-'][v0.6b]`. Eso lo escribió quien preservó la cinta en los años 2000, no
el juego en 1987. Se reconocen por esa forma y quedan apartados en
`metadatos_del_volcado`, fuera de los créditos. Son seis.

## Qué comparten entre sí: 573 parejas, y la misma rutina con doce nombres

Todos contra todos, buscando tiras de bytes idénticas de 32 o más: **573 de las
1.176 parejas posibles comparten algo**, y en 304 de ellas hay código.

### Primero hubo que separar el código de los dibujos

Lo primero que sale al ordenar por cuántos cartuchos comparten un trozo son 46
bytes que están en **26 cartuchos de Konami**… y no son una rutina: son la
**tipografía**. `3E 63 03 0E 03 63 3E` dibuja un `3`, y `7C 66 63 63 63 66 7C`
una `D`. Konami reutilizaba sus dibujos tanto como su código, y una matriz de
bytes no distingue.

Aquí se distingue sin adivinar: el listado de cada juego ya sabe qué bytes son
código, porque los lleva como instrucciones con su dirección delante. Si la
dirección de la tira aparece así, es código; si no, son datos. Hay un test que
lo vigila, porque sin esa separación la matriz diría que estos cartuchos
comparten rutinas cuando lo que comparten son letras.

### Las piezas del armazón, y cómo las bautizó cada repositorio

| bytes | cartuchos | qué es | nombres distintos |
|---:|---:|---|---:|
| 36 | **18** | la lectura de mandos (`ld a,7` + `call 0x0141`, SNSMAT) | **12** |
| 161 | 12 | una rutina de pintado | 11, y **10 sin bautizar** |
| 170 | 11 | el logotipo que sube por la pantalla | 6 |
| 53 | 11 | el reproductor de música, nota larga | 9 |
| 50 | 9 | el reproductor de música, la octava | 7 |

La misma lectura de mandos, byte a byte en dieciocho cartuchos, se llama
`LEE_MANDOS` en uno, `lee_los_mandos` en otro, `lee_el_mando_por_el_psg`,
`lee_las_filas_7_y_8_del_teclado`, `teclado_del_jugador_1`… **doce nombres para
una sola rutina**, porque los repositorios se escribieron a lo largo de meses sin
un sitio donde mirar. Éste es ese sitio.

Y hay una pieza de **161 bytes repartida por doce cartuchos que diez de ellos
dejaron sin nombre** (`L_4716`, `L_4766`, `L_4867`…): sólo Ping Pong la bautizó,
como `PINTA_TIRA_BUCLE`. Bautizarla en los otros diez es trabajo para sus
repositorios, no para éste.

### Lo que este método no ve, y por eso hizo falta el siguiente

Compara **bytes**, así que sólo encuentra una rutina compartida si además la
ensamblaron en la misma dirección: en cuanto cambia el mapa de memoria, la misma
rutina da bytes distintos porque sus direcciones lo son. De aquí **no sale** una
separación en familias —a umbral bajo todos los Konami quedan conectados y a
umbral alto se deshacen en fragmentos—, sino un continuo. Eso lo resuelve la
comparación normalizada, abajo.

Un aviso concreto de esto: la lectura de mandos de 65 bytes que Athletic Land
comparte con Antarctic **está en la Antarctic europea y en la japonesa 1ª, y no
en la 2ª** — que es justo la que el Makefile de ese repositorio elige por
defecto y la que mide esta base. Un hallazgo puede depender de qué volcado se
mire.

## Las familias: qué armazón comparte cada cartucho

Aquí cada instrucción se **normaliza** poniendo a cero sus operandos de dieciséis
bits —los que llevan direcciones— y se comparan secuencias de instrucciones. Un
tramo largo de instrucciones iguales salvo las direcciones es la misma rutina
reensamblada en otro sitio.

La diferencia con la comparación por bytes no es teórica: **Super Cobra y Yie Ar
Kung-Fu comparten 203 instrucciones**, y la de bytes sólo les encontraba 39.
Golf y Tennis, 632 instrucciones frente a 256 bytes.

Y entonces sí aparecen familias. De los 37 cartuchos que se pueden medir así (las
cintas y las MegaROM no declaran un origen único, y se quedan fuera diciéndolo):

| cartuchos | años | la pareja más estrecha | quiénes |
|---:|---|---|---|
| 20 | 1983–1986 | athletic / cabbagepatch, 44,5 % y 40,8 % | athletic, billiards, boxing, cabbagepatch, goonies, hyperrally, hypersports 1/2/3, kingsvalley, knightmare, monkey, mopiranger, pingpong, pippols, roadfighter, skyjaguar, supercobra, yiearkungfu 1/2 |
| 5 | 1984–1985 | hyperolympic1 / hyperolympic2, **67,3 %** y 63,4 % | baseball, golf, hyperolympic1, hyperolympic2, tennis |
| 2 | 1983 | timepilot / frogger, 7,4 % y 14,9 % | frogger, timepilot |

Sueltos, sin llegar al umbral con nadie: antarctic, gamemaster, mahjong, soccer,
twinbee.

**El reparto no va por año**: la familia grande abarca 1983-1986 y la de los cinco
deportivos 1984-1985, solapadas. Tampoco por número de catálogo.

### Por qué el 5 %, y no otro número

Se une una pareja cuando el código común es al menos ese porcentaje de **ambos**
—el menor de los dos, no la media—. Barriendo el umbral:

    2 %   4 grupos: 28 + 2 + 1 + 1      todo pegado, no separa
    4 %   6 grupos: 22 + 5 + 2 + ...
    5 %   8 grupos: 20 + 5 + 2 + ...
    6 %  12 grupos: 16 + 5 + 2 + ...
    8 %  24 grupos:  5 + 3 + 2 + 2 ...  la familia grande ya se deshace

El grupo de cinco y el de dos **son los mismos del 4 al 8 %**, mientras la familia
grande se va deshaciendo. Eso distingue una familia de un artefacto del umbral, y
es un test.

Cómo hay que leerlo: agrupa por **código compartido medido**, y nada más. Que dos
cartuchos caigan en la misma familia no dice que los escribiera el mismo equipo ni
que uno saliera del otro. Y la familia de veinte es más un vecindario que una
familia: dentro hay parejas al 44 % y parejas que apenas se rozan.

## Cómo se usa

    python3 tools/recoge_portada.py  ../ > datos/proyectos.json
    python3 tools/recoge_binarios.py ../ > datos/binarios.json
    python3 tools/recoge_cifras.py   ../ > datos/cifras.json
    python3 tools/recoge_readme.py   ../ > datos/readmes.json
    python3 tools/monta_base.py            > datos/serie.json
    python3 tools/recoge_marca.py    ../ > datos/marcas.json
    python3 tools/recoge_creditos.py ../ > datos/creditos.json
    python3 tools/recoge_protecciones.py ../ > datos/protecciones.json
    python3 tools/monta_base.py            > datos/serie.json

    python3 tools/recoge_comun.py    ../ > datos/comun.json          # tarda
    python3 tools/nombra_comunes.py  ../ > datos/rutinas_comunes.json
    python3 tools/recoge_normalizado.py ../ > datos/normalizado.json  # tarda
    python3 tools/familias.py              > datos/familias.json

    python3 tools/coteja_portada.py  ..    # lo publicado contra lo medido
    python3 tools/make_web.py              # las 7 paginas por idioma
    python3 -m unittest discover -s tests  # 34 comprobaciones

`monta_base.py` va dos veces a propósito: los dos últimos recolectores necesitan
saber qué binario mirar, y eso lo dice `serie.json`. La segunda pasada da el
mismo fichero que la tercera. `datos/serie.json` es el registro que hay que leer;
los otros seis son las recogidas de las que sale.

## Lo que todavía no está

Los cartuchos que no se pueden comparar normalizados: las **cintas** y las
**MegaROM** (Nemesis, F-1 Spirit), porque no declaran un origen único. Medirlas
exige tratar cada banco o cada pieza de cinta por separado, con su propio origen.
