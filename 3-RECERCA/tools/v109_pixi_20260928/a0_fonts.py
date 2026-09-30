"""Freeze source identities and inventory; originals read-only."""
from pathlib import Path
import sys,json,hashlib,datetime
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'4-RESULTATS/v109_pixi_20260928'
sys.path.insert(0,str(ROOT/'3-RECERCA/tools/v71_marques_v69_20260916'))
from psb69 import PSB
claim=json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())
assert claim['claim_id']=='CODEX_V109_PIXI_I_ARTEFACTES_20260928'
sources={'base':ROOT/'1-PHOTOSHOP/V108.psb','export':Path.home()/'Downloads/V108.psb','pixi':Path.home()/'Downloads/V108-Pixi.tif'}
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sources':{}}
for key,p in sources.items():
 s=p.stat(); h=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
 rec={'path':str(p),'size':s.st_size,'mtime_ns':s.st_mtime_ns,'sha256':h}
 if p.suffix=='.psb':
  ps=PSB(str(p)); rec.update(width=ps.width,height=ps.height,depth=ps.depth,channels=ps.channels,layers=ps.layers)
 report['sources'][key]=rec
 print(key,s.st_size,h,flush=True)
assert report['sources']['base']['sha256']=='23be3edcf050441788122fe82eb4808009b2b81557862c3cde6054d8bac12ff2'
with (OUT/'FONTS.json').open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2)
