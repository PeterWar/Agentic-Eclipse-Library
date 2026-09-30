# 169 · La «lupa» i els anells foscos arran del limbe: selecció física per fotograma (V98)

25-09-2026 · Claude, V98 (desatès) · Marques de Pere a `1-PHOTOSHOP/V97_Artefactes.psb` (P04, P03, P05, 04 ACHF, P02c, P01, P02) i punts 5 i 6 del seu encàrrec.

## 1. Què veia Pere
- **Punt 5, la «lupa»:** la corona interior, just al costat del limbe, semblava ampliada; les estructures no encaixaven amb les de pocs píxels més enfora. Pere en va pintar la intensitat: verd (esquerra), groc, vermell (dalt i dreta). A la WOW (P04) i a l'MGN (P03), sobretot; a la WOW bilateral (P05), menys.
- **Punt 6:** a 1–9 px del limbe no hi pot haver anells foscos concèntrics amb la Lluna; si n'hi ha, són del desplaçament de la Lluna.

## 2. D'on venia (mesurat)
**La franja d'un instant de la V86–V97** posava, a tota la zona escombrada per la Lluna (12–38 px segons l'azimut) i fins a 45 px, la dada de NOMÉS 11 fotogrames Vixen dels primers 22 s, suavitzada amb σ 1,3 px (i σ 0,8 px al mosaic).
- A dalt i a la dreta aquesta dada és sobretot soroll de gra gros: la correlació del seu pas alt amb la fusió és de 0,34–0,47 (0,68–0,90 a l'esquerra, on Pere marcava verd). `4-RESULTATS/v98_20260925/D1_REGISTRE_FRANJA.json`.
- La WOW i l'MGN igualen el contrast per escala: un gra més gros i fluix hi surt amb el contrast de la textura fina de fora. Això és la «lupa».
- A la dreta, a més, la franja feia un clot del −17 % a 1–3 px (ln G), que la fusió no tenia.

**El dèficit de vora de cada fotograma** (`D5_DEFICIT_VORA_comuna.json`): la corona que veu un fotograma a D px del seu limbe observat és més fosca. Curts: −43 % a 2 px, −13 % a 4, −5 % a 6. Mitjans: −16 % a 2, −4 % a 4. Llargs: −68 % a 2, −9 % a 4. Si es barregen fotogrames amb la Lluna a llocs diferents (la Lluna es mou −27,2 px en x i −8,5 px en y durant la totalitat), surten anells.
- ⛔ **La corba no és la mateixa a tots els sectors** (a 2 px, −12 % a baix-dreta i −26 % a dalt-dreta, `D7_DEFICIT_PER_SECTOR.json`). Calibrar-la (dividir per una transmissió de vora) seria posar un model en lloc de dada. Codex hi estava d'acord (`CODEX_PLA_V98.md`).

## 3. La cura a l'origen: selecció física per fotograma (`3-RECERCA/tools/v98_20260925/a3b_franja_neta.py`)
Per a cada píxel de la caixa lunar, la mitjana ponderada (els pesos LDIC de la cadena) de TOTS els fotogrames Vixen (67) que el veuen **net**: pes × smoothstep(D_obs, lo, hi) de la seva classe d'exposició, amb D_obs la distància al limbe observat d'aquell fotograma. Rampes: curts 6→9 px, mitjans 5→8, llargs 6→10 (on el dèficit mesurat ja és ≲ 1 %). Cap suavitzat.
- És el que fa Brno (Druckmüller, Rušin i Minarovjech 2006, eq. 3–4): de cada fotograma, els píxels que la Lluna no tapa (`LITERATURA_LIMBE.md`).
- **A la dreta i a baix-dreta** (la Lluna s'hi allunya) hi entren quasi tots els fotogrames (33–53 per píxel, contra 11): el S/N i la resolució de la resta de la imatge. La dada neta arriba fins al limbe.
- **A dalt i a l'esquerra** (la Lluna hi puja i hi avança) els primers ~5,7 px (10,7 a 180°) no els veu net cap fotograma: **no hi ha dada** (norma canònica). Les capes en Multiplicar hi porten només el nivell (decisió B de Pere); les de Superposar, transparent.
- Lluny del limbe és el mateix apilat: fusió / dada nova a 60–120 px = 1,0097 (p16–p84: 1,0085–1,0108). La unió (60–90 px) no fa costura.
- **Trampa trobada:** els `limb_frames` de la V85 eren de finestra LDIC per canal (la del polígon i els pentàgons, doc. 168); refets amb la comuna (`a9b_limb_frames_comuna.py`; el control per canal reprodueix la V85 bit a bit).

## 4. Els operadors a la vora de la dada
Una mitjana local que només veu un costat (convolució normalitzada d'ordre 0) té el biaix del gradient radial. Cures (`f3_filtres_v98.py`):
- **MGN i ACHF isòtrops:** mitjana local d'**ordre 1** (pla local, Knutsson i Westin 1993). Amb suport complet dona exactament l'ordre 0 (prova: |dif| ≤ 2,4·10⁻⁷); a la vora d'una rampa lineal, error 0 (l'ordre 0 hi feia fins a 3,1).
- **ACHF azimutals:** ordre 1 al llarg de l'arc, per FFT (a l'extrem d'un arc tallat: biaix −0,115 → 0).
- **WOW:** sense la «vora difuminada» de la V95 (era per al dèficit de la franja d'un instant); es queden els parells simètrics.
- **RHEF local:** parells simètrics per sector; una cel·la vota només amb ≥ 200 mostres (Gilly i Cranmer 2025 avisen del rang amb poques mostres).
- **RHEF:** la fosa de r_in (on els anells deixen de ser complets), de 8 a 64 px: la de 8 px feia l'arc de ~14 px sobre la Lluna (marques P02/P02b).

## 5. Resultat (jutge per capa `J14_V98.json`, compost `compost/`)
| | V97 | V98 |
|---|---|---|
| Lupa, WOW (índex mín./mediana; 1 = gra com lluny) | 0,41 / 0,57 | 0,85 / 1,04 |
| Lupa, WOW bilateral | 0,42 / 0,59 | 0,85 / 0,96 |
| Lupa, MGN | 0,30 / 0,57 | 0,75 / 0,88 |
| Anell fosc a 1–9 px, NRGF (P01) | −0,19 | −0,015 |
| Anell fosc a 1–9 px, RHEF (P02) | −0,15 | −0,05 |
| Anell fosc, RHEF local 30° (P02d, punt 3) | −0,45 | −0,13 |
| Compost, dalt (75–135°) | clot −4 % a 1–3 px | pla (±0,5 %) |

## 6. El que queda (i per què)
- **Al primer píxel de dada, les RHEF locals (45, 46) i els ACHF azimutals (47–49)** encara surten una mica més foscos a dalt-esquerra i baix-esquerra (fins a −0,13 a −0,18 en rang; al compost, un −2–3 % a baix-esquerra). La dada lineal no hi té cap dèficit (d9: les primeres files són un 0,5–2,5 % més clares que la tendència, per la curvatura del perfil). **Hipòtesi:** aquests dos operadors comparen píxels al mateix radi SOLAR, i prop de la Lluna la corona observada és un 1–3 % més fosca que al mateix radi solar més lluny de la Lluna (la Lluna tapa llum que l'òptica hi escamparia: l'ombra de la llum difusa). És a tots els fotogrames; no es pot treure amb selecció ni sense un model de llum difusa. Queda declarat.
- **La banda sense dada de dalt** (0–5,7 px): sense textura, amb el to continu (compost pla, ±0,5 %). És on no hi ha cap fotograma net.
- **Biaix dels fotogrames curts a brillantor mitjana** (+25 %, `D12_GUANY_PER_FOTOGRAMA.json`): probablement el pes LDIC que depèn del valor del mateix píxel prop del terra de soroll. A la brillantor del limbe les classes quadren a ±1–2 %. Pendent d'estudiar a l'apilat (no és de la V98).
