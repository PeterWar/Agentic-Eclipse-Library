"""Finish receipt stage after optional psutil was unavailable; no image processing."""
from photoshop_api import *
import hashlib,os
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()
def rec(p):
    p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
claim();p=HERE/'delivery_manifest.json';m=json.loads(p.read_text());assert len(m['new_RAW_inputs'])==6
# Initial manifest accidentally classified old remapped .npy paths as RAW;
# replace that section with the actual CR3 files used by the renderer.
raw=[]
for n in range(2973,2979):raw.append(rec(Path('/Users/USUARI/Desktop/Eclipse determinista/0-ENTRADES/VIXEN-R6III/totalitat')/f'572A{n}.CR3'))
assert all(x['path'].endswith('.CR3') for x in raw);m['new_RAW_inputs']=raw
m['code_and_outputs']=[rec(Path(x['path'])) if Path(x['path']).parent==HERE else x for x in m['code_and_outputs']]
m['code_and_outputs'].append(rec(Path(__file__)))
m['record_stage_note']='Initial recorder stopped before release because optional psutil absent; resumed using system ps. RAW receipt paths corrected from remapped arrays to six actual CR3. No source processing repeated.'
p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
other=[]
for line in subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines():
    parts=line.strip().split(None,1)
    if len(parts)!=2:continue
    pid=int(parts[0]);cmd=parts[1]
    if pid not in [os.getpid(),os.getppid()] and str(HERE) in cmd and '.py' in cmd and 'python' in cmd.lower():other.append(dict(pid=pid,cmd=cmd))
assert not other,other
handoff=ROOT/'.coordination/HANDOFF_2026-09-11_EARTHSHINE_SOURCE_COMPOSITOR.md'
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## Earthshine source compositor — RELEASED · {datetime.now(timezone.utc).isoformat()}\n\n- claim_id: CODEX_EARTHSHINE_RECONSTRUCTION_20260911 · serial_writes: RELEASED\n- Candidat C5, no PSB nou; pilot superior59,37%/0,180px vs fontV45 91,22%/0,379px. Regressions3/6, altres sectors i CameraRaw exacte pendents. Goal actiu, continuar sense nova confirmació.\n- Informe: {OUT / "RESULTAT.md"}\n- Handoff explícit: {handoff}\n- Manifest: {p}\n- Original PSB SHA0af484cb… intacte, documents79/140 oberts saved=false, tresXMP exactes. Cap maquinari/Git ni bypass de CUA. Renders i AppleEvents propis acabats; zero processos propis pendents després de sortir aquest registrador.\n')
claim();(ROOT/'.coordination/claim.lock/owner.json').unlink();(ROOT/'.coordination/claim.lock').rmdir();print('RECEIPTS_CORRECTED_AND_RELEASED',flush=True)
