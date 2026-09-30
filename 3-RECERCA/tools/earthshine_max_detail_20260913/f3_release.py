"""Final integrity and explicit release of only this claim, with zero workers."""
from common import *
import os,subprocess
claim();pub=json.loads((OUT/'E4_publish.json').read_text());doc=json.loads((OUT/'F1_documentation.json').read_text());assert sha(pub['path'])==pub['sha256'];freeze=json.loads((OUT/'A0_freeze.json').read_text());checks=[]
for z in freeze['products']:
    ok=sha(z['path'])==z['sha256'];assert ok;checks.append(dict(path=z['path'],exact=ok))
cs=next(q for q in freeze['authorities'] if q['path'].endswith('CLAUDE_STATUS.md'));assert sha(cs['path'])==cs['sha256'];assert json.loads((OUT/'F0_inputs_integrity.json').read_text())['all_exact']
for field in ['report','handoff','manifest']:assert sha(doc[field])==doc[field+'_sha256']
inv=subprocess.check_output(['ps','-axo','pid=,args='],text=True);workers=[]
for line in inv.splitlines():
    bits=line.strip().split(None,1)
    if len(bits)!=2:continue
    pid=int(bits[0]);args=bits[1]
    if pid not in [os.getpid(),os.getppid()] and 'research/tools/earthshine_max_detail_20260913/' in args and 'python' in args.lower():workers.append(line.strip())
assert not workers,workers
now=datetime.datetime.now(datetime.timezone.utc).isoformat();rep=dict(status='RELEASED',claim_id=CLAIM,time=now,handoff=doc['handoff'],product=pub,own_workers=workers,original_products=checks,raw_integrity_receipt=str(OUT/'F0_inputs_integrity.json'),CLAUDE_STATUS_exact=True,goal_scope='Four authorized routes investigated; best qualified photographic V55 delivered; no mathematical maximum/new resolution/full-limb/DHS claim')
save('F3_release.json',rep)
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f"\n\n## {now} · RELEASED · EARTHSHINE V55\n\nClaim {CLAIM}. V55 publicada, documentada i qualificada; quatre vies executades amb resultats negatius preservats. Handoff explícit {doc['handoff']}. OriginalsV54/V53exactes, rebut88RAWexactes, CLAUDE_STATUSintacte. Zero workers propis; només aquest coordinador allibera el seu owner/directori buit. SERIAL_WRITES RELEASED. Judici visual de Pere, detall complet de l'últimlimbe iDHS romanen oberts com a límits, sense promesa de màxim matemàtic.\n")
lock=ROOT/'.coordination/claim.lock';assert json.loads((lock/'owner.json').read_text())['claim_id']==CLAIM;(lock/'owner.json').unlink();lock.rmdir();assert not lock.exists();print('RELEASED ZERO WORKERS',flush=True)
