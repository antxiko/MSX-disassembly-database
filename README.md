# La base de datos de la serie de desensamblados MSX

Los cuarenta y siete desensamblados y los dos parches de la serie, reunidos en
un registro único que **no copia ninguna cifra**: las mide.

    proyectos                 49   (47 desensamblados y 2 parches)
    instrucciones            249.851
    comentarios de línea      81.234        32,5 % del total
    rutinas                   31.011
    rutinas por debajo del 10 %    0        en toda la serie
    bytes de binario       1.465.115

Medido el 2026-09-09 sobre los listados que cada repositorio publica.

## Por qué se vuelve a medir todo

Porque las cifras publicadas envejecen. La ficha de cada juego en la portada se
escribió el día que se publicó; si después alguien vuelve al listado y comenta
otra tanda, la web sigue diciendo la vieja. Pasa de verdad, y esta base lo
encontró a la primera:

- **Trailblazer** publica 30,7 % y su listado da hoy 30,8 %: el `.asm` se tocó
  en un commit posterior al del README.
- **Hyper Rally** (22,1 → 22,6), **Hyper Sports 2** (22,5 → 22,7) y **Nemesis**
  (23,3 → 23,4), lo mismo.
- La memoria de trabajo de **Twin Bee** daba 24,6 % cuando el listado ya iba por
  41,4 %: se había escrito a mitad de la tanda de comentarios.

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

Nada se empareja por parecido del nombre y nada se rellena a ojo: un proyecto al
que le falte una pieza sale con esa pieza a nulo y un aviso.

### La vara es la misma para los cuarenta y siete

Cada repositorio trae su copia de `densidad.py`, escritas a lo largo de meses, y
comparar entre juegos exige saber que cuentan igual. Hay cuatro variantes, y las
cuatro usan **el mismo criterio**: se diferencian en el fin de línea, en un caso
especial de Nemesis (un banco sin código) y en que la de Trailblazer suma varias
piezas de cinta. Así que aquí se mide con una copia canónica, y además se corre
el `make densidad` del propio repositorio para contrastar:

**34 repositorios cotejan exacto y ninguno discrepa.** Eso es lo que hace válida
la cifra de los 14 que no traen ese target, y es un test (`test_base.py`).

## Un hallazgo: "etiquetas" no significa lo mismo en todas las fichas

La portada publica un número de "etiquetas" por juego, y son tres magnitudes
distintas según el juego:

- las **rutinas** que cuenta `densidad.py` — Twin Bee, 1.000;
- las **"etiquetas con nombre"** del README — Hyper Sports 2, 314, que tiene 500
  rutinas;
- las **etiquetas del listado** — War in Middle Earth, 819.

Y en seis juegos (Billiards, Yie Ar Kung-Fu II, Demonia, F-1 Spirit, Stardust,
Temptations) la cifra publicada no es ninguna de las tres, y hoy no se sabe de
dónde sale. Quien compare "1.000 etiquetas" de Twin Bee con "314" de Hyper
Sports 2 está comparando cosas distintas.

Está sin corregir a propósito: tocar diecisiete fichas de la portada es otra
tarea, y se decide aparte.

## La firma de la casa: la marca oculta de Konami

El hallazgo **no es nuestro**: lo destapó **Manuel Pazos** (@ManuelPazosMSX) en
septiembre de 2021. Konami escondió en muchos de sus cartuchos el número de
catálogo y el título en katakana, del revés y con el código de la casa. Aquí se
rastrea en los cuarenta y nueve binarios, también en los que no son de Konami:
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

## La firma de las personas: quién hizo cada juego

De los cuarenta y nueve binarios, **19 llevan algún crédito en texto legible**.
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

## Cómo se usa

    python3 tools/recoge_portada.py  ../ > datos/proyectos.json
    python3 tools/recoge_binarios.py ../ > datos/binarios.json
    python3 tools/recoge_cifras.py   ../ > datos/cifras.json
    python3 tools/recoge_readme.py   ../ > datos/readmes.json
    python3 tools/monta_base.py            > datos/serie.json
    python3 tools/recoge_marca.py    ../ > datos/marcas.json
    python3 tools/recoge_creditos.py ../ > datos/creditos.json
    python3 tools/monta_base.py            > datos/serie.json

    python3 tools/coteja_portada.py  ..    # lo publicado contra lo medido
    python3 -m unittest discover -s tests  # 18 comprobaciones

`monta_base.py` va dos veces a propósito: los dos últimos recolectores necesitan
saber qué binario mirar, y eso lo dice `serie.json`. La segunda pasada da el
mismo fichero que la tercera. `datos/serie.json` es el registro que hay que leer;
los otros seis son las recogidas de las que sale.

## Lo que todavía no está

Esto son dos de cuatro capas. Faltan **lo compartido** (la matriz de tiras de
bytes idénticas entre los cuarenta y siete binarios, generalizando
`comun_konami.py`, para ver qué armazón comparte cada juego con cuál) y **la
web** bilingüe de la serie.
