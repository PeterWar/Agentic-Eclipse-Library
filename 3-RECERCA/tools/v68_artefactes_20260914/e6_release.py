from pathlib import Path
import json,datetime,hashlib,os,subprocess
R=Path.cwd();O=R/'output/v68_artefactes_20260914';lock=R/'.coordination/claim.lock';claim='CODEX_V68_V67_ARTIFACTS_20260914';assert json.loads((lock/'owner.json').read_text())['claim_id']==claim
assert json.loads((O/'E4_readback.json').read_text())['PASS'] and (O/'RESULTAT.md').exists()
jobs=subprocess.check_output(['ps','-eo','pid,command'],text=True)
own=[s for s in jobs.splitlines() if ('python' in s.lower() and 'v68_artefactes_20260914/' in s and int(s.strip().split()[0])!=os.getpid()) or ('osascript' in s and not s.strip().split(None,1)[-1].startswith('/bin/zsh'))]
assert not own,own
now=datetime.datetime.now(datetime.timezone.utc).isoformat();rec=dict(time=now,claim_id=claim,status='RELEASED',handoff=str(R/'.coordination/HANDOFF_2026-09-14_CODEX_CAPES_TOTALS_V68.md'),owned_workers_remaining=0,Photoshop_final='V68.psb open and saved; V67 document59 remains unsaved and untouched')
(O/'E6_release.json').write_text(json.dumps(rec,indent=2)+'\n')
with (R/'.coordination/CODEX_STATUS.md').open('a') as f:f.write(f'\n## {now} · RELEASED · V68\nSERIAL_WRITES released; zero owned workers. V68 opened and saved; full forced native reread 0 DN16. User V67 saved file and unsaved document59 preserved. Handoff: {rec["handoff"]}. Thin exterior bright transition and residual fine pattern remain explicitly qualified.\n')
(lock/'owner.json').unlink();lock.rmdir();print('RELEASED',flush=True)
