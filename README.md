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

## Cómo se usa

    python3 tools/recoge_portada.py  ../ > datos/proyectos.json
    python3 tools/recoge_binarios.py ../ > datos/binarios.json
    python3 tools/recoge_cifras.py   ../ > datos/cifras.json
    python3 tools/recoge_readme.py   ../ > datos/readmes.json
    python3 tools/monta_base.py            > datos/serie.json

    python3 tools/coteja_portada.py  ..    # lo publicado contra lo medido
    python3 -m unittest discover -s tests  # 12 comprobaciones

`datos/serie.json` es el registro que hay que leer; los otros cuatro son las
recogidas de las que sale.

## Lo que todavía no está

Esto es la primera de cuatro capas. Faltan **los créditos** (quién firma cada
juego, con su cita y su dirección en el binario), **lo compartido** (la matriz
de tiras de bytes idénticas entre los cuarenta y siete binarios, generalizando
`comun_konami.py`) y **la web** bilingüe de la serie.
