"""Snapshot/update authority, inventory candidate evidence, explicit serial release."""
from photoshop_api import *
import hashlib,shutil,ast,os
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def rec(p):
    p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
claim();now=datetime.now(timezone.utc).isoformat();ia=Path('/Users/USUARI/Desktop/Eclipse 2026/IA')
handoff=ROOT/'.coordination/HANDOFF_2026-09-11_EARTHSHINE_SOURCE_COMPOSITOR.md';report=OUT/'RESULTAT.md'
prior=json.loads((ROOT/'research/tools/earthshine_compatibility_20260911/delivery_manifest.json').read_text())
snap=HERE/'docs_before';snap.mkdir(exist_ok=False)
canon=[]
for i,item in enumerate(prior['canonical_after']):
    p=Path(item['path']);assert sha(p)==item['sha256'],('Authority changed unexpectedly',p)
    shutil.copy2(p,snap/(str(i)+'_'+p.name));canon.append(p)
entry=f'> **11-09-2026 · Candidat Earthshine a l’origen, no PSB nou.** C5 combina 67fontsVixen; pilot superior0,180px vsV45 0,379px, textura40–64 corroborada ambSony. Regressions verdes3/6 i altres sectors pendents; CameraRaw exacte encara no reproduït. Originals intactes; goal actiu, continuació autònoma sense confirmacions. Represa: `{handoff}`. Informe: `{report}`.\n\n'
for p in [ROOT/'CLAUDE.md',ROOT/'AGENTS.md',ia/'README.md',ia/'ESTAT_ACTUAL.md',ia/'MAPA_RUTES_I_OUTPUTS.md']:
    p.write_text(entry+p.read_text())
(ia/'Coordinació/HANDOFF_VIGENT.md').write_text(handoff.read_text())
active=ia/'ACTIVE.json';a=json.loads(active.read_text());a['updated']=now;a['phase']='post-eclipse-earthshine-source-compositor-candidate-no-new-PSB';a['formal_worktree_handoff']=str(handoff)
a['earthshine_source_compositor_candidate']=dict(report=str(report),handoff=str(handoff),candidate=str(OUT/'C5_signed_frequency_compositor.npz'),candidate_field='band8_16',status='CANDIDATE_ONLY; regressions and CameraRaw replay unresolved; goal active',published_new_psb=False,code=str(HERE),preservation=str(OUT/'Z0_preservation.json'))
active.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
index=ROOT/'research/README.md';index.write_text(entry+index.read_text())
link=ia/'output/earthshine_reconstruction_20260911'
assert not link.exists() and not link.is_symlink();link.symlink_to(OUT,target_is_directory=True)
inputs={}
meta=ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json';frames=json.loads(meta.read_text())['frames']
for m in frames:
    # All Vixen sources actually used; Sony judge sources are inventoried below.
    if m['tren']=='vixen':
        p=Path(m['native']['file']);inputs[str(p)]=rec(p)
inputs[str(meta)]=rec(meta)
for p in [ROOT/'research/tools/v45_earthshine_20260910/cau'/x for x in ['vixen_reference.npy','epoch_vixen_3.npz','sony_reference.npy','epoch_sony_A_1.npz','epoch_sony_B_2.npz']]+[ROOT/'output/earthshine_compatibility_20260911/C0_native_profiles.npz',ROOT/'output/earthshine_compatibility_20260911/B1_relative_geometry.json',ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz',ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy',ROOT/'research/tools/v46_earthshine_20260911/V45_live_source.psd',ROOT/'research/tools/v46_earthshine_20260911/cau/live_lunar_rgb_u16.npy']:
    inputs[str(p)]=rec(p)
raw=[]
for m in frames:
    if m['stem'] in [f'572A{n}' for n in range(2973,2979)]:
        p=Path('/Users/USUARI/Desktop/Eclipse determinista/0-ENTRADES/VIXEN-R6III/totalitat')/(m['stem']+'.CR3');row=rec(p);raw.append(row)
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
files=[rec(p) for folder in [HERE,OUT] for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='delivery_manifest.json' and '__pycache__' not in p.parts]
manifest=dict(created_utc=now,claim_id='CODEX_EARTHSHINE_RECONSTRUCTION_20260911',status='CANDIDATE_NOT_PUBLISHED; goal remains active',source_preservation=json.loads((OUT/'Z0_preservation.json').read_text()),inputs_key_not_all_transitive=list(inputs.values()),new_RAW_inputs=raw,code_and_outputs=files,canonical_after=[rec(p) for p in canon],handoff=rec(handoff),source_urls=['https://www.sciencedirect.com/science/article/abs/pii/S1047320312000405','https://community.adobe.com/questions-712/is-there-any-jsx-to-execute-the-auto-tone-of-camera-raw-1072109'],validation='Scientific full-limb PASS absent. See all negative controls and regressions in RESULTAT. No new PSB or final Photoshop gate.')
(HERE/'delivery_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('MANIFEST',len(files),'artifacts',len(inputs),'key inputs',len(raw),'RAW',flush=True)
# All tracked rendering/Photoshop exec sessions finished before this stage.
# Check no other process is running a script in this task directory.
other=[]
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
    fields=line.strip().split(None,1)
    if len(fields)!=2:continue
    pid=int(fields[0]);cmd=fields[1]
    if pid in [os.getpid(),os.getppid()]:continue
    if str(HERE) in cmd and '.py' in cmd and 'python' in cmd.lower():other.append(dict(pid=pid,cmd=cmd))
assert not other,other
status=ROOT/'.coordination/CODEX_STATUS.md'
with status.open('a') as f:f.write(f'\n\n## Earthshine source compositor — RELEASED · {datetime.now(timezone.utc).isoformat()}\n\n- claim_id: CODEX_EARTHSHINE_RECONSTRUCTION_20260911 · serial_writes: RELEASED\n- Candidat C5, no PSB nou; pilot superior59,37%/0,180px vs fontV45 91,22%/0,379px. Regressions3/6, altres sectors i CameraRaw exacte pendents. Goal actiu; continuar sense nova confirmació.\n- Informe: {report}\n- Handoff explícit: {handoff}\n- Manifest: {HERE / "delivery_manifest.json"}\n- Original PSB SHA0af484cb… intacte, documents79/140 oberts saved=false, preferènciesXMP exactes. Cap maquinari/Git; cap bypass de CUA. Tots els renders i AppleEvents propis acabats; zero processos propis pendents després de sortir aquest registrador.\n')
claim();(ROOT/'.coordination/claim.lock/owner.json').unlink();(ROOT/'.coordination/claim.lock').rmdir();print('RELEASED',flush=True)
