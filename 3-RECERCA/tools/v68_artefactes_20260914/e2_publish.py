from pathlib import Path
import json,subprocess,hashlib
R=Path.cwd();O=R/'output/v68_artefactes_20260914'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
qa=json.loads((O/'D6_integrity.json').read_text());gate=(O/'E2_photoshop_gate.txt').read_text().strip();assert qa['PASS'] and gate.startswith('OBRE ')
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V68_V67_ARTIFACTS_20260914'
src=O/'V68_native.psb';dst=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V68.psb');assert not dst.exists()
assert sha(src)==qa['sha256'];subprocess.run(['/bin/cp','-c',str(src),str(dst)],check=True);assert sha(dst)==qa['sha256']
rep=dict(path=str(dst),sha256=qa['sha256'],bytes=dst.stat().st_size,source=str(src));(O/'E2_publish.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print('PUBLISHED',dst,flush=True)
