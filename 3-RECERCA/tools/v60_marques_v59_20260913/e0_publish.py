from common60 import *
import os,shutil,datetime
claim();qa=json.loads((O/'D6_final_QA.json').read_text());assert qa['PASS'];source=O/'V60_ready.psb';target=SRC.parent/'V60.psb';assert not target.exists();assert sha(SRC)==qa['V59_source_unchanged_sha256'];assert sha(source)==qa['product_sha256']
tmp=target.with_name('V60.tmp.psb');assert not tmp.exists()
with source.open('rb') as src,tmp.open('xb') as dst:shutil.copyfileobj(src,dst,8<<20)
assert sha(tmp)==qa['product_sha256'];os.rename(tmp,target)
rep={'path':str(target),'sha256':qa['product_sha256'],'bytes':target.stat().st_size,'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'V59_unchanged':qa['V59_source_unchanged_sha256'],'layers':31,'photoshop_gate':qa['Photoshop'],'native_readback_max_DN16':qa['native_readback_max_DN16']};save('E0_publish.json',rep);print('PUBLISHED',target,flush=True)
