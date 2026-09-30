from pathlib import Path
import json,hashlib,subprocess,datetime
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';q=json.loads((O/'D14_integrity.json').read_text());assert q['PASS'];assert json.loads((O/'D12_native_candidate_check.json').read_text())['PASS'];assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V65_PERE_GEOMETRY_STARS_20260914';gate=(O/'E1_photoshop_gate.txt').read_text().strip();assert gate.startswith('OBRE ');p=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V65.psb');assert not p.exists();subprocess.run(['/bin/cp','-c',q['path'],str(p)],check=True)
with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
assert h==q['sha256'];m=dict(path=str(p),sha256=h,bytes=p.stat().st_size,native_source=q['path'],time=datetime.datetime.now(datetime.timezone.utc).isoformat(),gate=gate);(O/'E0_publish.json').write_text(json.dumps(m,ensure_ascii=False,indent=2));print(m,flush=True)
