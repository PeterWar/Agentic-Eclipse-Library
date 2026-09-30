from pathlib import Path
import json,datetime,os,subprocess
R=Path('/Users/USUARI/Downloads/Eclipse 2026');O=R/'output/v57_integracio_20260913';lock=R/'.coordination/claim.lock';claim=json.loads((lock/'owner.json').read_text());assert claim['claim_id']=='CODEX_CAPES_TOTALS_V57_20260913'
assert (O/'F2_authorities.json').exists()
# Exclude this launcher and this process. Native Photoshop remains open as the user's deliverable.
rows=subprocess.check_output(['ps','-axo','pid=,ppid=,command='],text=True).splitlines();workers=[]
for line in rows:
 parts=line.strip().split(None,2)
 if len(parts)<3:continue
 pid=int(parts[0]);cmd=parts[2]
 if pid in (os.getpid(),os.getppid()) or 'release.py' in cmd:continue
 if 'v57_integracio_20260913/' in cmd and ('python' in cmd or 'osascript' in cmd or 'porta_photoshop.sh' in cmd):workers.append(line)
assert not workers,workers
now=datetime.datetime.now(datetime.timezone.utc).isoformat();rec=dict(time=now,status='RELEASED',claim_id=claim['claim_id'],own_workers_remaining=workers,Photoshop='V57.psb left open for Pere',handoff=str(R/'.coordination/HANDOFF_2026-09-13_CODEX_CAPES_TOTALS_V57.md'))
with (R/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n\n## {now} · RELEASED · {claim["claim_id"]}\n\nMuntatge general V57 complet, verificat i obert a Photoshop per a Pere. Zero processos propis de muntatge/QA. Handoff: {rec["handoff"]}. Les 32 capes V42 preservades més tres capes V56; 35 capes, readback 0 DN16, fonts intactes. Línia fina exterior del limbe pendent de revisió del conjunt de filtres. S\'allibera només el claim propi.\n')
(O/'F3_release.json').write_text(json.dumps(rec,ensure_ascii=False,indent=2));assert json.loads((lock/'owner.json').read_text())['claim_id']==claim['claim_id'];(lock/'owner.json').unlink();lock.rmdir();assert not lock.exists();print(json.dumps(rec,ensure_ascii=False))
