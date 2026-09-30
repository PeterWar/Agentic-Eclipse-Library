from pathlib import Path
import json,datetime,os,subprocess,hashlib
R=Path.cwd();O=R/'output/v64_geometria_20260914';lock=R/'.coordination/claim.lock';owner=json.loads((lock/'owner.json').read_text());assert owner['claim_id']=='CODEX_V64_V63_GREEN_GEOMETRY_20260914'
assert json.loads((O/'E3_final_readback.json').read_text())['PASS'];assert (O/'E5_authorities.json').exists()
# All launched native and Python tool sessions have completed. Check no other
# process remains for this round; exclude this release and its invoking shell.
lines=subprocess.check_output(['/bin/ps','-axo','pid=,ppid=,command='],text=True).splitlines();jobs=[]
for line in lines:
 parts=line.strip().split(None,2)
 if len(parts)!=3:continue
 pid,ppid,cmd=int(parts[0]),int(parts[1]),parts[2]
 if pid in [os.getpid(),os.getppid()]:continue
 if 'research/tools/v64_geometria_20260914/' in cmd and 'e6_release.py' not in cmd:jobs.append(dict(pid=pid,command=cmd))
assert not jobs,jobs
now=datetime.datetime.now(datetime.timezone.utc).isoformat();h=R/'.coordination/HANDOFF_2026-09-14_CODEX_CAPES_TOTALS_V64.md';assert h.exists();pub=json.loads((O/'E0_publish.json').read_text())
with (R/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n## {now} · RELEASED · CODEX_V64_V63_GREEN_GEOMETRY_20260914\nV64 saved and open in Photoshop at100%,25root layers, annotations hidden. Full forced native readback0DN16,159channel checks; V63 Pere and independentEarthshineV56 hashes unchanged. Actual CUA AX/screenshot verified. Original unsaved Interiors_V63_validity id4877 remains open unsaved; V62/V63 remain saved and untouched. Coverage improvement delivered for review, not a claim that every exposure is registered within1pixel; native NW opacity threshold residual1.509px qualified. All D4 copy transforms undone; original83 exact and fully masked in lunar ROI. Explicit handoff: {h}. Zero own workers. SERIAL_WRITES released.\n')
receipt=dict(time=now,claim_id=owner['claim_id'],status='RELEASED',handoff=str(h),product=pub['path'],sha256=pub['sha256'],own_workers=jobs,observed_documents=[dict(id=4525,name='V62.psb',saved=True,layers=24),dict(id=4713,name='V63.psb',saved=True,layers=25),dict(id=4877,name='Interiors_V63_validity.psb',saved=False,layers=1),dict(id=5536,name='V64.psb',saved=True,layers=25)],final_document_selected='V64.psb',CUA_confirmed=True)
p=O/'E6_release.json';assert not p.exists();p.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');assert json.loads((lock/'owner.json').read_text())==owner;(lock/'owner.json').unlink();lock.rmdir();print('RELEASED',h,flush=True)
