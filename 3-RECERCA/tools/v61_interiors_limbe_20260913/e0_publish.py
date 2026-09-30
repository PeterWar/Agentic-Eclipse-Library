from common61 import *
import subprocess,datetime
claim();qa=json.loads((O/'D5_final_integrity.json').read_text());assert qa['PASS'];assert 'OBRE' in (O/'D6_photoshop_gate.txt').read_text();assert json.loads((O/'C4_smart_retention.json').read_text())['PASS'];p=O/'V61_native.psb';assert sha(p)==qa['sha256'];target=SRC.with_name('V61.psb');assert not target.exists();subprocess.run(['/bin/cp','-c',str(p),str(target)],check=True);assert sha(target)==qa['sha256'];sources=json.loads((O/'A0_sources.json').read_text());receipt={}
for key,j in sources.items():
 h=sha(j['path']);assert h==j['sha256'],key;receipt[key]={'path':j['path'],'sha256':h,'unchanged':True}
save('E0_publish.json',{'path':str(target),'sha256':qa['sha256'],'bytes':qa['bytes'],'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_files':receipt,'alignment_status':'restored and common rigid transform validated','blue_limb_status':'not fully resolved; only compositing-alpha correction validated'});print(target)
