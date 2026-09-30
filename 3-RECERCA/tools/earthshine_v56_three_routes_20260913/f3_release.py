"""Verify published V56 and preservation, then release only this own claim."""
from common import *
import os,subprocess
claim();pub=json.loads((OUT/'E4_publish.json').read_text());doc=json.loads((OUT/'F1_documentation.json').read_text());assert sha(pub['path'])==pub['sha256'];freeze=json.loads((OUT/'A0_freeze.json').read_text());checks=[]
for q in freeze['products']:
 h=sha(q['path']);assert h==q['sha256'];checks.append(dict(path=q['path'],sha256=h,exact=True))
cs=next(a for a in freeze['authorities'] if a['path'].endswith('CLAUDE_STATUS.md'));assert sha(cs['path'])==cs['sha256'];assert json.loads((OUT/'F0_integrity.json').read_text())['all_exact'];assert json.loads((OUT/'E3_readback.json').read_text())['PASS'];assert json.loads((OUT/'E3_visual_review.json').read_text())['PASS']
for field in ['report','handoff','manifest']:assert sha(doc[field])==doc[field+'_sha256'],field
for a in json.loads(Path(doc['manifest']).read_text())['artifacts']:assert sha(a['path'])==a['sha256'],a['path']
for a in json.loads((OUT/'F2_authorities.json').read_text())['rows']:assert sha(a['path'])==a['after_sha256'],a['path']
inv=subprocess.check_output(['ps','-axo','pid=,args='],text=True);workers=[]
for line in inv.splitlines():
 bits=line.strip().split(None,1)
 if len(bits)!=2:continue
 pid=int(bits[0]);args=bits[1]
 if pid not in [os.getpid(),os.getppid()] and 'research/tools/earthshine_v56_three_routes_20260913/' in args and 'python' in args.lower():workers.append(line.strip())
assert not workers,workers;now=datetime.datetime.now(datetime.timezone.utc).isoformat();save('F3_release.json',dict(status='RELEASED',claim_id=CLAIM,time=now,handoff=doc['handoff'],product=pub,own_workers=workers,original_products=checks,raw_integrity_receipt=str(OUT/'F0_integrity.json'),CLAUDE_STATUS_exact=True,manifest_artifacts_verified=True,goal_scope='All three proposed routes tested; useful qualified V56 photographic24-40 contrast increment delivered. No new resolution/full last-limb/DHS claim.'))
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f"\n\n## {now} · RELEASED · EARTHSHINE V56\n\nClaim {CLAIM}. V56 publicada i verificada: les tres vies provades, reforç fotogràfic 24–40 aproximadament 2,4–2,9% dins r435, 93/93 retenció, controls de font/detector/transport i Photoshop PASS dins dels límits declarats. V55/V54/V53 i 88 RAW exactes; 25 capes, alfa/màscares/geometria preservades. Manifest, documents i autoritats verificats. Handoff explícit {doc['handoff']}. Zero workers propis; només aquest coordinador retira el seu owner i directori buit. SERIAL_WRITES RELEASED. Judici visual de Pere i límits de nova resolució, últim limbe i DHS continuen oberts; no formen una promesa de recuperació nova en aquesta entrega.\n")
lock=ROOT/'.coordination/claim.lock';assert json.loads((lock/'owner.json').read_text())['claim_id']==CLAIM;(lock/'owner.json').unlink();lock.rmdir();assert not lock.exists();print('RELEASED ZERO WORKERS',flush=True)
