from pathlib import Path
import json,hashlib,shutil,datetime
R=Path('/Users/USUARI/Downloads/Eclipse 2026');O=R/'output/v57_integracio_20260913'
assert json.loads((R/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_CAPES_TOTALS_V57_20260913'
q=json.loads((O/'D2_final_QA.json').read_text());assert q['PASS']
v=json.loads((O/'D0_package.json').read_text());assert v['PASS']
assert json.loads((O/'D3_visual_review.json').read_text())['integration_reviewed']
t=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V57.psb');assert not t.exists()
with t.open('xb') as w,Path(v['path']).open('rb') as f:shutil.copyfileobj(f,w,16*1024*1024)
with t.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
assert sha==v['sha256'];rep={**v,'path':str(t),'published_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(O/'E0_publish.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2));print(json.dumps(rep),flush=True)
