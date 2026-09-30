# 130 · La V25: la base lineal dels dos trens a la graella de Pere, amb la corba B i el detall ACHF

**2 de setembre de 2026 (tarda i nit).** Ordre de Pere, després de triar la
corba B entre dues vistes: «fes el LDIC lineal en base a l'opció B i mira si
pots preparar la imatge perquè no ho hagi de corregir tant jo després via
filtres [Camera Raw: contrast +42, textura +100, borrar neblina +17, que crea
un petit halo fosc a la corona interior]. Suposo que superposant filtres de
Druckmüller treurem resultats millors… sigues resolutiu.»

Lliurable: `Projecte photoshop/1-Unint Capes/Capes Totals/CapesTotalsV25_lineal_B.psb`
(3,59 GB, 23 capes, porta Photoshop OBRE), rebut al costat
(`CapesTotalsV25_lineal_B_REBUT.md`), vistes a `IA/output/v25_lineal_20260902/`,
eines a `research/tools/v25_lineal/`, mesures a `cau_v25/`. La V24 no s'ha tocat.

## 1. La decisió de la corba, amb dues imatges

Les dues corbes declarades (maqueta 0,17/0,68; cadena 0,22/0,74/0,045) es van
renderitzar sobre la mateixa dada (run 019, `comu.render_visual`, mateixa
àncora) al llenç sencer, amb finestra 1:1 i perfil de nivell contra radi
(`IA/output/corba_de_to_20260902/`). Pere: «les dues són molt semblants però em
decanto per la opció B». Nivell G: 1,1 R☉ 0,733 · 1,5 0,514 · 2,5 0,315 · 4,0
0,275 (A: 0,673 · 0,505 · 0,352 · 0,321).

## 2. El que s'ha construït (tres etapes, tot al rectangle sencer)

**Etapa 1 · fusió i base al llenç comú** (`etapa1_fusio_base_detall.py`):
sRGB lineal per tren amb la seva matriu (CIENCIA); ρ de la Sony a la Vixen per
canal, radial en ln r × azimutal k≤2, finestra 2,0-3,5 R☉ (quocient ~0,31-0,34,
azimutals ≤ 1,5 %, residu 0,7-0,9 %); fusió smoothstep 2,00→2,65; fons per raig
(σ_lnr 0,2, rampa 2,45→3,25, estrelles re-injectades); corba B sobre la
lluminància; detall = NRGF + ACHF 2-32 px per canal → mediana → suavitzat S/N →
anivellat (H1 0,0007) i passa-alt σ24 (H1 0,0033).

**Etapa 2b/2c · geometria** (`etapa2b_geometria_v23.py`, `etapa2c_afina.py`):
llenç comú → V23 mesurat contra la fusionada de la V24 sobre la corona sencera
(1,15-4 R☉, banda 4-40 px): rotació −91,969°, escala 1,0000; 48 finestres:
residu mediana 1,49 px, p90 2,55 px, sense component de similitud. ⛔ L'etapa
2 original, contra la capa 10 sola (anell prim 1,09-1,45), es va enganxar a la
vora del disc: 89,94° i 22 px d'error a les finestres. Regla: registrar contra
la corona sencera, mai contra un anell que contingui el limbe.

**Etapa 3 · muntatge** (`etapa3_munta_v25.py`): un re-mostreig Lanczos de base
i capes de detall; extensió per raig del cel fora de la cobertura (16 % del
llenç, cosmètica declarada, com la V19); mitja lluna del limbe omplerta per
raig (fins a 22 px, declarada); ghost de la Sony tapat a 2,99 R☉ (declarat);
PSB nou copiant la V24, capes 01-13 apagades, EARTHSHINE V24e reposada SOTA
la base, base amb màscara que s'obre dins d'1,012 R☉, ACHF 70 % i passa-alt
40 % apagat, ESTRELLES i REFLEX reposades a dalt; fusionada a quatre canals;
fidelitat 3/3; perfil radial monòton PASSA; porta Photoshop OBRE.

## 3. Cinc trampes pagades en una tarda (totes a `trampes.md`)

1. **Dos `comu.py`** (pilot i cadena) al `sys.path`: carrega cada família amb
   la seva ruta i treu el mòdul de `sys.modules` abans de carregar l'altre.
2. **0 × NaN = NaN a la fusió**: fora de la cobertura de cada tren els FITS
   porten NaN; `nan_to_num` abans de la suma ponderada, no després.
3. **La fusionada d'un PSB de 16 bits amb bloc `Mt16` té QUATRE canals**: amb
   tres, Photoshop diu «les opcions d'obertura no són correctes».
4. **A la V24 les perles i el limbe són les capes de MÉS AVALL** amb màscares
   gairebé opaques; posar-les a dalt pinta un rectangle negre. I la capa
   EARTHSHINE V24e porta una banda exterior fins a ~1,08 R☉ amb el compost V23
   a nivell 0,51 («banda = max(meu, seu)»): sobre una base més clara és una
   franja fosca. Cal llegir l'ordre i les màscares abans de reordenar res.
5. **El forat lunar de la cadena no és el disc de C2 de Pere**: vora de la base
   a 1,010-1,050 R☉ segons l'azimut. Cap capa hi tenia dada: s'ha omplert per
   raig i s'ha declarat. La cura de fons és a la fase 2 de la cadena.

## 4. Deutes i què segueix

- Un sol re-mostreig del RAW a la graella de Pere (fase 2 de la cadena amb el
  llenç V23 com a `LLENC_COMU`): elimina el segon re-mostreig i el residu d'1,5 px.
- Variància per canal a la cadena → porta de soroll a l'ACHF i WOW/NAFE.
- Temps físics i darks per temperatura (research/129 §5).
- La prova A/B amb la mateixa vara: la V24 amb el Camera Raw de Pere (TIFF)
  contra la V25 tal qual (bony per sector, H1, H4). Pere ha de mirar.
- Color: la base és CIENCIA (extinció de León); el blau del format canònic és
  Camera Raw de Pere i va a sobre.
