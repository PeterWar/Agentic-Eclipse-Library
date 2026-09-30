# El `-110` de la R6 no és el cable: és cadència sense marge

8 d'agost de 2026, vespre. Diagnòstic del run multicàmera `20260808T173855`,
on la R6 va perdre 34 fotogrames de 120 i 42 de 61 canvis d'exposició.

## Conclusió

**No és el cable, ni el connector, ni l'enllaç USB.** Són dues causes
independents, totes dues de pressupost de temps:

1. **27 de les 34 pèrdues**: la cadència de 0,40 s de les finestres de
   contacte **no té marge per construcció**, i en aquesta sessió el cos només
   acceptava una pulsació cada **0,80 s**.
2. **7 de les 34**: el forat entre fotogrames es compila amb l'obturació
   **prevista**; quan un setter és rebutjat, el fotograma anterior és més
   llarg del que el pla creu i la pulsació següent xoca.

## Per què no és el cable

| Evidència | Valor |
|---|---|
| Reconnexions de sessió PTP | **cap**: `connection_epoch` = 1 tot el run |
| Durada de les 34 recuperacions | 6–42 ms, mediana 12,5 |
| Bateria | 98 % |
| Ajustos del cos | idèntics al run bo del 7 (RAW, Single, Memory card, NR alt off) |
| Espai lliure a la targeta | **més** que el dia 7: 7.168 fotos contra 3.756 |

Un connector intermitent tomba l'enllaç i obliga a reobrir la sessió. Aquí la
sessió no es va perdre ni una sola vegada: el cos era viu i responia, i el que
deia era «I/O in progress» a pulsacions que arribaven massa aviat.

## El patró que ho va destapar

Les pèrdues són **alternades**: 25 de les 33 distàncies entre pèrdues
consecutives són exactament 2, en dos trams llargs.

```
  1  .....X.X.X.X.X.X.X.X.X.X.X..........X.....XX..........XX....
 61  ....................XX....X.X.X.X.X.X.X.X.X.X.X.X.X.X.X.X...
```

Els dos trams són **les finestres de contacte**, l'únic lloc del programa on
els fotogrames van a 0,40 s. La mecànica, mesurada:

- interval **planificat** entre fotogrames de contacte: 0,400 s;
- interval **real** entre les pulsacions que van sortir al tram 87–117:
  **0,797–0,807 s**, mediana 0,802 sobre quinze fotogrames.

O sigui: la pulsació de 0,40 arriba massa aviat i el cos la refusa; la
recuperació costa 12 ms; la següent, que ja cau a 0,80 s de l'última bona,
sí que hi és a temps. Fallada, encert, fallada, encert.

## El pressupost no tenia marge, i això és nostre

```
r6m3_single_hdr_frame_gap_s("1/2000")
  = max(0,40 ; 0,0005 + 0,40 + 0,0) = 0,400 s
```

El forat compilat és **exactament** el terra declarat. Marge: zero. Un
programa que corre exactament al límit mesurat del cos falla el dia que el
cos va una mica més lent, i «una mica més lent» no és una hipòtesi: és el que
va passar.

## No és un terra fix, és una **cadència sostinguda**

Els primers fotogrames de la finestra sí que surten a 0,40 s, i llavors el cos
es queda enrere:

| Fotograma | Interval | Durada de la pulsació | Resultat |
|---:|---:|---:|---|
| 1–3 | 25–30 s | 0,053–0,054 s | ok |
| 4 | 0,40 s | 0,053 s | ok |
| 5 | 0,40 s | **0,141 s** | ok |
| 6 | 0,40 s | — | **perdut** |
| 7 endavant | 0,40 s | 0,105–0,121 s | un sí, un no |

El cos absorbeix dues pulsacions a 0,40 s i després només en sosté una cada
0,80. La durada de la pulsació és l'indicador: **de 54 ms a 121 ms**.

## La comparació que ho tanca

Run `20260807T172151`, **la mateixa geometria i la mateixa cadència de 0,40**:

| | 7 d'agost | 8 d'agost |
|---|---:|---:|
| Fotogrames | **115/115** | 86/120 |
| Saltats · recuperacions | 0 · 0 | 34 · 34 |
| Durada de pulsació, mediana | **54 ms** | 121 ms (màx 277) |
| Intervals reals a 0,40 s | **55 seguits, mediana 0,401** | cap: 0,80 |

Mateix codi, mateixa geometria, mateixos ajustos, més espai a la targeta i
més bateria. El dia 7 el cos va sostenir 55 pulsacions seguides a 0,401 s; avui
no n'ha sostingut ni tres. **La diferència és del cos, no del programa** — però
el programa no tenia ni una dècima de marge per absorbir-la.

Això explica també el run trencat del 7 al vespre, que es va atribuir a «un
estat intermitent del transport USB»: la seva signatura era **114 ms de
mediana de pulsació contra 20**, exactament la d'avui. És el mateix fenomen.

## Què queda sense explicar

**Per què el cos va més lent avui.** Pere confirma que no s'ha canviat res:
mateix cable i mateixa CFexpress, i els ajustos són idèntics. Queda la
temperatura —el cos porta un dia sencer de feina— o alguna altra variació
d'estat que no es veu des del Mac.

**I això, en el fons, és la lliçó.** No cal saber per què el cos va més lent
un dia que un altre: cal que el programa no depengui que vagi de pressa. La
correcció de sota va per aquí.

## D'on sortia el 0,40, i per què era un error de traspàs

Pere confirma que **no s'ha canviat res**: mateix cable i mateixa CFexpress.
Això obliga a mirar el número, i el número no venia d'on semblava.

Els 400 ms surten de la campanya **EDSDK** de `research/60`: el cos hi va
acceptar **dotze** pulsacions seguides sense cap rebuig. Dotze no és una
cadència sostinguda, i l'EDSDK no és la pila que vola.

I la mesura bona ja existia al repositori, sense fer-se servir. Escala de
cadència del **6 d'agost, per gphoto2, amb prova de resistència**:

| Interval | Grups | Esperats | Observats | Veredicte |
|---------:|------:|---------:|----------:|-----------|
| 0,80 s | 125 | 375 | 375 | PASS |
| **0,60 s** | **165** | **495** | **495** | **PASS** |
| 0,60 s | 20 | 60 | 60 | PASS |
| 0,55 s | 25 | 75 | **39** | FAIL |
| 0,55 s | 25 | 75 | 75 | PASS |
| 0,50 s | 25 | 75 | **3** | FAIL |

**0,60 aguanta 165 grups seguits; 0,55 és marginal —un PASS i un FAIL— i 0,50
s'ensorra.** El programa de missió corria a **0,40**, per sota fins i tot del
que s'ensorra. Que el dia 7 fes 115/115 no era robustesa: era sort.

## Correcció aplicada

`R6M3_SINGLE_HDR_FRAME_MIN_GAP_S` passa de **0,40 a 0,65** —el terra verificat
per resistència més un 8 % de marge— als **dos** testimonis independents: el
compilador de la GUI i el worker congelat. El guard fail-closed va fer la seva
feina i va refusar el perfil fins que les dues declaracions van coincidir.

A 98,8 s de totalitat el programa passa de 115 a **88 fotogrames**, 69 dins la
totalitat, i **conserva les 15 exposicions úniques**. Les finestres de contacte
passen de 25 a 16 a C2 i de 22 a 14 a C3 — i el run d'avui, amb 25 previstos,
només en va lliurar 14 i 11. **Menys sobre el paper i més a la targeta.**

De retruc va destapar dos defectes més:

- el contracte del perfil derivava **l'evidència d'un run passat** de la
  constant viva, o sigui que canviar la geometria reescrivia en silenci la
  geometria d'un run que ja s'havia fet. Ara el 0,40 d'aquell run és literal;
- la sonda de comparació EDSDK no reservava el setter que obre la finestra de
  C3, i amb 0,40 les dues implementacions coincidien igualment. A 0,65 hi
  encabia una escala de més. Corregida contra el worker, que és l'autoritat.

## Segona ronda: el run `20260808T192218` amb la cadència a 0,65

La correcció va fer el que havia de fer i va destapar el defecte de sota.

| | 0,40 s | 0,65 s |
|---|---:|---:|
| Fotogrames disparats | 86 de 120 (72 %) | **77 de 88 (88 %)** |
| A l'exposició prevista | 49 | **58** |
| Exposicions úniques | 9 | **12** |
| Accions saltades · recuperacions | 76 · 34 | **25 · 11** |
| **Finestra de C2** | 14 de 25, totes bones | **16 de 16, totes bones** |
| **Finestra de C3** | 11 de 22, totes bones | **7 de 14, cap bona** |

**El bloc de C2 va sortir sencer i perfecte per primera vegada.** El de C3 es
va perdre, i per una causa diferent:

```
86,55  fotograma 0,5 s                                 ok
87,45  setter → 1/2000            REBUTJAT (busy, actiu = 0,5 s)
87,70  fotograma  vol 1/2000      ok, però a 0,5 s
...    tretze fotogrames de la finestra de C3, tots a 0,5 s
```

**Un sol setter refusat es va menjar la finestra sencera**, perquè la finestra
de contacte no té cap més canvi d'exposició per disseny. I a 0,5 s els
fotogrames necessiten 0,90 mentre el pla els espaia a 0,65: d'aquí que a més
en caigués un sí i un no.

La causa és **la mateixa malaltia en un altre lloc**: la readiness del setter
després d'un fotograma era exposició + 0,30 s, calibrada exactament sobre les
mesures del 7 d'agost a 2, 8 i 15 s —marge zero— i **extrapolada a 0,5 s, on
mai no s'havia mesurat**. El pla hi va posar 0,90 i el model en reservava 0,80.

Hi havia un defecte estructural al costat: la finestra de C3 obre **tan aviat
com pot** per aprofitar temps mort —aquí, 6,1 s abans del que calia—, i això
col·loca el seu únic setter just darrere el fotograma més lent de l'escala.

## Segona correcció

`R6M3_SINGLE_HDR_SETTER_AFTER_FRAME_GUARD_S = 0,35`, i l'interval entre
fotogrames ara ha de cobrir també la readiness del setter que ve darrere:

```
gap(obturació) = max(terra 0,65 ; exposició + 0,40 ; ready + 0,35)
```

El cas que va fallar passa de 0,90 a **1,15 s**. Les finestres de contacte, a
1/2000, no es mouen: continuen a 0,65 i C2 conserva els seus 16 fotogrames.
Com que el marge viatja dins l'interval, l'obertura elàstica de C3 l'hereta i
el seu setter deixa de caure enganxat a l'escala.

Preu, a 98,8 s: de 88 a **84 fotogrames**, amb les 15 exposicions úniques i
els dos fotogrames de 15 s intactes. **Per sota de 96 s de totalitat es perd
un dels dos fotogrames de 15 s** —el marge es paga d'aquí—, i és un preu que
val la pena: l'earthshine principal el porta l'A7RIIIA amb sis àncores, i el
que es protegeix és el segon anell de diamant.

## Tercera ronda: verificat al cos, i surt net

Run `20260808T202023`, multicàmera, totalitat 98,8 s, amb la cadència a 0,65 i
el marge de 0,35 posats.

| | 0,40 | 0,65 | 0,65 + marge |
|---|---:|---:|---:|
| Fotogrames | 86 de 120 | 77 de 88 | **84 de 84** |
| Setters rebutjats | 42 de 61 | 14 de 63 | **0 de 49** |
| Accions saltades | 76 | 25 | **0** |
| Recuperacions | 34 | 11 | **0** |
| Bloc de C2 | 14 de 25 | 16 de 16 | **16 de 16** |
| Bloc de C3 | 11 de 22 | 7 de 14, cap bona | **14 de 14, totes bones** |
| Resultat del canal | WARNING | WARNING | **COMPLETE** |

**133 accions, retard màxim 0,011 ms**, les 15 exposicions úniques, els dos
fotogrames de 15 s, postflight sencer correcte i `card_only_schedule_and_
ledger_complete`. Identitat verificada, cleanup i restore correctes.

És el primer run en què aquest cos no perd res. Les dues correccions —la
cadència que venia d'una campanya EDSDK de dotze pulsacions, i el marge del
setter que anava enganxat al fotograma anterior— eren les dues causes, i no
n'hi havia cap tercera.

## Què queda

**El reintent acotat continua sense fer-se, i continua valent la pena.** Aquest
run no n'ha necessitat cap, però la finestra de C3 encara depèn d'**un sol
setter sense reintent**: si algun dia el refusa, la torna a perdre sencera. El
contracte del projecte ho permet per a un `was not set` net i el worker ja en
té la maquinària.

**I el deute de sempre**: `card_only`. El postflight acredita cronologia i
ledger, no els CR3 de la CFexpress un per un.

## El que sí que va bé

Mission First va funcionar com toca: identitat verificada, cleanup i restore
correctes, `physical_state_unknown=false`, cada acció ambigua consumida sense
replay i **la Sony no se'n va ressentir gens** (38/38, retard màxim 0,008 ms).
Les finestres de contacte van conservar l'exposició correcta en els fotogrames
que van sortir: 14 de 14 a C2 i 11 de 11 a C3, tots a 1/2000. Les perles i els
dos anells hi són.
