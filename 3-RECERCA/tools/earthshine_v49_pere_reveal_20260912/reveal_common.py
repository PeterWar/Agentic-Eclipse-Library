from pathlib import Path
import json,hashlib,subprocess,numpy as np
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;OUT=ROOT/'output/earthshine_v49_pere_reveal_20260912';CLAIM='CODEX_V49_PERE_REVEAL_20260912'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
SOURCE=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V49.psb')
OLD=ROOT/'output/earthshine_diffraction_20260912/REVISIO_V49_sense_modificar.psb'
SNAP=OUT/'V49_Pere_referencia_20260912.psb';NAME='V49 · graella verda nativa · Camera Raw de Pere'
N=1400;X0=4677;Y0=3077;CX=699.568111973117;CY=699.6475341408573
def save(name,v):(OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def channel(layer,cid):
    w,h=layer.size
    if cid==-2:
        md=layer._record.mask_data;w,h=md.right-md.left,md.bottom-md.top
    for ci,cd in zip(layer._record.channel_info,layer._channels):
        if int(ci.id)==cid:return np.frombuffer(cd.get_data(w,h,16,layer._psd._record.header.version),'>u2').reshape(h,w).astype(np.uint16)
    return None
def jsx(js):
    sc='tell application id "com.adobe.Photoshop"\nwith timeout of 3600 seconds\ndo javascript '+json.dumps(js,ensure_ascii=False)+'\nend timeout\nend tell'
    p=subprocess.run(['osascript','-e',sc],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr.strip())
    return p.stdout.strip()
