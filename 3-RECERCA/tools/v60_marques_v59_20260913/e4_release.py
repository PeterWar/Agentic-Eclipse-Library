from common60 import *
import os,subprocess,datetime
claim();pub=json.loads((O/'E0_publish.json').read_text());assert (O/'E3_authorities.json').exists();assert 'saved=true' in (O/'E1_open.txt').read_text();assert sha(Path(pub['path']))==pub['sha256'];assert sha(SRC)==pub['V59_unchanged']
workers=[]
for line in subprocess.check_output(['ps','-axo','pid=,ppid=,args='],text=True).splitlines():
 q=line.strip().split(None,2)
 if len(q)<3:continue
 pid,ppid=int(q[0]),int(q[1]);cmd=q[2]
 if pid in [os.getpid(),os.getppid()]:continue
 if str(T) in cmd or str(O) in cmd or 'v60_marques_v59_20260913/' in cmd:workers.append({'pid':pid,'ppid':ppid,'command':cmd})
assert not workers,workers
# Remove only this task's reproducible, closed intermediate; retain immutable V59 and verified V60_ready.
work=O/'V60_work.psb';w=json.loads((O/'D2_work_channels.json').read_text());assert work.is_file() and sha(work)==w['sha256'];removed={'path':str(work),'sha256':w['sha256'],'bytes':work.stat().st_size,'reason':'Owned intermediate superseded by verified native-cache V60_ready and published V60; all source/QA evidence retained'};work.unlink()
now=datetime.datetime.now(datetime.timezone.utc).isoformat();lock=R/'.coordination/claim.lock';owner=json.loads((lock/'owner.json').read_text());assert owner['claim_id']=='CODEX_V60_V59_MARKS_20260913';handoff=R/'.coordination/HANDOFF_2026-09-13_CODEX_CAPES_TOTALS_V60.md';rep={'time':now,'status':'RELEASED','claim_id':owner['claim_id'],'own_workers_remaining':workers,'source_and_product_sha256_reverified':True,'Photoshop':'V60 left open,31layers,saved=true; native CUA full-canvas verified','handoff':str(handoff),'blue':'Unchanged, pending','removed_own_intermediate':removed}
with (R/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} · RELEASED · {owner["claim_id"]}\n\nV60 lliurada i oberta a Photoshop,31capes,desada. Verd i cremallera lila corregits a la composició;RGB lunar original exacte. Blau sense correcció simple validada,pendent. Photoshop/readback0DN16;25canals editats verificats,128exactes. V59 i producte reverificats abans d’alliberar. Zero processos propis pendents. Retirat només V60_work.psb reproduïble; V59 immutable i V60_ready verificat conservats. Handoff: {handoff}.\n')
save('E4_release.json',rep);assert json.loads((lock/'owner.json').read_text())['claim_id']==owner['claim_id'];(lock/'owner.json').unlink();lock.rmdir();print('RELEASED',flush=True)
