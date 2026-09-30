from common58 import *
import datetime,os,subprocess
claim();assert (O/'J2_authorities.json').exists() and (O/'J1_UI_verified.json').exists();pub=json.loads((O/'J0_publish.json').read_text());assert sha(pub['path'])==pub['sha256']
for row in json.loads((O/'H10_sources_unchanged.json').read_text()):assert sha(row['path'])==row['sha256']
workers=[]
for line in subprocess.check_output(['ps','-axo','pid=,ppid=,command='],text=True).splitlines():
 q=line.strip().split(None,2)
 if len(q)<3:continue
 pid=int(q[0]);cmd=q[2]
 if pid in [os.getpid(),os.getppid()]:continue
 if ('v58_correccions_20260913/' in cmd and any(x in cmd for x in ['python','osascript','porta_photoshop.sh'])) or cmd.strip()=='osascript':workers.append(line)
assert not workers,workers
now=datetime.datetime.now(datetime.timezone.utc).isoformat();lock=R/'.coordination/claim.lock';owner=json.loads((lock/'owner.json').read_text());assert owner['claim_id']=='CODEX_V58_SIX_CORRECTIONS_20260913';rec=dict(time=now,status='RELEASED',claim_id=owner['claim_id'],own_workers_remaining=workers,Photoshop='Published V58.psb left open, saved=true, Moon selected; CUA full-canvas screenshot verified',source_and_product_sha256_reverified=True,handoff=str(R/'.coordination/HANDOFF_2026-09-13_CODEX_CAPES_TOTALS_V58.md'))
with (R/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} · RELEASED · {owner["claim_id"]}\n\nV58 lliurada i oberta a Photoshop: 30 capes, fitxer desat, earthshine seleccionat. Reobertura i readback 0 DN16; 108 canals editats verificats. Fonts V57 de Pere i Earthshine V56, i SHA del producte, reverificats abans d’alliberar. Zero processos propis pendents. Handoff: {rec["handoff"]}. Línia lluminosa de la base i un candidat estel·lar ambigu declarats, judici visual de Pere pendent. S’allibera només el claim propi.\n')
save('J3_release.json',rec);assert json.loads((lock/'owner.json').read_text())['claim_id']==owner['claim_id'];(lock/'owner.json').unlink();lock.rmdir();assert not lock.exists();print(json.dumps(rec,ensure_ascii=False),flush=True)
