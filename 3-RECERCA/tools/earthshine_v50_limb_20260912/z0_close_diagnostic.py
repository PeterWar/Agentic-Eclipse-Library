"""Close the unqualified V50 campaign without promoting an image."""
from common50 import *
from datetime import datetime,timezone
from PIL import Image,ImageDraw
import tifffile,subprocess,gc
start=json.loads((OUT/'A0_start.json').read_text());source=Path(start['source']);assert sha(source)==start['sha256'];assert not source.with_name('Earthshine_V50.psb').exists()
for row in start['authorities']:assert sha(row['path'])==row['sha256'],row['path']
for row in json.loads((OUT/'E0_plan.json').read_text())['preferences']:assert sha(row['path'])==row['sha256'],row['path']
# A full-canvas diagnostic accompanies every detailed probe shown in the report.
a=tifffile.imread(V49/'A1_Pere_actual.tif');assert a.shape[:2]==(7506,10551) and a.dtype==np.uint16
rgb=a[...,:3].copy()
if a.shape[-1]==4:
 with tifffile.TiffFile(V49/'A1_Pere_actual.tif') as tf:associated=[int(x) for x in tf.pages[0].extrasamples]==[1]
 if associated:
  for y in range(0,7506,128):rgb[y:y+128]=np.rint(np.clip(a[y:y+128,:,:3].astype(float)*65535/np.maximum(a[y:y+128,:,3,None],1),0,65535)).astype(np.uint16)
views=[]
for title,key in [('V49 revisada · original','original'),('PROVA REFUSADA · font lineal','physical_delta'),('PROVA REFUSADA · resta òptica','pupil_delta')]:
 if key!='original':rgb[Y0:Y0+N,X0:X0+N]=np.load(OUT/f'E2_{key}_composite.npy')
 im=Image.fromarray((rgb[::6,::6]>>8).astype(np.uint8));im.thumbnail((1000,712));panel=Image.new('RGB',(1000,748),'#242424');panel.paste(im,(0,36));ImageDraw.Draw(panel).text((16,10),title,fill='white');views.append(panel)
sheet=Image.new('RGB',(3000,748),'#242424')
for i,im in enumerate(views):sheet.paste(im,(i*1000,0))
sheet.save(OUT/'COMPARACIO_LLENC_PROVES_REFUSADES.jpg',quality=94);del a,rgb;gc.collect()
report=OUT/'RESULTAT_V50_NO_VALIDADA.md';handoff=ROOT/'.coordination/HANDOFF_2026-09-12_V50_NO_VALIDADA.md';now=datetime.now(timezone.utc).isoformat()
text=f'''# V50 no validada — V49 revisada preservada

{now}

**No s'ha aconseguit la correcció final demanada. No s'ha creat Earthshine_V50.psb.** Les proves òptiques continuen introduint irregularitats i franges; no s'han promogut ni maquillat amb una màscara.

La referència estètica continua sent `{source}`: SHA-256 `{sha(source)}`, {source.stat().st_size} bytes, 10551 × 7506 RGB16, 26 capes. Fitxer exacte respecte de l'arrencada. No s'han modificat els RAW, les capes originals, les màscares de Pere ni les preferències Camera Raw. Les dues proves natives només han obert còpies pròpies i les han tancat; abans i després hi havia zero documents oberts.

## Resultats que sí queden mesurats

- **A1/A2, dispersió multiescala en verd natiu:** 21 camps sense censura, 5 preses entrenen i les altres reserven sis èpoques. Model positiu σ2/4/8/16/32 px, pesos 0,101689/0,045383/0,008158/0,005749/0,001450; total 0,162430. Predictor amb els fotons de l'altre verd CFA, sense remostrejar la radiància observada. Els últims sis píxels redueixen el residu temporal en 22,86–33,32%; la banda −40…−6 millora en les sis èpoques. És coherència temporal condicionada, **no una PSF identificada ni una correcció fotogràfica validada**. Comparteix calibració/FPN; el control girat, la injecció i el jutge Sony d'aquest model no s'han completat.
- **B0, nucli estel·lar:** 20/24 ajustos acceptats sobre fotons verds natius de 572A2978/2979/2996, amb integració de píxel. Percentils 16/50/84 del sigma geomètric: 0,875/1,005/1,247 px. Mesura condicionada a les ales A1, no PSF efectiva universal de l'apilat.
- **B1–B3:** separar Sol/Lluna per inversa regularitzada i després amb cinc captures conjuntes produeix soroll i residus negatius/grans a la frontera. 120+800 iteracions no resolen la misspecificació. **Refusats**, no continuar iterant el mateix model com si fos una cura.
- **C0/C1, apilat complet:** inversió solar positiva amb exterior 2D propi per inici/final; evita assumir una corona estàtica o un exterior radial lineal. El fit temporal C1 redueix RMS en sectors reservats 69,38→26,82 i als últims sis píxels 14154,71→828,11 G. Malgrat això, tots dos conserven un halo compartit. Demostra de nou que acord temporal no equival a desaparició de l'artefacte.
- **D0, pupil·la física alternativa:** 90 mm, escala mesurada 2,1494813525884373 arcsec/px, 550 nm i seeing nominal 0,97 px. Substitueix les ales gaussianes; **no se sumen Airy i A1**. Exterior solar 2D positiu. Millora la franja ampla però deixa residus ambdós signes i anell irregular. La PSF efectiva de l'apilat, els moviments, l'ocultació i la contribució exterior al retall no estan prou qualificats. **Refusat**.
- **D1, geometria diagnòstica:** el màxim de derivada del compost complet difereix de l'antic F4 en mediana +0,404 px, i varia entre meitats. Això no és una mesura inequívoca del contorn físic; no s'ha aplicat cap canvi de radi, centre o màscara al producte.
- **E0–E2, Photoshop real:** dues còpies passen pel mateix descriptor Camera Raw històric. Una refà la font amb l'apilat lineal i l'altra aplica D0. La primera enfosqueix massa la cara (mediana −2568 DN16 al nucli) i conserva halo; la segona crea un anell fosc/granulat, amb 22322 píxels retallats al rang de representació en la variant delta. **Cap de les dues és V50**.
- **Correspondència amb el revelat de Pere:** E2 ajusta una sola corba monòtona global del replay històric als píxels V49 desats. Sectors imparells reservats: error absolut mediana 11,68, p95 38,27, p99 49,55 DN16. És una aproximació molt estreta d'aparença, **no recuperació dels controls exactes de Camera Raw**. Els nusos queden a E2_appearance.json i poden estalviar repetir aquesta feina.
- **E3, altre contrafactual:** compensar el canvi global de resposta abans de restar no resol el llimb; deixa excursions positives grans. La prova separada de suport mesurat només existeix com a NPY/PNG diagnòstic. **Ni geometria ni màscara promogudes**.

## Vistes

![Llenç sencer: original i dues proves refusades]({OUT/'COMPARACIO_LLENC_PROVES_REFUSADES.jpg'})

![Detall de la prova òptica refusada, amb nou anell]({OUT/'E2_pupil_delta_moon.png'})

## Abast de la validació i represa

No hi ha PASS de recuperació de tot el llimb, ni d'absència d'halos, ni equivalència amb DHS. Tampoc s'ha executat una porta Photoshop de lliurament d'un PSB V50 inexistent. Els fitxers PSD E0/E1 són sondes amb composició arxivada; **no són productes per editar ni versions lliurades**.

S'atura aquesta família de proves perquè la verificació visual les refusa; no per falta d'autorització. La instrucció de Pere de continuar autònomament continua vigent. Una altra temptativa necessita una hipòtesi distinta i una prova curta que pugui refutar-la abans de generar més variants. Punt no resolt: operador físic per fotograma que distingeixi la Lluna del Sol canviant als últims píxels, amb PSF efectiva/registre/ocultació qualificats i alternativa vàlida als llargs censurats. El desplaçament del màxim de derivada D1 no s'ha de convertir directament en un canvi de radi.

Conservar l'aspecte V49 desat; usar E2 com a resposta global aproximada si una nova font arriba a superar les portes. No reprendre els vells perfils radials amb exterior lineal, les cinc curtes sorolloses B3, els paràmetres C1 només perquè baixen un residu, o les màscares E3. No fer una V50 només per satisfer la numeració.

Codi: `{HERE}`. Rebuts, camps i sondes: `{OUT}`. Manifest amb hashes: `{HERE/'delivery_manifest.json'}`. Represa anterior, amb ablacions de Camera Raw i font exacta: `.coordination/HANDOFF_2026-09-12_V49_PERE_REVELAT_I_LLIMB.md`.
'''
report.write_text(text)
handoff.write_text(text)
(HERE/'REPRESA.md').write_text(f'# Represa V50 no validada\n\nLlegir `{handoff}`. V49 original preservada. No V50 ni font òptica promoguda.\n')
summary=f'> **12-09-2026 · V50 demanada, no validada; V49 revisada preservada.** A1/A2 milloren residus temporals, però els models òptics i les dues proves natives Photoshop introdueixen encara halos/irregularitats. Cap V50, radi, màscara o correcció nova promoguda. V49 SHA `{sha(source)}` exacta; Camera Raw intacte. Corba global E2 aproxima el revelat desat amb p95 reservat 38,27 DN16, sense identificar els controls. Resultat pendent, no completat. Represa `{handoff}`; informe `{report}`. Les notes anteriors són història.\n\n'
for row in start['authorities']:
 p=Path(row['path'])
 if p.suffix=='.md':p.write_text(summary+p.read_text())
active=Path(start['authorities'][2]['path']);v=json.loads(active.read_text());v['updated']=now;v['phase']='post-eclipse-V50-unqualified-V49-Pere-preserved';v['formal_worktree_handoff']=str(handoff);v['paths']['latest_earthshine_diagnostic_manifest']=str(HERE/'delivery_manifest.json');v['earthshine_v50_attempt']=dict(request='Autonomous validated V50 limb correction',status='NOT_ACHIEVED',new_PSB=False,original_V49_sha256=sha(source),report=str(report),source_correction_promoted=False,mask_or_geometry_promoted=False,native_probe_files_only=True,appearance_match_heldout_p95_DN16=38.265215905210425);active.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
save('Z0_preservation.json',dict(time=now,original_V49_exact=True,sha256=sha(source),V50_exists=False,CameraRaw_preferences_exact=True,photoshop_probes_closed=True,goal_achieved=False,authorities_updated=[x['path'] for x in start['authorities']]))
files=[p for root in [HERE,OUT] for p in root.rglob('*') if p.is_file() and p.name!='delivery_manifest.json']+[handoff]
manifest=dict(created=now,status='DIAGNOSTIC_ONLY_NOT_QUALIFIED',source=str(source),source_sha256=sha(source),new_PSB=False,report=str(report),handoff=str(handoff),artifacts=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in files],authorities=[dict(path=row['path'],bytes=Path(row['path']).stat().st_size,sha256=sha(row['path'])) for row in start['authorities']])
(HERE/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
status=ROOT/'.coordination/CODEX_STATUS.md'
with status.open('a') as f:f.write(f'\n## V50 no validada — RELEASED · {now}\n\n- claim_id: {CLAIM}\n- Campanya tancada amb resultat NOT_ACHIEVED; V49 revisada SHA {sha(source)} exacta.\n- Cap V50, font, màscara o geometria nova promoguda. Dues sondes natives tancades; preferències exactes.\n- A1/A2 només coherència temporal; E2 p95 de resposta global 38,27 DN16. Pilots òptics refusats visualment.\n- Represa: {handoff}\n- serial_writes: RELEASED. Zero processos de càlcul/Photoshop propis en segon pla; aquest escriptor finalitza després d’alliberar el lock.\n')
owner=ROOT/'.coordination/claim.lock/owner.json';assert json.loads(owner.read_text())['claim_id']==CLAIM;owner.unlink();owner.parent.rmdir();print('NOT_ACHIEVED; ORIGINAL EXACT; CLAIM RELEASED;',len(files),'artifacts',flush=True)
