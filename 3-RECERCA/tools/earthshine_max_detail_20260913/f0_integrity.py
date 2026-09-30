"""Read back preserved inputs; hashes against campaign entry receipts."""
from common import *
claim();f=json.loads((OUT/'A0_freeze.json').read_text());rows=[]
for q in f['products']:
    h=sha(q['path']);rows.append(dict(path=q['path'],sha256=h,exact=h==q['sha256']))
for q in json.loads((OUT/'A1_native_rgb_all.json').read_text())['frames']:
    h=sha(q['raw_path']);rows.append(dict(path=q['raw_path'],sha256=h,exact=h==q['raw_sha256']))
assert all(q['exact'] for q in rows)
save('F0_inputs_integrity.json',dict(rows=rows,all_exact=True,raw_count=88,products=2,time=datetime.datetime.now(datetime.timezone.utc).isoformat()))
print('ORIGINALS',len(rows),'EXACT',flush=True)
