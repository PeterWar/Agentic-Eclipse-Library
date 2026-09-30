from pathlib import Path
import json,hashlib,subprocess,datetime
R=Path.cwd();O=R/'output/v63_encaix_contorn_20260913'
q=json.loads((O/'D1_integrity.json').read_text());c=json.loads((O/'C1_foreground_checks.json').read_text())
assert q['PASS'] and c['PASS']
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V63_INNER_ALIGNMENT_LUNAR_CONTOUR_20260913'
p=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V63.psb')
assert not p.exists();subprocess.run(['/bin/cp','-c',q['path'],str(p)],check=True)
with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
assert h==q['sha256'] and p.stat().st_size==q['bytes']
m=dict(path=str(p),sha256=h,bytes=p.stat().st_size,native_source=q['path'],time=datetime.datetime.now(datetime.timezone.utc).isoformat())
(O/'E0_publish.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(m),flush=True)
