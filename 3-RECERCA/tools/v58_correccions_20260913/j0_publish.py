from common58 import *
import shutil,datetime
claim();qa=json.loads((O/'I4_final_QA.json').read_text());assert qa['PASS'];pkg=json.loads((O/'I2_package.json').read_text());src=Path(pkg['path']);dst=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V58.psb');assert not dst.exists();assert sha(src)==pkg['sha256']
with src.open('rb') as fi,dst.open('xb') as fo:shutil.copyfileobj(fi,fo,16*1024*1024)
s=sha(dst);assert s==pkg['sha256'];save('J0_publish.json',dict(path=str(dst),sha256=s,bytes=dst.stat().st_size,layers=30,size=[10551,7506],depth=16,profile='Adobe RGB (1998)',published_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),PASS=True));print('PUBLISHED',dst,s,flush=True)
