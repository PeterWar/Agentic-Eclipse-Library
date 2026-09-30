from pathlib import Path
import json,hashlib,subprocess,datetime
R=Path.cwd();O=R/'output/v62_prominencies_20260913'
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V62_V61_PROMINENCES_20260913'
def sha(p):
 with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
qa=json.loads((O/'E0_integrity.json').read_text());assert qa['PASS']
src=Path(qa['path']);dst=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V62.psb')
assert not dst.exists();assert src.stat().st_size==qa['bytes']
subprocess.run(['cp','-c',str(src),str(dst)],check=True)
h=sha(dst);assert h==qa['sha256']
earth=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V56.psb')
he=sha(earth);assert he=='edee45ad76f08f8450beed3e85ed0d226eb0b1e11347478d2e998d74281ce12e'
p=O/'E1_publish.json';assert not p.exists();p.write_text(json.dumps(dict(path=str(dst),sha256=h,bytes=dst.stat().st_size,staging=str(src),time=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_V61_unchanged=qa['user_V61_unchanged_SHA'],independent_Earthshine_V56_unchanged=he),ensure_ascii=False,indent=2)+'\n')
print('PUBLISHED',dst,h,flush=True)
