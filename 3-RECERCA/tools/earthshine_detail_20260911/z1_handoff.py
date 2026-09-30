"""Record V48 with scoped evidence and release only this completed writer claim."""
from detail_common import *
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import shutil,ast,subprocess,os

HERE=Path(__file__).resolve().parent
IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA')
now=datetime.now(timezone.utc).isoformat()
def rec(p):
    p=Path(p)
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def write_json(p,a):p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')

pub=json.loads((OUT/'C8_publish.json').read_text())
assert rec(pub['path'])['sha256']==pub['sha256']
assert json.loads((OUT/'Z0_final_preservation.json').read_text())['PASS']
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
prior_path=ROOT/'research/tools/earthshine_validation_20260911/delivery_manifest.json'
prior=json.loads(prior_path.read_text())
canon=[]
for item in prior['canonical_after']:
    p=Path(item['path']);assert rec(p)['sha256']==item['sha256'],('Authority changed',p);canon.append(p)
if ROOT/'research/README.md' not in canon:canon.append(ROOT/'research/README.md')
snap=HERE/'docs_before';snap.mkdir(exist_ok=False)
for i,p in enumerate(canon):shutil.copy2(p,snap/(str(i)+'_'+p.name))
before=[rec(p) for p in canon]

# Documentary clarifications only; no candidate pixels, scores or gates change.
p=OUT/'C0_pre_camera_raw.json';a=json.loads(p.read_text())
a['independence_qualification']='The updated fine-detail source is Vixen only. Retained legacy coarse photographic structure includes both trains; final photograph versus Sony is not independent.';write_json(p,a)
p=OUT/'C4_build.json';a=json.loads(p.read_text());a['method']=a['method'].replace('Reversible V47','Reversible V48');write_json(p,a)
p=OUT/'C6_V48_vs_V47_retention.json';a=json.loads(p.read_text())
a['method']='Photographic retention V48 versus V47, not independent cross-camera validation; inherited labels are explicitly mapped.'
a['limits']=['Shared Sony coarse photographic structure prevents independent cross-camera interpretation','Exploratory historical bands and 11 rotated controls; no new independent discovery threshold','Final source layer checked before mask or solar contamination; original physical mask inherited'];write_json(p,a)

report=OUT/'RESULTAT.md'
handoff=ROOT/'.coordination/HANDOFF_2026-09-11_EARTHSHINE_V48.md'
assert not handoff.exists()
text=f'''# Handoff Earthshine V48 — {now}

**Producte fotogràfic revisable lliurat:** `{pub['path']}`. SHA `{pub['sha256']}`; 25 capes RGB16, 10551×7506. Photoshop/readback PASS màxim 3 DN16. Les 24 capes originals, màscara i geometria queden preservades; les fonts antigues continuen disponibles. V48 oberta, document 1297 desat. Documents originals 79/140 sense desar i intactes; V46/V47 i els 88 RAW verificats per SHA, tres XMP exactes.

Informe: `{report}`. Cadena: `{HERE/'PIPELINE.md'}`. Manifest: `{HERE/'delivery_manifest.json'}`. Vista real Photoshop: `{OUT/'vistes/C4_Photoshop_moon.png'}`.

## Estat i abast

- B0 renova 88 RAW (67 Vixen +21 Sony): radiància CFA ordinària, confiança separada, quatre mostres vàlides no saturades, negatius conservats. Mateixa geometria V45, calibració i rellotge. Sis controls exactes. No nous desplaçaments globals inferits de la vora aparent.
- B1 és font Vixen sola amb compositor fix C0 de V47; B2 és Sony separada. La V48 conserva l'estructura ampla de Pere (ja contenia Sony) i substitueix la part fina amb B1 abans de Camera Raw. Mateixa calibració tonal global congelada; cromaticitat original exacta abans de quantització. Cap retoc espacial ni màscara nova.
- Irregularitat de font: mediana 0,25048→0,22112 px, 21/24 sectors milloren; empitjoren 0°,330°,345°. No és una mesura suficient de resolució. El vel clar residual continua visible.
- B4 entre fonts independents: guany exploratori verd9,24–40 px,lineal/log. Cobertura per referència corregida: suport parcial a l'última franja 435–449 en dos sectors; regressió 120–150°,40–64,log,contra SA8. No recuperació uniforme.
- C6 és retenció fotogràfica, no independència entre trens: 0 pèrdues nominals vsV47 i 1 guany verd9,24–40,lineal. A0/A1 tampoc són prova independent perquè la foto conserva Sony. Els controls rotats i BH són exploratoris; no afirmació astronòmica calibrada.
- B7/B8 barreja directa de88 fonts: no promoguda. B6 moviment durant exposició: hipòtesi nominal, Vixen10s≈3,14–3,80px amb centres modelats. No PSF mesurada, cap deconvolució. Rebut `B6_REJECTED_cross_pointing.json` invàlid per barrejar apuntamentsSony.
- No PASS de recuperació completa del llimb, equivalència DHS ni injecció integral RAW/CFA/CameraRaw. Sliders històrics exactes no recuperats; estètica aproximada amb calibració global ja congelada. Capes Totals intacte.

## Represa acotada, sense nova confirmació

L'objectiu global continua actiu. La següent comprovació útil és mesurar resposta òptica i possible moviment a partir de perfils complets vàlids de preses curtes amb els CFA nous; separar perfil d'il·luminació de registre lunar per textura. Un model nou ha de predir captures reservades i passar una injecció en el domini de la font abans de substituir V48. No repetir l'ajust PSF uniforme refusat, les translacions de vora lluminosa, el mosaic FFT64/pas8 ni cercar paràmetres indefinidament contra els mateixos jutges. Sense guany corroborat, conservar V48 i declarar el límit mesurat.

Sortides `{OUT}`; Python `/Users/USUARI/.venvs/eines-ia-py312/bin/python`; c0→c1→c2→c3→c4→c5 C4→c6→c7→c8. Els scripts rebutgen sobreescriptura del PSB i PSD; llegir PIPELINE abans de reproduir. Noms heretats de B5: V45=fontV47,C5=fontV48. C6 inclou mapa de noms. Zero processos propis pendents al release; cap Git, maquinari o delegació.
'''
handoff.write_text(text)
entry=f'> **11-09-2026 · Earthshine V48 fotogràfica lliurada.** 88 RAW renovats amb radiància CFA ordinària; detall fi Vixen, Sony separada com a jutge. Contorn de font millora en21/24 sectors; estètica aproximada de Pere, 24 capes originals exactes+1, cap màscara nova. Photoshop/readback PASS màxim3DN16. Vel clar i detall de tot l’últim llimb encara oberts; no equivalència DHS. Comparacions de la foto final ambSony són retenció, no independència (la base ampla ja contéSony). Represa: `{handoff}`.\n\n'
for p in [ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'README.md',IA/'ESTAT_ACTUAL.md',IA/'MAPA_RUTES_I_OUTPUTS.md',ROOT/'research/README.md']:
    p.write_text(entry+p.read_text())
(IA/'Coordinació/HANDOFF_VIGENT.md').write_text(text)
p=IA/'ACTIVE.json';a=json.loads(p.read_text());a['updated']=now
a['phase']='post-eclipse-earthshine-V48-photographic-reviewable-science-limb-open';a['formal_worktree_handoff']=str(handoff)
a['current_earthshine_product']={**pub,'PASS':True,'PASS_scope':'File, original layer preservation and native Photoshop recomposition only; partial photographic improvement, not complete limb science','scientific_all_limb_PASS':False,'report':str(report),'handoff':str(handoff),'code':str(HERE)}
a['earthshine_task']=dict(status='V48_PHOTOGRAPHIC_DELIVERED_GLOBAL_DETAIL_GOAL_ACTIVE',completed='All88 ordinary-CFA sources refreshed; V48 file and Photoshop gate passed; original layers and files preserved',next_action='Bounded valid-source PSF/motion diagnosis and independent prediction before any further photographic product; no arbitrary mask or indefinite judge tuning',handoff=str(handoff))
a['earthshine_source_compositor_candidate']['status']='Historical candidate superseded by V48 all67 ordinary-CFA Vixen source; optical-profile global shifts rejected; complete limb science open'
a['earthshine_v48_source']=dict(candidate=str(OUT/'B1_full_native_ensemble.npz'),independent_reference=str(OUT/'B2_sony_reference.npz'),native_inputs=88,source_frames=67,reference_frames=21,judge=str(OUT/'B4_full_source_judge.json'),retention=str(OUT/'C6_V48_vs_V47_retention.json'),all_limb_scientific_PASS=False)
write_json(p,a)
link=IA/'output/earthshine_detail_20260911';assert not link.exists() and not link.is_symlink();link.symlink_to(OUT,target_is_directory=True)

# Inventory hashes include all native caches, diagnostics, actual Photoshop
# exports, rejected experiments and source code; originals traced by Z0/parents.
files=[p for directory in [HERE,OUT] for p in sorted(directory.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
print('HASHING',len(files),'files',flush=True)
with ThreadPoolExecutor(max_workers=3) as pool:items=list(pool.map(rec,files))
manifest=dict(created=now,status='V48_PHOTOGRAPHIC_DELIVERED; SCIENTIFIC_ALL_LIMB_OPEN',publication=pub,files=items,canonical_before=before,canonical_after=[rec(p) for p in canon],handoff=rec(handoff),prior_manifest=rec(prior_path),raw_preservation=rec(OUT/'Z0_final_preservation.json'),source_inventory=rec(OUT/'B0_all_native.json'),scope='Inventory plus RAW hash preservation, source controls and native Photoshop pixel check. Not a full end-to-end independent RAW reproduction or all-limb recovery PASS.',limitations='RESULTAT.md; source regressions explicit. Photo-versus-Sony retention is not independent. No complete RAW injection or measured per-frame PSF.')
write_json(HERE/'delivery_manifest.json',manifest)
other=[]
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
    f=line.strip().split(None,1)
    if len(f)!=2:continue
    pid=int(f[0]);cmd=f[1]
    if pid in [os.getpid(),os.getppid()]:continue
    if 'python' in cmd.lower() and 'earthshine_detail_20260911/' in cmd and '.py' in cmd:other.append(dict(pid=pid,cmd=cmd))
assert not other,other
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:
    f.write(f'\n\n## {now} — RELEASED — EARTHSHINE V48 LLIURADA, DETALL GLOBAL OBERT\n\nClaim CODEX_EARTHSHINE_DETAIL_20260911. PROGRÉS: 88 RAW CFA renovats, fonts67Vixen i21Sony separades; irregularitat21/24 sectors millor, regressions declarades. V48 PSB25capes, originals24 exactes; mateix estil aproximat, màscara i geometria. Photoshop/readback PASS3DN16. SHA{pub["sha256"]}. RAW88/88, V46/V47 i tresXMP exactes; originals79/140 saved=false, V48doc1297 saved=true. Objectiu global actiu; vel i detall de tot el llimb no resolts.\n\nProducte {pub["path"]}. Informe {report}; handoff explícit {handoff}; manifest {HERE/"delivery_manifest.json"}. Zero processos propis pendents després de sortir el registrador; cap Git, maquinari o delegació. Allibero només owner propi i directori buit.\n')
claim=ROOT/'.coordination/claim.lock';assert json.loads((claim/'owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_DETAIL_20260911'
(claim/'owner.json').unlink();claim.rmdir()
print('RELEASED',len(items),'files; V48 delivered, full-limb goal active',flush=True)
