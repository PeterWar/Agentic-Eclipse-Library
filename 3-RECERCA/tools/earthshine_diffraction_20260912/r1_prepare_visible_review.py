"""User-requested Photoshop checkpoint: byte-exact V48/V49 review copies.
No new photographic correction; no original or live unsaved document is saved.
"""
from photoshop_review_api import *
import shutil,hashlib
base=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors')
rows=[]
for version,sha in [('V48','48715be427ebd5ea654eeea746e0a295201f9f0a354e4f5e37fbf40df47443a5'),('V49','21896b1b40bfd2ba0c13aec07491bebbaf05f4f91dbe2698957e392b3928bc2d')]:
    src=base/f'Earthshine_{version}.psb';dst=OUT/f'REVISIO_{version}_sense_modificar.psb';assert not dst.exists()
    with src.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
    # APFS clone when available, otherwise normal byte copy.
    p=subprocess.run(['/bin/cp','-c',str(src),str(dst)],capture_output=True,text=True)
    if p.returncode:
        assert not dst.exists();shutil.copyfile(src,dst)
    with dst.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
    gate=subprocess.run(['/bin/zsh',str(ROOT/'research/tools/capes_totals_v14/porta_photoshop.sh'),str(dst)],capture_output=True,text=True,check=True)
    assert gate.stdout.strip().startswith('OBRE '),gate.stdout
    rows.append(dict(version=version,source=str(src),review_copy=str(dst),sha256=sha,bytes=dst.stat().st_size,byte_exact=True,Photoshop=gate.stdout.strip()));save('R1_visible_review.json',dict(method=__doc__,copies=rows,source_or_camera_raw_changes=False))
    print(version,gate.stdout.strip(),flush=True)
print('PREPARED EXACT REVIEW COPIES',flush=True)
