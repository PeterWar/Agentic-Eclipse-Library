from common58 import *
import datetime
claim();pub=json.loads((O/'J0_publish.json').read_text());assert sha(pub['path'])==pub['sha256'];assert json.loads((O/'I4_final_QA.json').read_text())['PASS'];names=['V58_work.psb','V58_overlap_work.psb','V58.psb','V58_protected_work.psb','V58_protected_fixed_work.psb','V58_final.psb','V58_enabled_work.psb','V58_delivery.psb','V58_reviewed_work.psb'];rows=[]
for n in names:
 p=O/n;assert p.is_file() and not p.is_symlink();assert p.resolve().parent==O.resolve();assert p.resolve()!=Path(pub['path']).resolve();row={'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)};rows.append(row);print('receipted',n,flush=True)
rec=dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Only disposable full PSB intermediates created by this V58 task. Keep immutable userV57 snapshot, final V58_ready QA copy, published V58, all arrays, code, reports and native previews.',files=rows,bytes_reclaimed=sum(r['bytes'] for r in rows));save('J4_intermediate_inventory.json',rec)
for row in rows:Path(row['path']).unlink()
save('J4_cleanup_completed.json',dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),all_listed_intermediates_removed=True,bytes_reclaimed=rec['bytes_reclaimed'],retained=['V57_Pere_input.psb','V58_ready.psb',pub['path'],'all scientific arrays and receipts/nativeTIFFs']));print('RECLAIMED',rec['bytes_reclaimed'],flush=True)
