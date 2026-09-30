from common import *
claim();assert sha(V55)==V55_SHA;products=[]
for name in ['Earthshine_V55.psb','Earthshine_V54.psb','Earthshine_V53.psb']:
 p=CI/name;products.append(dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size))
paths=[ROOT/'AGENTS.md',ROOT/'CLAUDE.md',ROOT/'.coordination/CLAUDE_STATUS.md',ROOT/'.coordination/HANDOFF_2026-09-13_CODEX_EARTHSHINE_V55.md',Path('/Users/USUARI/Desktop/Eclipse 2026/IA/ACTIVE.json')];auth=[]
for i,p in enumerate(paths):
 dst=OUT/'receipts'/f'authority_{i}_{p.name}';dst.write_bytes(p.read_bytes());auth.append(dict(path=str(p),sha256=sha(p),snapshot=str(dst)))
inputs=[]
for row in frames():
 for key,hkey in [('file','sha256'),('detector_file','detector_sha256')]:
  h=sha(row[key]);assert h==row[hkey];inputs.append(dict(path=row[key],sha256=h))
for p in [OLD/'arrays/B11_repeatable_all.npz',OLD/'arrays/D10_candidate_rgb.npy',OLD/'D11_exact_retention.json',ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz']:
 inputs.append(dict(path=str(p),sha256=sha(p)))
save('A0_freeze.json',dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),products=products,authorities=auth,inputs=inputs,native_cache_frames=88,geometry='Frozen from V55; no recentering, FOV or resampling of product'))
print('FROZEN',len(inputs),'input assets',flush=True)
