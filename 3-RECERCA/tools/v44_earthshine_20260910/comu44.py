"""V44: isolated outputs, unchanged 10551 x 7506 field and lunar epoch."""
import sys
from pathlib import Path
HERE44 = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE44.parent / 'v43_earthshine_20260910'))
from comu43 import *
CAU44 = HERE44 / 'cau'
OUT44 = ROOT / 'output/v44_earthshine_20260910'
REB44 = OUT44 / '4-rebuts'
VIS44 = OUT44 / 'lliurables/vistes'
MC = (CX + 14.8, CY + 0.9)
N = 1400
X0, Y0 = int(round(MC[0])) - N//2, int(round(MC[1])) - N//2
CXT, CYT = MC[0]-X0, MC[1]-Y0
RL = 455.5018
YY, XX = np.mgrid[:N, :N].astype(np.float32)
R = np.hypot(XX-CXT, YY-CYT)
PHI = np.arctan2(YY-CYT, XX-CXT)
CLAIM = 'CODEX_EARTHSHINE_V44_20260910'

def claim():
    owner = json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())
    assert owner['claim_id'] == CLAIM, owner

def prepare():
    claim()
    for p in (CAU44, REB44, VIS44): p.mkdir(parents=True, exist_ok=True)

def frames():
    fr = json.loads((CAU43/'fotogrames_v43.json').read_text())
    contacts = {tag: json.loads((p/'4-rebuts/F1.2_sol_llenc.json').read_text())['contactes'] for tag,p in RUNS.items()}
    for m in fr:
        m['stem'] = m['nom'].split('.')[0]
        m['t_mid_C2'] = m['t'] + m['exp']/2 - contacts[m['tren']]['C2_t']
        m['t_mid_vixen'] = m['t_mid_C2'] + contacts['vixen']['C2_t']
    return fr, contacts

def to_srgb(rgb, mask):
    lum = (rgb[...,0] + 2*rgb[...,1] + rgb[...,2])/4
    tone = comu.corba_to(np.nan_to_num(lum), mask, 70736.46875, pend=.22, anc=.74, terra=.045)
    yl = comu.a_lineal(tone)
    q = np.nan_to_num(rgb/np.maximum(lum,1e-9)[...,None],nan=1.)
    qm = q.max(-1)
    with np.errstate(divide='ignore',invalid='ignore'):
        wg = np.where(qm>1,(1/np.maximum(yl,1e-8)-1)/(qm-1),1)
    wg = np.clip(np.nan_to_num(wg,nan=0,posinf=1),0,1)
    return np.clip(np.nan_to_num(comu.a_srgb(yl[...,None]*(1+wg[...,None]*(q-1)))),0,1)*mask[...,None]

def png(name, a):
    from PIL import Image
    Image.fromarray(np.round(np.clip(a,0,1)*255).astype('uint8')).save(VIS44/name)

def pear(a,b,m):
    good=m & np.isfinite(a) & np.isfinite(b)
    u=a[good].astype(float);v=b[good].astype(float)
    u-=u.mean();v-=v.mean()
    return float(u@v / max(np.linalg.norm(u)*np.linalg.norm(v),1e-30))
