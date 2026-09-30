"""Self-contained final scientific/photographic record, after native QA/publish."""
from common import *
claim();get=lambda n:json.loads((OUT/n).read_text());pub=get('E4_publish.json');qa=get('E3_readback.json');inj=get('B14_repeatable_injections.json');ret=get('D11_exact_retention.json');assert qa['PASS'] and not ret['lost_triples'] and inj['all_scene_pass'] and inj['all_detector_no_amplification'];assert sha(pub['path'])==pub['sha256']
hand=ROOT/'.coordination/HANDOFF_2026-09-13_CODEX_EARTHSHINE_V55.md';report=OUT/'RESULTAT.md';manifest=HERE/'delivery_manifest.json'
source=get('B12_repeatable_external.json')['tiles'];photo=get('D13_photo_retention.json')['tiles'];table=[]
for band in [[16,24],[24,40],[40,64],[64,96]]:
 def avg(rows,c,k):return float(np.mean([q[k] for q in rows if q['band']==band and q['candidate']==c]))
 table.append(f"| {band[0]}–{band[1]} | {avg(source,'baseline','Sony'):.4f} → {avg(source,'repeatable','Sony'):.4f} | {avg(source,'baseline','LROC'):.4f} → {avg(source,'repeatable','LROC'):.4f} | {avg(photo,'V54','Sony'):.4f} → {avg(photo,'D10_photo','Sony'):.4f} |")
text=f'''# Earthshine V55: detall més fidel separant el patró del sensor

13-09-2026. Pere autoritzà treball desatès sobre RGB natiu, patró fix residual, escales/orientacions i, en segon terme, PSF d'estrelles. S'han executat les quatre vies. Es lliura una V55 amb menys contaminació del detector i millor coincidència de textura; no s'afirma una nova resolució angular, recuperació de tot l'últim limbe, màxim matemàtic ni equivalència amb DHS. El judici visual de Pere queda obert.

## Producte i preservació

- Producte: `{pub['path']}`.
- SHA-256: `{pub['sha256']}`; {pub['bytes']} bytes; 10551 × 7506, RGB16, 26 capes.
- Font V54: `79386f21103b49c16638846e51d70fe1c5e9a29d873b31fcdf1f23dc1886852f`, intacta. V53 també exacta; els 88 RAW s'han rehashat contra el registre d'entrada: 88/88 exactes (`F0_inputs_integrity.json`).
- Canvien només els RGB de la capa lunar25 i el seu nom. Les altres25 capes, alfa, màscares, modes, visibilitat, geometria i cromatisme (diferències R−G/B−G) es conserven. Mateix FOV i mostreig de producte. Cap píxel LROC/Sony nou al productor Vixen.
- Cap nova màscara, capa d'anell, retoc pintat, interpolació generativa o deconvolució no identificada. Es conserva el revelat desat com a base; no es reexecuta Camera Raw.

## Què ha millorat i com s'ha mesurat

La comparació següent és la mitjana de correlació en37 finestres2D interiors de192², superposades: no són37 experiments independents. Els controls rotats es calculen de la mateixa manera abans/després. Les correlacions angulars, marques verdes i últim limbe tenen jutges separats als JSON; no se substitueixen per aquesta mitjana favorable.

| Escala (px del producte) | Font Vixen vs Sony independent | Font Vixen vs LROC | Foto V54→V55 vs Sony: retenció |
|---|---|---|---|
{chr(10).join(table)}

La comparació científica de la font exclou Sony/LROC del productor. La foto ampla antiga ja conté Sony: la seva correlació és **retenció**, no corroboració independent. No convertir un increment de correlació en un percentatge de resolució o de detall nou. A8–16 el senyal científic entre trens continua feble; no s'hi fa cap afirmació nova.

El jutge EXACTE heretat de V54 (lineal/log, les9 marques verdes, superior i regions radials, nuls rotats) conserva **92/92** comprovacions; el recompte total passa a {ret['new_triples']}, però l'addicional és exploratori i no una nova estructura declarada (`D11_exact_retention.json`). L'operador detecta6 ones implantades,360 cèl·lules espai/escala, transferència1,0; els patrons purs de detector implantats deixen entre {min(q['residual_ratio'] for q in inj['detector_only']):.3f} i {max(q['residual_ratio'] for q in inj['detector_only']):.3f} de l'error original, sense amplificació (`B14_repeatable_injections.json`).

Les360 injeccions fotogràfiques aparellades conserven transferència1,0 (`D14_differential_injection.json`). **Són proves diferencials condicionals**, amb covariància, guanys de repetibilitat i resposta congelats. L'escena lliure preserva una textura comuna per construcció: aquest PASS sol no prova recuperació. Cal llegir-lo amb els controls de detector i el jutge extern. No és una prova absoluta RAW→Camera Raw natiu.

## Cadena aplicada

1. `a1_native_rgb.py --all`:88 RAW, calibratge natiu R/G1/G2/B, WB i variància WB² pròpies, camps/offsets per color. Els176 plans G1/G2 coincideixen exactament amb les fonts ordinàries prèvies. Captures/respostes nadiues, hashes i transformacions a `native/` i `A1_native_rgb_all.json`.
2. Deriva mesurada4,95 ×26,33px natius, RMS principals9,63/0,46px. El moviment gairebé unidimensional deixa modes mal identificats. Pilot central: patró fix en radiància calibrada amb ridge0,1; error temporal reservat −34,12%, millor que poses permutades (`B0/B1/B2`). No és una nova calibració física de dark/flat.
3. `b3_fpn_full.py G --all67 --robust --hetero --full-error-safe`: problema espacial global1400², cap mosaic. Escena lliure + detector desplaçat, translació bilineal i adjunts comprovats. Fourier16–64 amb faldons12–96; només suport físic lunar i CFA vàlid. Covariància = soroll condicional + dispersió temporal baixa + error quadràtic local per captura (suau32px). La covariància no es resta dels píxels. Els nuisances per captura també usen captures reservades: el test temporal és condicional. Fonts/filtres sempre en Fourier; el gaussià estima errors.
4. `b11_repeatable_detector.py`: dues meitats disjuntes estratificades per exposició i temps. Mateix operador; guanys per5 bandes ×8 orientacions de la potència creuada positiva respecte de potència de senyal+soroll de semidiferència. S'aplica una sola transferència global al detector de totes67 captures. La geometria/covariància/calibratge són compartits; les meitats no són sensors independents. Sortida aplicada: `arrays/B11_repeatable_all.npz`, SHA `644f007478b56dc680b1ef1d44359255d6dbb299f5ccb2ddd56ce93d5438cc2a`.
5. Resposta de pantalla espacial: D8 mesura que el coeficient global extrapolat de l'interior no val prop del limbe. `d10_spatial_response_domain.py` ajusta Photo=β(r)·Gnet+γ(r)·D només amb sectors parells60–435 i banda16–64. β/γ són polinomis de Bernstein de grau2 en r², sis coeficients no negatius, domini igual al radi màxim del suport visible heretat. Cap valor d'extrem imposat; no hi ha màscara nova. Coeficients β=[170,559966;210,222665;0], γ=[124,424770;89,520493;0]. Els zeros són resultat de NNLS. γ(60)=123,21; γ(350)=64,90; γ(435)=16,75; γ(449)=6,60DN16/G. No són controls Camera Raw ni prova de procedència de cada component.
6. V55RGB = V54RGB − arrodonir(γ(r)·correcció_sensor). Mateixa diferència als3 canals, només on l'alfa/màscara heretades són visibles. RGB definitiu `arrays/D10_candidate_rgb.npy`. La base desada, el seu residu de revelat i els detalls no modelats queden preservats. No s'afegeix contrast positiu nou per dissimular el soroll retirat.

## Contorn i Photoshop

El mateix detector radial/arcs de V54 dona RMS global d'arcs69,803→68,583DN16; màxim local237,69→241,48 ja per sobre100 a la base. Canvi màxim del perfil del compost al limbe8,5DN16 (D0 rebutjat arribava289). Els llindars literals2%/monotonia/90% ja fallaven V53/V54: es conserven i es declara la discrepància, no es canvien per forçar PASS. No s'afirma que aquests llindars absoluts passin. `D12_profiles.json` guarda perfils complets i deltes. Inspecció del disc/composició a1:1 i aclarit×2 sense nou halo o costura apreciable; vista sencera conserva els artefactes coronals preexistents aliens a aquest canvi.

Photoshop real: `E2_photoshop_gate.json`. Dos lectors, 26capes, canals editats descomprimits exactes i preservació de25capes (`E1_verify.json`). Readback: màxim {qa['max_full_DN16']}DN16 al llenç i {qa['max_moon_DN16']}DN16 a la Lluna, PASS (`E3_readback.json`). Els documents oberts de Pere, estat desat, document actiu i diàlegs es preserven. El PSB usa merged RAW i canals editats ZIP16.

## Vies negatives, sense esborrar intents

- **RGB:** R conté textura útil, sobretot16–40; GR supera G i RGB no supera GR després de FPN. B és més feble. Escales R1,6431493/B0,8217931 i pesos fotònics congelats sense Sony (`A3/A5/A6`). El trasllat de vermell addicional al revelat (`D3`) provoca7529 píxels fora de rang, radis443,37–457,61: rebutjat abans de desar RGB. Ni clipping ni màscara per obtenir PASS. Aquest senyal de font queda disponible, sense vermell addicional nou aV55.
- **Coeficient fotogràfic constant:** D0 i D6 milloren mitjanes però cadascun perd una comprovació heretada24–40 a green_8. Rebutjats, tot i93 coincidències totals enD0. D8 documenta la resposta espacial que motivà el modelD10; els reservats/jutges no canvien. La successió és exploratòria, sense p-valor formal ni afirmar un reservat mai vist.
- **Estrelles/PSF:**18 intents,3 ajustos locals útils, FWHM2,45–3,91px natius; estrelles útils a6,8–6,9Rsol, cap estrella prop de la Lluna (catàleg mínim6,16Rsol). No extrapolació de PSF lunar validada, cap deconvolució (`C0_stars_psf.json`).
- **Diagnòstics invàlids:** A2 inicial spline amb NaN contaminava l'espectre: substituït per A2b amb suport explícit. RMS FFT de residus B3 posats a zero fora del disc té contaminació de vora i no jutja el limbe. `--full-error` sense guarda deixa62píxels de referència leave-one-out zero: no usar; només `--full-error-safe`. D9 havia normalitzat Bernstein a450px, menys que el suport visible, i extrapolava γ negatiu: no producte; D10 corregeix el domini segons alfa existent. Primera còpia del jutge D4 col·lidia en globals x/y: corregida abans d'obtenir rebut. Primer B11 usava clau exposure inexistent: corregida aexp i ordenació temporal abans de produir meitats.

## Límits i punt de represa

Aquesta és la millor versió qualificada de la campanya; no s'ha demostrat el màxim d'informació possible. Detall complet de l'últim limbe, resolució8–16, PSF espacial i equivalènciaDHS continuen oberts. Les limitacions d'identificació i d'independència impedeixen prometre recuperació addicional amb un altre filtre. La següent millora hauria d'aportar una restricció nova de la mescla/resposta entre trens o informació òptica local, mantenint V55 intacta. No repetir D0/D6 ni afegir una ploma a green_8. Valorar visualmentV55 a la mateixa brillantor queV54.

Reproducció: intèrpret `/Users/USUARI/.venvs/eines-ia-py312/bin/python`; `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2`; scripts sota `{HERE}` i rebuts/arrays sota `{OUT}`. Tots exigeixen claim propi `{CLAIM}` i moltes sortides són exclusives: una futura represa ha d'adquirir claim nou i declarar un directori nou; no rerun a cegues ni importar executables antics. No Git, càmeres/PTP, agents auxiliars o missatges a Claude. Traspàs `{hand}`. Manifest `{manifest}`.

Fonament extern consultat, sense enviar dades fotogràfiques: [Fixsen, Moseley i Arendt2000, self-calibration of arrays](https://arxiv.org/abs/astro-ph/0002260), per la separabilitat condicionada per moviments; [Wronski etal.2019, Handheld Multi-Frame Super-Resolution](https://research.google/pubs/handheld-multi-frame-super-resolution/), per ús conjunt de mostres CFA. LaV55 no implementa ni reivindica la seva superresolució.
'''
with report.open('x') as f:f.write(text)
handtext=f'''# Represa Codex · Earthshine V55 · 13-09-2026

Campanya desatesa de màxim detall acabada amb una millora qualificada del patró del sensor. Les quatre vies RGB/FPN/escales2D/PSF d'estrelles s'han executat; límits científics oberts no es declaren resolts. Judici visual de Pere pendent.

- Producte `{pub['path']}`, SHA `{pub['sha256']}`, {pub['bytes']}bytes,10551×7506RGB16,26capes. V54/V53 i88RAW exactes;25capes + alfa/màscares/cromatisme/geometria preservats, nomésRGB25 i nom nous.
- Informe complet, negatius i reproducció: `{report}`. Manifest `{manifest}`. Codi `{HERE}`. Output `{OUT}`.
- Productor qualificat **B11 → D10**. B11: detector global de67Vixen amb covariància full-safe i repetibilitat per dues meitats, bandes/orientacions Fourier. D10: resposta fotogràfica espacial ajustada a sectors parells, revelat desat fix, sense nova màscara. No recuperació PSF ni rerenderCameraRaw.
- Font Sony independent16–24:0,2872→0,3463;24–40:0,4148→0,5032;40–64:0,7096→0,7541. Foto Sony és retenció:0,8146→0,8439 /0,8493→0,8708 /0,8912→0,8981. No percentatge de resolució.
-92/92 comprovacions heretades preservades.360injeccions condicionals de font i360de transport, transferència1; detectorpur residual0,354–0,733. No prova absoluta RAW→CameraRaw. Mateixos controls, nuls i dades jutjades; repeticions exploratòries reconegudes.
- D0/D6 **rebutjats** perquè perden una coincidència green_8 malgrat millora global. D3vermell rebutjat per7529píxelsfora de rang al limbe. Estrelles massa lluny per validarPSF lunar. A2NaN/B3FFT de residu enmascarat/full-error sense guarda/D9domini450: invàlids o no producte; llegir informe abans de reutilitzar.
- Arcs RMS69,803→68,583; canvi màxim perfil compost limbe8,5DN16. Llindars literals de contorn ja fallenV53/V54: no canviats, noPASSabsolut. No nova recuperació de tot l'últimlimbe ni8–16 niDHS.
- Photoshop real OBRE26capes, doslectors, readbackmàxim{qa['max_full_DN16']}DN16llenç/{qa['max_moon_DN16']}Lluna. Documents dePere preservats. Vistes natives a`vistes/E3_Photoshop_V55_*`.

Arrencada: AGENTS, CLAUDE sencer, estats, IA README→ESTAT→MAPA, informe. Comprovar lock viu; arrel canònica de codi Downloads senseGit; actiusDesktop. No tocar RAW/runs/CameraRaw/originals. No importar executables d'aquesta campanya amb claim vell; nouclaim/output per represa. Només el teu diari. Cap missatge enviat aClaude. Alliberament efectiu aCODEX_STATUS iF3_release.json; aquest document no substitueix el lock.
'''
with hand.open('x') as f:f.write(handtext)
manifest_data=dict(product=pub,source=str(CI/'Earthshine_V54.psb'),source_sha256='79386f21103b49c16638846e51d70fe1c5e9a29d873b31fcdf1f23dc1886852f',report=str(report),handoff=str(hand),status='QUALIFIED_PHOTOGRAPHIC_V55; PERE_VISUAL_REVIEW_PENDING',source_arrays=[dict(path=str(OUT/'arrays'/n),sha256=sha(OUT/'arrays'/n)) for n in ['B11_repeatable_all.npz','D10_candidate_rgb.npy','D10_gamma.npy']],receipts=[dict(path=str(p),sha256=sha(p)) for p in sorted(OUT.glob('*.json'))],code=[dict(path=str(p),sha256=sha(p)) for p in sorted(HERE.glob('*.py'))],limits=['No new resolution or full last-limb recovery claim','Conditional injection and repeated exploratory judges','Sony photographic comparison not independent'])
with manifest.open('x') as f:json.dump(manifest_data,f,ensure_ascii=False,indent=2);f.write('\n')
save('F1_documentation.json',dict(report=str(report),report_sha256=sha(report),handoff=str(hand),handoff_sha256=sha(hand),manifest=str(manifest),manifest_sha256=sha(manifest)))
print('DOCUMENTED',report,flush=True)
