"""Final preservation audit, manifest and explicit release of only our lock."""
from common import *
import sys,subprocess,os,ast
claim();a=json.loads((OUT/'A0_freeze.json').read_text());verified=[]
for row in a['inputs']:
    assert sha(row['path'])==row['sha256'],row['path'];verified.append(row['path'])
assert sha(V53)==V53_SHA
v49=CI/'Earthshine_V49.psb';assert sha(v49)=='fc22af4660c7ac7aeb10a1433f1c159a91968fed70646c4b9200bb5bf7748366'
cl=next(x for x in a['authorities'] if x['path'].endswith('CLAUDE_STATUS.md'));assert sha(cl['path'])==cl['sha256']
pub=json.loads((OUT/'E4_publish.json').read_text());assert sha(pub['path'])==pub['sha256'];assert json.loads((OUT/'E3_readback.json').read_text())['PASS'];assert json.loads((OUT/'D1_injection.json').read_text())['all_pass'];assert not json.loads((OUT/'D2_retention.json').read_text())['lost_triples']
active=json.loads(Path('/Users/USUARI/Desktop/Eclipse 2026/IA/ACTIVE.json').read_text());assert active['current_earthshine_product']['sha256']==pub['sha256'];assert Path(active['formal_worktree_handoff']).exists()
doc=json.loads((OUT/'F0_documentation.json').read_text());assert Path(doc['report']).exists() and Path(doc['handoff']).exists()
for row in doc['authorities_after']:assert sha(row['path'])==row['sha256'],row['path']
for p in HERE.glob('*.py'):ast.parse(p.read_text())
# No worker remains. Ignore this releasing coordinator and its shell ancestor.
ps=subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True);own={os.getpid(),os.getppid()};workers=[]
for line in ps.splitlines()[1:]:
    q=line.strip().split(None,2)
    if len(q)==3 and str(HERE) in q[2] and int(q[0]) not in own:workers.append(line)
assert not workers,workers
import numpy,scipy,psd_tools
save('F1_final_audit.json',dict(PASS=True,inputs_unchanged=len(verified),raw67_unchanged=True,V53_unchanged=True,V49_unchanged=True,Claude_status_unchanged=True,authorities_consistent=True,product_sha256=pub['sha256'],own_background_workers=0,runtime=dict(python=sys.version,executable=sys.executable,numpy=numpy.__version__,scipy=scipy.__version__,psd_tools=psd_tools.__version__),visual_review='Full native Photoshop canvas and lunar1:1 plus same x2 exposure views inspected. Subtle detail contrast; no new obvious limb ring. Existing exterior/background appearance inherited, unchanged.'))
# Additional inputs actually used after A0; these hashes freeze current state.
extra=[SRC/'full_sampler_delta/C0_pre_camera_raw_full.psd',SRC/'full_sampler_delta/C0_pre_camera_raw_rgb.npy',SRC/'full_sampler_delta/C1_camera_raw.psd',SRC/'A0_native_samples_572A2978.npz',
ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy',ROOT/'output/earthshine_reconstruction_20260911/A1_camera_raw_descriptor.bin',ROOT/'output/earthshine_v50_limb_20260912/E2_appearance.json',ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz',ROOT/'output/v38_20260908/4-rebuts/A1_franja_font.json',
Path('/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/019_VIXEN_CIENCIA_20260827T212404Z/4-rebuts/F1.3_registre.json'),ROOT/'research/tools/encaix_sony/psb_utils.py',ROOT/'research/tools/capes_totals_v14/porta_photoshop.sh',ROOT/'research/tools/earthshine_native_psf_20260911/d1_camera_raw.py']
save('F1_additional_inputs.json',dict(files=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in extra]))
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
save('F2_release.json',dict(status='RELEASED',claim_id=CLAIM,time=now,handoff=doc['handoff'],report=doc['report'],product=pub['path'],own_background_workers=0,note='Recorded while holding our lock immediately before sealing manifest and removing only our owner.json and empty claim directory. Releasing coordinator exits after successful removal. No new thread or message sent to Claude.'))
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} — RELEASED — EARTHSHINE V54\n\nClaim {CLAIM}. V54 publicada i verificació final PASS:74 entrades incloent67 RAW intactes; V53 i V49 exactes; CLAUDE_STATUS intacte;25 capes originals i màscara/alfa exactes. Photoshop26 capes i3DN16. Les quatre vies s\'han executat i documentat; millora fotogràfica40–64 limitada, DHS i els detectors absoluts contradictoris continuen oberts. Handoff explícit {doc["handoff"]}. Zero workers propis; aquest coordinador acaba després de retirar només el seu owner i directori buit. SERIAL_WRITES RELEASED.\n')
files=sorted([p for p in OUT.rglob('*') if p.is_file()]+[p for p in HERE.rglob('*') if p.is_file() and p.name!='delivery_manifest.json'])
files += [Path(pub['path']),CI/'Earthshine_V54_REBUT.md',Path(doc['handoff']),ROOT/'.coordination/CODEX_STATUS.md']+[Path(x['path']) for x in doc['authorities_after']]
rows=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in files]
manifest=dict(campaign='Earthshine V54 detail20260913',created_utc=now,scope='Files and source identities, not full physical recovery. C branch refused; D branch product. All limits in RESULTAT.md.',source_V53_sha256=V53_SHA,files=rows)
with (HERE/'delivery_manifest.json').open('x') as f:json.dump(manifest,f,ensure_ascii=False,indent=2);f.write('\n')
claim();lock=ROOT/'.coordination/claim.lock';(lock/'owner.json').unlink();lock.rmdir();assert not lock.exists()
print('SEALED',len(rows),'FILES; RELEASED; V54',pub['sha256'],flush=True)
