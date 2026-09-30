# 162 — Earthshine V44: contorn Vixen, registre i detall lunar

10-09-2026 · Codex · encàrrec directe de Pere sobre les marques verdes i cian.

## Resultat i abast

Lliurat a `Capes interiors/Earthshine_V44.psb` (18:31:05 UTC), amb la còpia
verificada a `research/tools/v44_earthshine_20260910/staging/Earthshine_V44.psb`:
10551 × 7506, RGB de 16 bits, 18 capes. Les quinze capes d'entrada de
`Earthshine_V43_detall.psb`, incloses les anotacions i els ajustos de Pere,
conserven els canals comprimits byte a byte. La capa antiga pintada queda
oculta; `09 1/60 x2` continua visible. S'afegeixen una aportació natural
al 12 % visible, una alternativa al 24 % oculta i l'HDR mesurat de diagnòstic
ocult. Les dues aportacions són alternatives: activar-ne només una.

**Lliurament verificat amb Photoshop real.** SHA-256
`49fe61696845014160278d431969972ea59d1566b33ed0250bdcc4d9d8e33220`;
1.237.257.170 bytes. `C5_publish.json` i `C5_photoshop_readback.json`, a
`output/v44_earthshine_20260910/4-rebuts/`, lliguen el mateix SHA al contenidor,
a l'obertura, a la recomposició real i al fitxer publicat. La diferència
màxima és 1 DN16 tant a la ROI lunar com als píxels visibles de tot el llenç;
l'alfa és exacte (diferència 0). La verificació estructural per si sola no
substitueix aquestes proves.

No canvia el camp, l'escala del llenç ni la posició de la Lluna. No s'ha
inserit relleu de LROC: només serveix de jutge extern. El conjunt de Capes
Totals continua sent V42; aquesta ronda lliura l'earthshine per separat.

## Fonts i causa de les marques

- V43 lliurada: SHA-256
  `52ac5cfd90d7b1434eec49274b694b72c19e3159a490a2b3e2f27119b8d025b1`.
- V43 anotada de Pere: `Earthshine_V43_detall.psb`, SHA-256
  `609c3a5f2a1f03930629e1e163d33f40e3541d69e0b7835a58552ea6acc0c8e4`.
- Handoff llegit: `.coordination/HANDOFF_2026-09-10_CLAUDE_A_CODEX_EARTHSHINE.md`;
  cadena anterior a `research/tools/v43_earthshine_20260910/`.
- Inventari, rectangles, màscares i marques: `A0_inventari_psb.json` i
  `A1_marques.json`. La capa anotada també tenia un canvi de to de Pere;
  no s'ha atribuït tota diferència a la pintura.

La sensació de «Lluna petita» no justifica ampliar el disc a ull. Hi havia
tres problemes separats: la màscara V43 començava/acabava quatre píxels abans
del literal del rebut; el perfil azimutal es llegia amb veí més proper;
i la transició estreta en radiància, passada per la corba logarítmica,
donava una vora efectiva de només aproximadament 0,56 píxels en pantalla.
A més, la corona exterior usada per unir la V43 no tenia el mateix to ni
la mateixa resposta angular que la capa `09` visible de Pere.

La falta de relleu cian tenia també causes de procés: el σ3 i l'esvaïment
0,85–0,95 R eliminaven detall exterior. Un segon remostreig de radiància amb
NaN substituït per zero, separat del pes, introduïa biaix fosc a prop dels
píxels saturats. La selecció temporal barrejava rellotges amb un desfasament
de 10,83 s entre els orígens C2 dels dos sensors.

## Reapilat i moviment

S'han tornat a apilar 88 entrades lunars: 67 Vixen, 9 Sony A i 12 Sony B.
Catorze tessel·les amb correcció de registre s'han regenerat des dels RAW
amb la calibració existent. Les altres conserven la seva única interpolació
ja calculada. No s'ha tornat a calibrar indiscriminadament tot l'arxiu.
`B2_inputs.json` identifica per fotograma el fitxer, pes, hash, instant i
correcció; els `B2L_*.json` documenten les regeneracions.

La geometria solar, lunar i de camp existent es conserva i el registre fi
s'incorpora a la transformació inversa abans de l'única interpolació CFA.
Numerador i denominador reben la mateixa geometria. L'instant de selecció
és `t_inici + exposició/2 − C2_sensor + C2_vixen`. La superfície acumula tots
els instants vàlids; el suport de l'instant lunar al contorn té T0 = 15 s
en el rellotge Vixen i escala temporal 10 s. Això no és una deconvolució
del moviment durant cada exposició.

El registre usa correlació creuada entre sensors, prefiltratge de camp
sencer sense una màscara comuna incrustada, moments FFT de doble precisió
i controls de translació coneguda. L'equivariança numèrica del control és
millor que 3e−7 px; **no és precisió astromètrica**. La discrepància entre
sectors encara és aproximadament d'1–5 px en els fotogrames febles (fins
a 4,98 px a 572A2980).

La base de relleu i l'exterior usen Vixen + Sony A (76 entrades), amb zero
píxels sense dada al disc. Sony B aporta només detall interior corroborat,
principalment 16–24 px: queda exclosa a menys de 140 px del ghost, entra
completament a 180 px i s'esvaeix entre 0,86 i 0,88 R. No aporta fons ni
detall exterior. S'han estudiat i apilat totes les entrades sense obligar
una dada contaminada a contribuir a totes les zones.

## Contorn i unió amb les perles

El contorn es mesura als verds CFA natius de 17 exposicions curtes Vixen,
amb derivada radial σ0,75 px i 1.440 angles; la validesa censura saturació
però el llindar radiomètric de pes no pot fabricar la vora. Mediana del
contorn observat: 453,323 px; desacord entre meitats: 0,237 px RMS;
dispersió mediana entre fotogrames: 0,546 px. Són mesures del contorn òptic,
no un model de topografia lunar subpíxel.

L'aportació fotogràfica s'afegeix sobre la `09` intacta. La cobertura usa el
contorn observat amb integració de 4 × 4 subpíxels. Aquesta quadratura no
augmenta la resolució de la imatge. La resposta de pantalla de `09` s'ajusta
per sectors alterns, amb σ efectiu 2,107 px, exponent 9,959 i una fase angular
de primer i segon harmònic. Error normalitzat mitjà absolut: 0,04193 als
sectors d'ajust i 0,04191 als reservats. Excloent els pols de l'ajust,
l'error als pols és 0,04023. La fase pertany a la resposta de pantalla:
no desplaça ni engrandeix la geometria lunar.

Aquest model és **empíric i auxiliar**. No prova que l'anisotropia vingui
d'una PSF física concreta ni resol tota la història de processat de `09`.
El criteri fotomètric protegeix els píxels on algun canal de `09` arriba o
supera la continuació exterior local modelada: inclou perles brillants i
corona, però no és una identificació exhaustiva de totes les perles.
19.112 píxels així protegits conserven exactament el valor de `09`; l'aportació
és zero fora de radi 470 px i no enfosqueix cap píxel de la base.

La revisió independent a 1:1 i als quatre punts cardinals confirma la
millora de la unió i la conservació visual de les perles brillants revisades.
L'exploració d'arcs molt
estrets encara troba transicions febles locals (fins a aproximadament
0,0084 sRGB en una mediana de 5°); no s'afirma «cap residu al limbe».

## Detall i comprovació independent

El relleu combina fons mesurat i detall local amb ajust quadràtic en log
radiància. La síntesi central evita que la corona brillant contamini tota
la finestra. A l'exterior s'usa detall tangencial a radi fix, que evita
barrejar el gradient coronal amb la superfície; no recupera les components
radials de la mateixa manera. El mode radial constant d'aquest operador
té transferència zero, explícitament.

Jutge: LROC amb la geometria prèvia congelada. Màscara: els traços cian
reals de Pere. Banda tangencial 16–24 px. Nul: onze rotacions diferents,
de 30° a 330°. Són controls de correspondència de relleu, no una mesura
d'augment percentual de resolució òptica.

| Anell lunar | V43 radiància log: r | V44 radiància log: r | V44 final de pantalla: r | Màxim nul absolut final |
|---|---:|---:|---:|---:|
| 0,84–0,88 R | 0,214 | 0,205 | 0,247 | 0,129 |
| 0,88–0,92 R | 0,175 | 0,205 | 0,163 | 0,101 |
| 0,92–0,96 R | 0,125 | 0,198 | 0,212 | 0,092 |

La millora més clara és a 0,92–0,96 R. No totes les mètriques milloren a
tots els anells. **Entre 0,96 i 0,995 R no hi ha relleu corroborat suficient**:
la prova falla tant a les fonts com al resultat. El detall exterior
s'esvaeix entre 0,955 i 0,965 R i no es presenta aquesta franja final com
a superfície recuperada.

Injeccions febles de 0,05 DN sobre el fons real, després de l'apilat
calibrat: transferència 0,945–1,014 a 8, 12, 16 i 24 px en els operadors
locals; 0,977–0,999 a 16–24 px tangencials; 0,959–1,014 en la contribució
comuna amb Sony B. Aquests controls passen la finestra 0,9–1,1 declarada.
No proven la resposta de l'òptica, la calibració anterior ni el moviment
intraexposició. Detall i guany estan declarats a `F6_QA.json`.

El nivell natural usa G sRGB 0,176, proper al de Pere. Color mesurat
[1,03593, 1,05550, 0,85307]; contrast de relleu 12 % amb K = 15,9145,
o 24 % amb K = 31,5612. Aquest contrast amplifica un senyal feble: no
s'ha d'interpretar com a fotometria absoluta de la cara fosca lunar.

## Negatius preservats i límits

L'intent inicial de detall local en radiància lineal (`F3_detall.json`)
contaminava l'exterior amb la corona: RMS exterior 285 DN davant d'1,19 DN
interior. Queda rebutjat i fora de les capes lliurades. Els primers detectors
de limbe que usaven el tall de pes radiomètric també queden superats per
`F4_no_floor_in_detector.log`. Els logs inicials no són el resultat vigent.

La primera verificació amb `sips` va fallar per una excepció del lector.
ImageMagick llegeix el contenidor com a PSB de 16 bits i mida correcta.
La primera invocació sandbox de Photoshop va fallar; l'escalació va ser
rebutjada per manca d'autorització concreta de GUI segons la revisió
automàtica. Pere va autoritzar expressament la comprovació i acabar desatès.

La prova real ha requerit corregir dues particularitats del verificador:
`colorProfileName` no existeix en el document sense perfil assignat
(`ColorProfile.NONE`, estat heretat que es conserva), i un TIFF opac aplana
la transparència sobre blanc. El primer TIFF ja donava 1 DN16 a la Lluna,
però no validava els marges. L'exportació RGBA definitiva conserva alfa i
declara TIFF `ASSOCALPHA`: el RGB s'ha comparat correctament en valors
emmagatzemats premultiplicats, sense anomenar-los radiància física. Els
errors i el TIFF opac es conserven com a diagnosi; no han canviat el PSB.

## Reproducció i recepció

Eines: `research/tools/v44_earthshine_20260910/`. Intèrpret utilitzat:
`/Users/USUARI/.venvs/eines-ia-py312/bin/python`, amb
`PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1`.

Ordre: `a1_psb_marques.py` → `a2_registre.py` → `b2_run.py` →
`f2_stacks.py` → `f3b_detall_log.py` → `f3c_tangencial.py` →
`f3d_sonyB.py` → `f4_contorn.py` → `f5_render.py` → `f6_qa.py` →
`c5_psb.py build`, `verify`, `gate`, `readback`, `publish`.
`f3_detall.py` és un negatiu, no un pas de la recepta final.

La reproducció necessita els RAW, calibracions i caus V42/V43 referenciats
pels imports i `B2_inputs.json`. No és un paquet autònom. La construcció i
publicació refusen sobreescriure el PSB existent; una rèplica requereix
una sortida nova i el claim corresponent. No s'ha executat una segona
rèplica completa RAW→PSB: s'ha verificat aquesta execució i els seus canals.

Portes superades: fonts intactes; canals originals byte a byte; canals nous
uint16 exactes; lector independent; `porta_photoshop.sh` (OBRE 10551 px x
7506 px · 18 capes); recomposició forçada dins de Photoshop i readback TIFF
RGBA contra els píxels esperats. Tolerància declarada: màxim 6 DN16;
resultat: 1 DN16 a la Lluna i al llenç visible complet, alfa exacte.
S'han revisat visualment el resultat lunar a 1:1 i el llenç complet procedents
de la recomposició real. La geometria dels marges de la capa09 es conserva.
Les vistes de comparació són a `output/v44_earthshine_20260910/lliurables/vistes/`.
L'acceptació visual final correspon a Pere.
