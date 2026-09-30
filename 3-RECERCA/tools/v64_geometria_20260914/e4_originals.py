from pathlib import Path
import json,hashlib
R=Path.cwd();O=R/'output/v64_geometria_20260914';rows=[]
items=[('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V63.psb','f3dc9afbc8e7e90aefbd853f8436975b4442d105d51aef2389b80a9bab277e0c'),('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V56.psb','edee45ad76f08f8450beed3e85ed0d226eb0b1e11347478d2e998d74281ce12e')]
for path,expected in items:
 p=Path(path)
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 rows.append(dict(path=path,sha256=h,expected=expected,exact=h==expected));print(path,h==expected,flush=True)
(O/'E4_external_originals.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n');assert all(r['exact'] for r in rows)
