"""Record a reviewable V47 with explicit scientific limits; release own claim."""
from validation_common import *
from photoshop_api import jsx
from datetime import datetime,timezone
import shutil,ast,subprocess,os
HERE=Path(__file__).resolve().parent;ia=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');now=datetime.now(timezone.utc).isoformat()
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def rec(p):
 p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
pub=json.loads((OUT/'G6_publish.json').read_text());assert sha(pub['path'])==pub['sha256'];assert json.loads((OUT/'G7_actual_protection.json').read_text())['PASS']
report=OUT/'RESULTAT.md';handoff=ROOT/'.coordination/HANDOFF_2026-09-11_EARTHSHINE_V47.md'
text=f'''# Handoff Earthshine V47 — {now}

**Producte fotogràfic revisable:** `{pub['path']}`. SHA `{pub['sha256']}`. 25 capes RGB16; 24 capes de Pere exactes, màscara física heretada sense canvis, nova capa de detall fi de les fonts. Photoshop OBRE i readback PASS: màxim 4 DN16. V47 oberta per revisar; documents originals 79/140 preservats sense desar.

Informe complet: `{report}`. Cadena i controls: `{HERE/'PIPELINE.md'}`. Manifest: `{HERE/'delivery_manifest.json'}`. Figures: `{OUT/'vistes'}`.

## Decisió i límits

- Es rebutgen els desplaçaments globals de la Lluna inferits de la vora aparent a la ronda anterior: perjudiquen la textura corroborada amb la Sony. V47 usa el registre de textura V45.
- C0: 67 fonts Vixen, sis amb CFA ordinari i validesa contínua, ponderacions temporals iguals entre dos estimadors previs. Compositor de diferències de fonts vàlides, asinh, Poisson 8 px i transició 8–16 px. Sony independent com a jutge, cap textura LROC/DHS introduïda.
- G: conserva l'estructura ampla del revelat anterior, substitueix el detall fi per la font recomposta a tot el rectangle i reaplica Camera Raw. Calibració de to global; cap màscara nova, cercle ni degradat manual. Capa original i retoc manual V46 queden ocults, disponibles.
- V47 millora visualment les dents i manté el to i textura general de Pere. La font original i la corona no s'han sobreescrit. Chroma original exacte abans de quantitzar; màxim 4 DN16 en Photoshop, 0 RGB on la màscara és zero.
- No es declara recuperació completa de tot el llimb ni resolució equivalent a DHS, ni recuperats exactament els sliders històrics Camera Raw. Controls C1/C3 amb regressions explícites; operador C4 passa injecció amb pesos fixos, no tota la cadena RAW.
- D/E són assaigs no promoguts. E tenia un identificador de capa duplicat i fallava la recomposició; G crea una identitat nova i passa. No reusar aquell patró de clonació.

## Represa

L'objectiu global de màxim detall continua actiu, amb una versió concreta ja lliurada. No cal nova confirmació. Primer jutjar el detall final G a les marques verdes amb les captures independents i determinar els límits S/N/llum dispersa. No tornar a fer ajustos globals amb la brillantor del llimb, ni una cerca oberta contra els mateixos jutges. No promoure recuperació només perquè el contorn sigui més suau. Conservar la V47 i el revelat de Pere.

Scripts c0 → g0 → g1 → g2 → g3 → g4 → f0 G4. Inputs i outputs a `{OUT}`; Python `/Users/USUARI/.venvs/eines-ia-py312/bin/python`. Les sortides estan protegides contra sobreescriptura. Cap procés propi pendent al release; cap maquinari/PTP/Git, cap delegació.
'''
handoff.write_text(text)
prior=json.loads((ROOT/'research/tools/earthshine_reconstruction_20260911/delivery_manifest.json').read_text());snap=HERE/'docs_before';snap.mkdir(exist_ok=False);canon=[]
for i,item in enumerate(prior['canonical_after']):
 p=Path(item['path']);assert sha(p)==item['sha256'],('Authority changed',p);shutil.copy2(p,snap/(str(i)+'_'+p.name));canon.append(p)
entry=f'> **11-09-2026 · Earthshine V47 fotogràfica lliurada.** Contorn més regular, detall fi de fonts abans de CameraRaw, sense màscara nova; 24 capes de Pere exactes +1. Photoshop/readback PASS màxim4DN16. Detall complet de l’últim llimb i equivalència DHS no demostrats; goal actiu. Es rebutja el registre global basat en la vora aparent de la ronda anterior. Represa: `{handoff}`.\n\n'
for p in [ROOT/'CLAUDE.md',ROOT/'AGENTS.md',ia/'README.md',ia/'ESTAT_ACTUAL.md',ia/'MAPA_RUTES_I_OUTPUTS.md',ROOT/'research/README.md']:p.write_text(entry+p.read_text())
(ia/'Coordinació/HANDOFF_VIGENT.md').write_text(text)
p=ia/'ACTIVE.json';a=json.loads(p.read_text());a['updated']=now;a['phase']='post-eclipse-earthshine-V47-photographic-reviewable-science-limb-open';a['formal_worktree_handoff']=str(handoff)
a['current_earthshine_product']={**pub,'PASS':True,'PASS_scope':'Photographic limb and preservation; native Photoshop, independent pixel readback','scientific_all_limb_PASS':False,'report':str(report),'handoff':str(handoff),'code':str(HERE)}
a['earthshine_task']=dict(status='V47_PHOTOGRAPHIC_VERSION_DELIVERED_GLOBAL_DETAIL_GOAL_ACTIVE',completed='Reviewable V47, improved visible limb, user style and original pixels preserved, Photoshop gate passed',next_action='Judge final G texture against independent captures; determine measured residual limits before another source change',handoff=str(handoff))
a['earthshine_source_compositor_candidate']['status']='Superseded by V47 photographic delivery; optical-profile global shifts rejected for texture; scientific all-limb recovery still open'
p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
link=ia/'output/earthshine_validation_20260911';assert not link.exists() and not link.is_symlink();link.symlink_to(OUT,target_is_directory=True)
# Final live state and preference checks without altering any original document.
state=jsx('var a=[];for(var i=0;i<app.documents.length;i++)a.push(app.documents[i].id+"|"+app.documents[i].name+"|"+app.documents[i].saved);a.join("\\n");');assert '79|Earthshine_V45_Fonts.psb|false' in state and '140|Earthshine_V46_Detall.psb|false' in state
original=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V46_Detall.psb');assert sha(original)=='0af484cb7f1919900a51267f053467974c57902414258e67f54fe98638d2eb3a'
prefs=Path('/Users/USUARI/Library/Application Support/Adobe/CameraRaw/Defaults');pr=[]
for name in ['Previous.xmp','Preferences.xmp','Clipboard.xmp']:
 p=prefs/name;assert p.read_bytes()==(PREV/'settings_before'/name).read_bytes();pr.append(rec(p))
save('Z0_final_preservation.json',dict(original=rec(original),live_documents=state,camera_raw_preferences_exact=pr))
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
files=[rec(p) for directory in [HERE,OUT] for p in sorted(directory.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
manifest=dict(created=now,status='V47_PHOTOGRAPHIC_DELIVERED; SCIENTIFIC_ALL_LIMB_OPEN',publication=pub,files=files,canonical_after=[rec(p) for p in canon],handoff=rec(handoff),prior_manifest=rec(ROOT/'research/tools/earthshine_reconstruction_20260911/delivery_manifest.json'),source_inputs_receipts=[rec(ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json'),rec(OUT/'C0_temporal_ensemble.json')],scope='Inventory of current code and outputs; inherited/transitive inputs traced through prior manifests, not an independent full RAW reproduction',limitations='See RESULTAT and C1/C3 regressions; C4 fixed-weight operator control only. Historical CameraRaw sliders not exactly recovered.')
(HERE/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print('MANIFEST',len(files),flush=True)
# No long-running own render or solver may survive this explicit handoff.
other=[]
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
 f=line.strip().split(None,1)
 if len(f)!=2:continue
 pid=int(f[0]);cmd=f[1]
 if pid in [os.getpid(),os.getppid()]:continue
 if 'python' in cmd.lower() and 'earthshine_validation_20260911/' in cmd and '.py' in cmd:other.append(dict(pid=pid,cmd=cmd))
assert not other,other
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} — RELEASED — EARTHSHINE V47 LLIURADA, DETALL GLOBAL OBERT\n\nClaim CODEX_EARTHSHINE_VALIDATION_20260911. V47 PSB25capes, originals24 exactes, cap màscara nova; finesa de les fonts abans de CameraRaw, estètica preservada aproximadament. Photoshop OBRE i readback PASS4DN16. OriginalPSB SHA0af484cb… intacte; documents79/140 saved=false, tresXMP exactes. NovaV47 oberta. Registre global de vora aparent rebutjat; C0/C1/C3 amb regressions documentades. Objectiu global continua actiu, cap afirmació de recuperació completa del llimb.\n\nProducte {pub["path"]}; SHA{pub["sha256"]}. Informe {report}. Handoff explícit {handoff}. Manifest {HERE/"delivery_manifest.json"}. Zero processos propis després de sortir el registrador; cap Git, maquinari ni delegació. Allibero només el meu owner.json i directori buit.\n')
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_VALIDATION_20260911';(ROOT/'.coordination/claim.lock/owner.json').unlink();(ROOT/'.coordination/claim.lock').rmdir();print('RELEASED',flush=True)
