"""Record the bounded diagnostic, preservation, current restart point and release."""
from joint_common import *
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import ast,subprocess,os
HERE=Path(__file__).resolve().parent;IA=Path('/Users/USUARI/Desktop/Eclipse 2026/IA');now=datetime.now(timezone.utc).isoformat()
def rec(p):
    p=Path(p)
    with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h)
def write_json(p,a):p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
pres=json.loads((OUT/'Z0_preservation.json').read_text());oldcanon=pres['canonical_before']
for a in oldcanon:assert rec(a['path'])['sha256']==a['sha256'],('Authority changed',a['path'])
for a in [pres['publication_unchanged']]+pres['originals']+pres['camera_raw_preferences_exact']:assert rec(a['path'])['sha256']==a['sha256'],('Original or preference changed',a['path'])
js='var a=[];for(var i=0;i<app.documents.length;i++)a.push(app.documents[i].id+"|"+app.documents[i].name+"|"+app.documents[i].saved);a.join("\\n");'
state=subprocess.check_output(['osascript','-e','tell application id "com.adobe.Photoshop"\ndo javascript '+json.dumps(js)+'\nend tell'],text=True).strip()
assert state==pres['live_documents'],state
assert not any('C0_V48_disk_test' in a for a in state.splitlines())
save('Z1_after_native_preservation.json',dict(PASS=True,created=now,publication=pres['publication_unchanged'],originals=pres['originals'],camera_raw_preferences=pres['camera_raw_preferences_exact'],live_documents=state,scope='V46/V47/V48 and preferences rehashed after native visibility exports; source93 hashes already verified in Z0. No original saved/closed; own comparison document closed.'))
handoff=ROOT/'.coordination/HANDOFF_2026-09-11_EARTHSHINE_JOINT_I_MUNTATGE_V48.md';assert not handoff.exists()
report=OUT/'RESULTAT.md';plan=HERE/'REPRESA.md';pub=pres['publication_unchanged']
text=f'''# Handoff — V48 preservada; model per captura i muntatge — {now}

**Producte vigent:** `{pub['path']}`, SHA `{pub['sha256']}`. Cap V49 publicada. L’objectiu de recuperar el llimb continua actiu. Pere ha aclarit que les visibilitats modificades del document1297 eren només una inspecció; la V48 desada continua sent la referència estètica. La instantània viva d’aquesta ronda és arxivística, no una nova preferència.

Informe `{report}`. Represa acotada `{plan}`. Manifest `{HERE/'delivery_manifest.json'}`. Arrel de codi Downloads; arrel d’actius Desktop. Sense Git, maquinari ni agents nous.

## Resultats i límits

- Model implementat de Lluna comuna i Sol mòbil: primer dues èpoques, després8 captures d’ajust i4 de predicció del nou model. La calibració anterior utilitzava les captures: no és holdout complet de RAW.
- A2 corregeix la integració4×4 de l’ocultació amb àrea píxel/polígon convergent. A4 detecta eixamplament del mesurador de perfils i calibra sigma de graella1,4275159 amb un fantoma. Cap d’aquestes proves identifica la PSF física real de totes les captures.
- B6, últim model: convergeix, però deixa1.119 valors negatius,543 en píxels íntegrament lunars, i prediccions irregulars. No es promou. B5 no és estimació conjunta d’ales òptiques, només una prova amb escenes congelades.
- **Rectificació conceptual:** la màscara heretada a V48 és l’encaix fotogràfic V44 ajustat a la resposta tonal de Pere09, amb validesa de font. No és només una màscara d’ocultació física. C1 la relaciona amb `join_coverage.npy` a1 DN16; radi d’àrea455,935 versus453,544 de la silueta òptica.
- C0/C1: quatre exports natius sobre còpia pròpia separen la font lunar alternativa i LROC visibles sota la font V48. Reforcen part de la franja; retirar-les no resol el vel i altera lleugerament la barreja interior. RGB de la font, CameraRaw i màscares originals intactes. Baseline native vsV48 esperada màxim3 DN16; recomposició d’una sola font màxim1 DN16.
- C2: aplicar suport geomètric al conjunt lunar deixa r<435 exacte, però crea un **anell negre**. Rebutjat, no convertir-lo en una màscara nova o una resta manual.

## Continuació autoritzada

Qualificar la resposta per captura al CFA natiu, separant el seu mostreig del que afegeixen el remapat i la mesura polar. Començar amb una època i la partició declarada a REPRESA. No ampliar la inversió a totes les preses llargues sense qualificar aquest operador; no inferir vores de l’última mostra no saturada. No tornar a la translació global de la vora que perjudicava textura, ni a una força de deconvolució escollida pel resultat visual.

Preservació: fonts93 exactes aZ0; V46/V47/V48 i tres XMP rehash després dels exports aZ1. Documents79/140/1297 continuen saved=false,1275 saved=true. `C0_V48_disk_test.psb` és còpia exacta de V48 i no conté les variants: es van exportar a TIFF des d’un document propi tancat sense desar. No hi ha procés de càlcul ni document propi obert al release. Cap porta Photoshop de producte nou invocada, perquè no s’ha produït cap candidat nou.
'''
handoff.write_text(text)
entry=f'> **11-09-2026 · V48 vigent; model per captura i muntatge diagnosticats.** B6 convergeix però no qualifica la recuperació del llimb. A2/A4 corregeixen errors numèrics del prototip. La màscara heretada és un encaix fotogràfic ajustat a Pere09, no només ocultació física. Retirar fonts superposades no resol tot el vel; retallar amb geometria crea un anell negre. CapV49. V48 desada continua referència; canvis vius només eren inspecció de Pere. Represa `{handoff}` i `{plan}`. Objectiu global actiu.\n\n'
canon=[ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'ACTIVE.json',IA/'ESTAT_ACTUAL.md',IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md',IA/'Coordinació/HANDOFF_VIGENT.md',ROOT/'research/README.md']
oldprefix='> **11-09-2026 · V48 intacta; inversió òptica estàtica rebutjada.**'
for p in [ROOT/'CLAUDE.md',ROOT/'AGENTS.md',IA/'ESTAT_ACTUAL.md',IA/'README.md',IA/'MAPA_RUTES_I_OUTPUTS.md',ROOT/'research/README.md']:
    s=p.read_text();assert s.startswith(oldprefix),(p,s[:100]);p.write_text(entry+s.split('\n\n',1)[1])
(IA/'Coordinació/HANDOFF_VIGENT.md').write_text(text)
p=IA/'ACTIVE.json';a=json.loads(p.read_text());a['updated']=now;a['phase']='post-eclipse-earthshine-V48-preserved-joint-model-and-composition-diagnostic';a['formal_worktree_handoff']=str(handoff)
a['earthshine_task']=dict(status='V48_PRESERVED; JOINT_MODEL_NOT_PROMOTED; GLOBAL_DETAIL_GOAL_ACTIVE',completed='Joint lunar/solar scene pilot, converged numerical occultation and profile-operator probes, native composition diagnostics; no final recovery claim',next_action='Qualify per-capture native CFA forward sampling and censored response; do not promote geometric display clipping; see REPRESA.md',handoff=str(handoff))
a['earthshine_joint_diagnostic']=dict(status='DIAGNOSTIC_ONLY_NO_NEW_PRODUCT',report=str(report),code=str(HERE),last_model=str(OUT/'B6_profile_calibrated_joint.json'),judge=str(OUT/'B7_profile_calibrated_review.json'),native_composition=str(OUT/'C1_composition_review.json'),rejected_geometric_display=str(OUT/'C2_geometric_support_probe.json'),new_product=False,all_limb_recovery_PASS=False,display_join_is_not_pure_physical_mask=True,V48_saved_disk_is_style_reference=True)
write_json(p,a)
link=IA/'output/earthshine_joint_20260911';assert not link.exists() and not link.is_symlink();link.symlink_to(OUT,target_is_directory=True)
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
files=[p for directory in [HERE,OUT] for p in sorted(directory.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
with ThreadPoolExecutor(max_workers=3) as pool:inventory=list(pool.map(rec,files))
write_json(HERE/'delivery_manifest.json',dict(created=now,status='V48_PRESERVED; JOINT_AND_COMPOSITION_DIAGNOSTIC; GLOBAL_GOAL_ACTIVE',publication=pub,files=inventory,canonical_before=oldcanon,canonical_after=[rec(p) for p in canon],handoff=rec(handoff),prior_manifest=pres['prior_manifest'],inputs=pres['consumed_sources_exact'],scope='No new photographic product. Byte-exact V48 working copy and native TIFF diagnostics only. No native RAW reinjection or final independent recovery PASS.'))
other=[]
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
    f=line.strip().split(None,1)
    if len(f)==2 and int(f[0]) not in [os.getpid(),os.getppid()] and 'python' in f[1].lower() and 'earthshine_joint_20260911/' in f[1] and '.py' in f[1]:other.append(line)
assert not other,other
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} — RELEASED — V48 PRESERVADA, MODEL PER CAPTURA I MUNTATGE\n\nClaim {CLAIM}. PROGRÉS: model conjunt implementat i convergent; integració de píxel i mesurador de perfils qualificats numèricament. B6 no promogut: negatius i prediccions irregulars. Diagnòstic natiu C0/C1 identifica capes lunars alternatives i màscara d’encaix fotogràfic, no només física. C2 geomètric crea anell negre i queda rebutjat. Cap V49. V48 desada és referència; Pere aclareix que les visibilitats obertes eren només inspecció.\n\nHandoff explícit {handoff}; informe {report}; manifest {HERE/"delivery_manifest.json"}. Fonts93 exactes; originals V46/V47/V48 i XMP rehash després de Photoshop, documents originals sense canvis de saved. Zero processos de càlcul ni documents propis oberts; només aquest registrador acaba ara. Objectiu global actiu. Allibero owner propi i directori buit.\n')
claim=ROOT/'.coordination/claim.lock';assert json.loads((claim/'owner.json').read_text())['claim_id']==CLAIM
(claim/'owner.json').unlink();claim.rmdir();print('RELEASED',len(inventory),'files; V48 unchanged; goal active',flush=True)
