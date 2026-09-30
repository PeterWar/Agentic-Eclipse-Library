"""Publish auditable result and live restart pointers after native delivery."""
from common import *
import shutil,ast
claim();pub=json.loads((OUT/'E4_publish.json').read_text());qa=json.loads((OUT/'E3_readback.json').read_text());assert qa['PASS'];assert sha(pub['path'])==pub['sha256'];assert sha(V53)==V53_SHA
now=datetime.datetime.now(datetime.timezone.utc).isoformat();HAND=ROOT/'.coordination/HANDOFF_2026-09-13_CODEX_EARTHSHINE_V54.md';REPORT=OUT/'RESULTAT.md'
assert not HAND.exists() and not REPORT.exists()
ret=json.loads((OUT/'D2_retention.json').read_text());inj=json.loads((OUT/'D1_injection.json').read_text());prof=json.loads((OUT/'D2_profiles.json').read_text());design=json.loads((OUT/'D1_design.json').read_text())
# Correct a wording error; numeric/fitted/heldout data stay byte-equivalent.
old_design_sha=sha(OUT/'D1_design.json');design['acceptance']=design['acceptance'].replace('independent photographic triples retained','photographic retention triples (not independent) retained')
(OUT/'D1_design.json').write_text(json.dumps(design,ensure_ascii=False,indent=2)+'\n')
save('F0_wording_erratum.json',dict(file='D1_design.json',old_sha256=old_design_sha,new_sha256=sha(OUT/'D1_design.json'),reason='Photographic Sony comparison is retention, not independence; no number, gate, input or fit changed.'))
gains=[v for v in ret['rows'] if v['mode']=='linear' and v['band']==[40,64] and 'heldout' in v['region']]
tab='\n'.join(f"| {v['region'].replace('_heldout','')} | {(v['relative_amplitude']-1)*100:.2f}% | {v['same_structure']:.6f} | {v['old']['Sony']['r']:.6f} → {v['new']['Sony']['r']:.6f} |" for v in gains)
lo=min(v['transfer'] for v in inj['rows']);hi=max(v['transfer'] for v in inj['rows'])
report=f'''# Earthshine V54 · quatre vies executades, reforç fotogràfic limitat

13-09-2026. Ordre de Pere: «executa totes les tasques del handoff i fer una nova versió». Campanya local, un escriptor, cap agent auxiliar ni càmera.

## Resultat lliurat

[Earthshine_V54.psb]({pub['path']}) · **10551 × 7506, RGB16, 26 capes** · {pub['bytes']:,} bytes.

SHA-256: `{pub['sha256']}`.

La V54 reforça aproximadament un **4–5% el contrast de la textura tangencial de 40–64 píxels** a l'interior mesurat del disc. És detall ja present i corroborat. **No s'ha demostrat resolució nova, cràters nous, recuperació de tot l'últim limbe ni equivalència amb el DHS.** El reforç és subtil; judici visual de Pere pendent.

V53 preservada byte a byte: `{V53_SHA}`. 25 capes de la V53 són íntegrament exactes; a la capa lunar només canvien RGB i el nom descriptiu. Geometria, opacitat, barreja, alfa i màscara exactes. Diferències R−G i B−G exactes; píxels amagats exactes. Cap anell afegit, cap retoc de marques, cap canvi de FOV i cap píxel LROC/DHS introduït al producte.

## Les quatre vies del handoff

| Via | Prova efectuada | Resultat i ús |
|---|---|---|
| 1. Ala i deconvolució lineal | Perfil G dels 67 Vixen, sectors de30°, d−80…−5; mescla d'ales gaussianes σ4/8/16/32/64/128 i fons lunar constant/lineal/quadràtic; bins alterns fora d'ajust. Dos inversos Wiener i injecció amb nuclis creuats. | **No promoguda.** Al mateix sector, masses d'ala6,71% i70,21% donen residus reservats51,84 i51,68 unitats G: nucli no identificat. La inversió depèn del fons assumit. El camp de vel revelat no és una PSF calibrada. |
| 2. Soroll i guany per banda | Meitats alternes equilibrades per exposició i meitats temporals; bandes8–16/16–24/24–40/40–64. Max(Wiener regional, garrote k3). | No s'aplica una reducció de detall forta. La confiança de40–64 governa només el petit reforç positiu. La primera prova FFT cartesiana del quadrat complet incorporava la corona brillant i fou refusada: no entra al producte. |
| 3. Selecció temporal per azimut | Vectors Lluna−Sol del registre per fotograma, projectats per azimut; W·exp((distància−màxim)/20px), pesos positius continus;67 Vixen de l'inventari88. | **No promoguda.** Millora local superior però correlació Sony mitjana reservada0,177449 →0,176597. No és superior al conjunt. Calibració i registre previs congelats. |
| 4. Textura40–64 corroborada | Fonts Vixen separades, Sony i LROC com a jutges; nul girat30°…330°, bandes Fourier, marca superior i altres regions; reforç de la font fotogràfica anterior a Camera Raw. | **Promoció fotogràfica limitada.** Màxim8% abans del factor de confiança. Transport diferencial fix fins a l'aparença de Pere; validació injectada i retenció descrites sota. |

L'inventari inclou88 exposicions; els productors lineals nous només usen67 Vixen. La Sony és fora d'aquests productors i serveix de contrast. La fotografia ampla heretada ja conté Sony: les seves comparacions són **retenció**, no independència. El patró fix pot cancel·lar-se entre meitats del mateix sensor; per això no es confon amb soroll total independent ni s'introdueix un terme creuat productor.

## Per què la versió final conserva el revelat desat

La branca C va tornar a executar la recepta coneguda de Camera Raw en documents complets nous. El control identitat contra l'exportació històrica donà **0 DN16**. Tot i això, reavaluar el filtre després d'un canvi petit de la font alterà la resposta al senyal injectat:0,747–1,131 a40–64. **Branca C refusada; cap PSB lliurat d'aquesta branca.** Els valors sense selecció de banda de C2 es conserven com a diagnòstic i no es fan passar per la porta de la banda del senyal.

La branca D manté els píxels revelats de la V53 i transporta només Δ de la font fotogràfica anterior a Camera Raw amb una pendent global fixa β={design['beta']:.9f}. S'ajusta en sectors parells de30°, r100–435; fora d'ajust, correlació0,960352 i residu36,58 DN16. No s'ajusta amb Sony, LROC, la injecció ni el resultat desitjat. La pendent és una **aproximació empírica de resposta en aquesta banda**, no una reconstrucció dels controls personals de Camera Raw.

`RGB_V54 = RGB_V53 + round(β × Δ_font)`; la mateixa diferència entera a R/G/B. Δ es calcula a la font, no pintant la capa final. La part visible ve només del suport lunar heretat. No es tornen a calcular els termes locals de reducció de soroll que havien fet fallar C.

## Resultats mesurats

Injecció: vuit ones planes d'orientació aleatòria,42–60px,40 DN16 RMS, llavor540915. Confiança congelada. S'aprofita la resposta nativa de la fotografia basal a la mateixa injecció i s'afegeix exclusivament el transport diferencial de la font. **48/48 cel·les, transferència{lo:.6f}–{hi:.6f}, dins0,90–1,10.** És una qualificació del model diferencial fotogràfic, no d'una nova reconstrucció física completa des dels RAW. La injecció polar anterior amb llavor540913 també es conserva; no substitueix aquesta prova d'orientacions cartesians.

**92/92 comprovacions fotogràfiques prèvies retingudes** en lineal/log, contra Sony/LROC i nuls girats;0 perdudes. Són comprovacions superposades, no92 experiments independents. La correlació Sony mitjana reservada0,480005 →0,480023 és pràcticament invariant, no una millora científica significativa.

| Radi en píxels, sectors reservats | Guany d'amplitud40–64 | Correlació V53↔V54 | Correlació amb Sony |
|---|---:|---:|---:|
{tab}

La fila435–449 descriu canvi/retenció del producte, **no** recuperació corroborada de tots aquests píxels. Les bandes més fines no obtenen una afirmació nova de resolució.

## Limbe: comparació lleial i discrepància del handoff

La V53 continua sent la referència fotogràfica acceptada per Pere. S'han executat **literalment** els detectors suggerits, amb la mateixa geometria i per als dos productes. Alguns llindars no passen la mateixa V53: passos de mediana2,56–5,41% al disc; perfil d−3…+8 no estrictament monòton; mínim d0…+8/corona8…14 entre0,594 i0,714. d0 travessa la rampa alfa heretada, i els perfils interiors inclouen textura lunar real. El detector literal no distingeix aquests casos d'un defecte.

**No s'han canviat els llindars, la màscara, la vora ni la V53 per fabricar PASS.** Aquests llindars absoluts queden declarats com a discrepància pendent del handoff. La V54 no es presenta com una nova cura del limbe. El que es comprova és conservació d'aparença, perfils comparats i alfa exacta: canvi màxim de mediana lunar33 DN16 i al perfil compost del limbe56 DN16. Arcs RMS global69,785 →69,803 DN16 (<100); màxim local per radi ja supera100 a la V53 i també es declara al rebut. Revisió visual del llenç sencer i de la Lluna1:1: canvi subtil; sense nou anell evident. El fons exterior heretat no s'ha refet.

## Fitxer i Photoshop real

- Dos lectors: psd-tools i ImageMagick; canals RGB canviats descomprimits i comparats exactament;25 capes i alfa/màscara objectiu exactes.
- `OBRE 10551 px x 7506 px · 26 capes`.
- Exportació real nova, amb recomposició forçada: màxim{qa['max_full_DN16']} DN16 al llenç i{qa['max_moon_DN16']} DN16 a la ROI contra la recomposició pròpia; p99,9={qa['p999_moon']} DN16.
- Documents oberts de Pere, document actiu i preferència de diàlegs preservats. Sense càmeres, PTP, Git ni canvis de maquinari.

[Llenç real]({OUT/'vistes/E3_Photoshop_V54_full.png'}) · [Lluna real1:1]({OUT/'vistes/E3_Photoshop_V54_moon_1a1.png'}) · [Comparació V53/V54 a la mateixa llum×2]({OUT/'vistes/D2_comparacio_1a1.png'}). L'aclariment×2 només és una vista de revisió; el PSB conserva el nivell fotogràfic.

## Represa i reproducció

Codi: `{HERE}`. Runtime: `/Users/USUARI/.venvs/eines-ia-py312/bin/python`, amb `PYTHONDONTWRITEBYTECODE=1`, `OPENBLAS_NUM_THREADS=2`. Els scripts comproven el claim de la campanya i creen sortides sense sobreescriure. **No rellançar-los amb el claim alliberat ni reutilitzar les sortides existents**: qualsevol nova campanya ha d'adquirir el seu claim i crear noves rutes. No importar mòduls de campanyes antigues amb escriptures implícites.

Ordre: A0 congelació → B1 fonts/PSF/soroll → B2 jutge → B3/B4/B5 proves → C0/C1/C2/C3/C4 branca Camera Raw refusada → D1 transport fix → D2 perfils/retenció → E0 paquet/verificació/porta/readback/publicació → F0 documentació i manifest. C4 disposa de reproducció exacta dels48 resultats.

Rebuts clau: `A0_freeze.json`, `B1_design.json`, `B4_psf_pilot.json`, `B5_qualification_checked.json`, `C4_native_injection_band.json`, `D1_design.json`, `D1_injection.json`, `D2_retention.json`, `D2_profiles.json`, `E1_verify.json`, `E2_photoshop_gate.json`, `E3_readback.json`, `E4_publish.json`. `B5_qualification.json` és una sortida inicial superada: els suports buits s'expliciten a la versió `checked`; no són correlacions vàlides.

La dependència d'una inversió de Wiener respecte del nucli i la regularització també es documenta a la [referència oficial de scikit-image](https://scikit-image.org/docs/stable/api/skimage.restoration.html#skimage.restoration.wiener). Les decisions d'aquesta campanya es fonamenten en els arrays locals i les proves, no en aquella referència general.

Les quatre vies queden executades com a proves acotades i la nova versió lliurada. **L'objectiu més ampli d'esgotar tot el detall possible respecte del DHS continua obert.** Un següent avenç físic necessita una restricció externa del nucli òptic, una millor separació del patró fix o noves proves de compatibilitat temporal; no es resol amplificant el vel ni retocant el limbe acceptat.
'''
REPORT.write_text(report)
hand=f'''# Represa Codex · Earthshine V54 · 13-09-2026

Pere demanà executar les quatre vies del handoff de Claude i fer una versió nova. Fet: V54 fotogràfica, avanç limitat de contrast40–64; cap afirmació de resolució nova ni d'equivalència DHS. Judici visual de Pere pendent.

## Autoritat i producte

- Codi canònic sense Git: `{ROOT}`. Actius: `/Users/USUARI/Desktop/Eclipse 2026`.
- Producte: `{pub['path']}`; SHA `{pub['sha256']}`; {pub['bytes']} bytes;10551×7506 RGB16;26 capes.
- Font acceptada V53 exacta: `{V53}`; SHA `{V53_SHA}`. No modificar V49/V51 anotada/V52_Artefactes/V50 refusada.
- Informe autocontingut: `{REPORT}`. Codi: `{HERE}`. Manifest: `{HERE/'delivery_manifest.json'}`.
- El limbe acceptat de V53, alfa/màscares, cromatisme i25 capes exactes. Només RGB lunar + nom descriptiu canvien.

## Resultats i negatives que no s'han de perdre

1. PSF: dos nuclis admissibles6,71%/70,21% d'ala expliquen igual el mateix perfil. Inversió no identificada; proves creuades fallen. No tractar `vel_field.npy` post-CR com una PSF.
2. Soroll: meitats reals per exposició i temporals, bandes Fourier. FFT del quadrat amb corona fora contaminava la Lluna: refusada. Atenuació forta no promoguda. Confiança en40–64 només per reforç positiu limitat.
3. Pes temporal geomètric per azimut no supera globalment el reservat; no promogut.
4. Font fotogràfica pre-CR reforçada: primer es provà reexecutar Camera Raw. Control identitat0DN16, però injecció de la candidata0,747–1,131: **branca C refusada**. Producte final és **D**: revelat desat fix + pendent global β0,814715805 sobre Δ_font. No reconstrucció exacta dels controls de Pere.

Qualificació D:48/48 injeccions de resposta diferencial fotogràfica{lo:.6f}–{hi:.6f};92/92 comprovacions anteriors retingudes (superposades, no independents); contrast40–64 interior+4–5%; mateixa estructura>0,9997. Sony ja és a la foto ampla: retenció, no independència. LROC/DHS només referències, zero píxels al producte.

Photoshop real OBRE26 capes; readback màxim3DN16 llenç iROI. Dos lectors i canals descomprimits exactes. Documents de Pere i estat actiu preservats.

## Discrepància pendent dels detectors literals

Els llindars suggerits al handoff (pas2%, monotonia estricta, mínim d0…8≥90%) **fallen també la V53 acceptada**. No s'han canviat els llindars o la geometria per passar. Informe i `D2_profiles.json` conserven ambdós valors. Arcs RMS global69,785→69,803 (<100), però màxim local per radi>100 ja basal. La V54 preserva el limbe fotogràfic; no declara satisfets aquells llindars absoluts. Revisió del detector abans d'usar-lo com a veredicte, amb criteri físic predefinit i sense reobrir cosmèticament el limbe.

## Protocol de continuació

Llegir AGENTS, CLAUDE complet, estats, IA README→ESTAT→MAPA i aquest informe. Adquirir **claim nou** amb mkdir atòmic després de comprovar propietari; els scripts d'aquesta campanya exigeixen `{CLAIM}` i rebutgen sortides preexistents. Mai importar executables de campanyes antigues amb claims/rutes implícits. Cap càmera/PTP. Cap agent auxiliar usat aquí. Còpies de les autoritats prèvies a `{OUT/'receipts/authorities_before'}`.

Treball de les quatre vies i versió nova completat; detall absolut respecte del DHS encara obert. Cap missatge llançat a Claude. L'alliberament efectiu del claim consta al CODEX_STATUS i a `F2_release.json`; aquesta nota no substitueix comprovar el lock viu.
'''
HAND.write_text(hand)
(CI/'Earthshine_V54_REBUT.md').write_text(f'''# Earthshine V54 · 13-09-2026

{pub['path']}

SHA-256 `{pub['sha256']}` · {pub['bytes']} bytes ·10551×7506 RGB16 ·26 capes.

Reforç subtil de contrast de textura40–64 (+4–5% interior). V53 intacta; alfa/màscara exactes;25 capes exactes. No recuperació completa ni equivalència DHS. Injecció diferencial fotogràfica48/48; retenció92/92 (no independència Sony). Photoshop OBRE26; readback3DN16 llenç iROI. Detectors literals del handoff no compleixen tampoc la V53; discrepància declarada, sense canviar llindars.

Informe: {REPORT}
Represa: {HAND}
''')
paths=[ROOT/'AGENTS.md',ROOT/'CLAUDE.md',ROOT/'research/README.md',Path('/Users/USUARI/Desktop/Eclipse 2026/IA/ACTIVE.json'),Path('/Users/USUARI/Desktop/Eclipse 2026/IA/ESTAT_ACTUAL.md'),Path('/Users/USUARI/Desktop/Eclipse 2026/IA/MAPA_RUTES_I_OUTPUTS.md'),Path('/Users/USUARI/Desktop/Eclipse 2026/IA/Coordinació/HANDOFF_VIGENT.md')]
bd=OUT/'receipts/authorities_before';bd.mkdir(exist_ok=False);backups=[]
for i,p in enumerate(paths):
    dst=bd/f'{i}_{p.name}';shutil.copy2(p,dst);backups.append(dict(path=str(p),backup=str(dst),sha256=sha(p)))
note=f'> **13-09-2026 · Earthshine V54 fotogràfica lliurada.** Quatre vies del handoff executades; reforç de contrast40–64 aproximadament4–5% interior, sense resolució nova ni equivalència DHS. V53 i limbe acceptat preservats;25 capes exactes + RGB lunar, màscares/alfa exactes. Injecció diferencial48/48 i retenció92/92 (Sony fotogràfica no independent). Photoshop/readback PASS màxim3DN16. Detectors literals del handoff fallen també V53: discrepància declarada, cap llindar canviat. Producte `{pub["path"]}`, SHA `{pub["sha256"]}`. Represa `{HAND}`; informe `{REPORT}`. Les notes anteriors són història.\n\n'
for p in [paths[0],paths[1],paths[4],paths[5]]:p.write_text(note+p.read_text())
ag=paths[0].read_text();old='**El traspàs vigent és `.coordination/HANDOFF_2026-09-13_CLAUDE_A_CODEX_EARTHSHINE_DETALL.md`** (Claude → Codex; V53 vigent, limbe resolt, objectiu: detall del disc).'
if old in ag:paths[0].write_text(ag.replace(old,'**El traspàs vigent és `.coordination/HANDOFF_2026-09-13_CODEX_EARTHSHINE_V54.md`** (Codex; V54 fotogràfica, quatre vies executades, detall absolut encara obert). L\'anterior deia: '+old,1))
paths[2].write_text(f'> **13-09-2026 · Earthshine V54:** [resultat de les quatre vies]({REPORT}) i [represa]({HAND}). Millora fotogràfica limitada; negatives i discrepància de detectors preservades.\n\n'+paths[2].read_text())
paths[6].write_text(hand)
active=json.loads(paths[3].read_text());active['previous_earthshine_product_V53']=active['current_earthshine_product'];active['historical_earthshine_task_preV54']=active.get('earthshine_task')
active['phase']='post-eclipse-earthshine-V54-photographic-detail-delivered-DHS-open';active['formal_worktree_handoff']=str(HAND)
active['current_earthshine_product']=dict(path=pub['path'],sha256=pub['sha256'],bytes=pub['bytes'],version=54,layers=26,canvas=[W for W in [10551,7506]],depth=16,source=str(V53),PASS='File/layer preservation, native Photoshop3DN16, differential photographic injection and retention. Not all literal limb detectors or full physical recovery.',report=str(REPORT),handoff=str(HAND),user_feedback='Pere visual review of V54 pending; V53 limb acceptance preserved',open_goal='Absolute lunar detail versus DHS remains open')
active['earthshine_task']=dict(status='FOUR_HANDOFF_ROUTES_EXECUTED; V54_PHOTOGRAPHIC_DELIVERED; USER_VISUAL_REVIEW_PENDING; DHS_EQUIVALENCE_OPEN',completed='Bounded pilots of four routes, negative results preserved; modest source-band photographic promotion with saved appearance fixed.',next_action='Review V54 visually. Further physical recovery requires new independent optical/FPN constraints. Do not rerun failed native CR candidate or mistake literal baseline detector failures for a new V54 limb artifact.',handoff=str(HAND))
active['earthshine_v54_validation']=dict(injection_range=[lo,hi],injection_cells=48,photographic_retention=92,photographic_independence=False,readback_max_DN16=3,new_mask=False,new_resolution_claim=False,literal_handoff_detector_discrepancy=str(OUT/'D2_profiles.json'))
paths[3].write_text(json.dumps(active,ensure_ascii=False,indent=2)+'\n')
save('F0_documentation.json',dict(time=now,report=str(REPORT),handoff=str(HAND),authorities_before=backups,authorities_after=[dict(path=str(p),sha256=sha(p)) for p in paths],V53_exact=True))
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} — V54 LLIURADA — CLAIM ENCARA VIU FINS AL REBUT FINAL\n\nQuatre vies executades. V54 {pub["sha256"]}; reforç40–64+4–5% interior;48/48 injecció diferencial1,003–1,061;92/92 retenció; Photoshop OBRE26 i readback3DN16. V53 i25 capes exactes, alfa/màscara exactes. PSF no identificada, pes temporal sense guany global, branca CR refusada. No resolució nova/DHS. Detectors literals del handoff fallen també V53 i queden explícits, no retocats. Informe {REPORT}; handoff {HAND}. Validació final i alliberament pendents.\n')
for p in HERE.glob('*.py'):ast.parse(p.read_text())
print('DOCUMENTED',flush=True)
