"""Test the historical solar-register estimator using an imposed translation.
Uses a 4x decimated full-canvas observed G field; no PSB or run is modified.
The control establishes estimator behaviour, not the actual camera motion.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from comu45 import *
from astropy.io import fits
from scipy.ndimage import shift
from skimage.registration._masked_phase_cross_correlation import cross_correlate_masked
OUT=ROOT/'output/earthshine_strategies_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_STRATEGIES_20260911'
s=json.loads((RUNS['vixen']/'4-rebuts/F1.2_sol_llenc.json').read_text())['llenc']
with fits.open(RUNS['vixen']/'2-ldic/LDIC_G.fits',memmap=True) as f:g=f[0].data[::4,::4].astype(np.float32)
yy,xx=np.mgrid[:g.shape[0],:g.shape[1]];rr=np.hypot(xx-s['W']/8,yy-s['H']/8)
ap=(rr>1.3*s['R_sol_px']/4)&(rr<8*s['R_sol_px']/4)
win=cv2.createHanningWindow((g.shape[1],g.shape[0]),cv2.CV_32F)
valid=np.isfinite(g)&(g>0)&ap
def zeroed(a,mask):
    z=np.zeros_like(a);z[mask]=np.log10(a[mask]);z[mask]-=z[mask].mean();return (z*win).astype(np.float64)
zref=zeroed(g,valid);reports=[]
for imp in [(4.,-3.),(-3.,2.),(.75,-.5)]:
    moved=shift(g,(imp[1],imp[0]),order=1,cval=np.nan,prefilter=False)
    mask=np.isfinite(moved)&(moved>0)&ap
    d,resp=cv2.phaseCorrelate(zref,zeroed(moved,mask))
    row=dict(imposed_coarse=list(imp),imposed_native=(np.array(imp)*4).tolist(),old_recovered_coarse=list(d),old_error_native=float(np.linalg.norm(np.array(d)-imp)*4),old_response=resp)
    # Correctly normalized masked NCC: zero values are not image evidence.
    a=np.log(np.maximum(np.nan_to_num(g),1e-6));b=np.log(np.maximum(np.nan_to_num(moved),1e-6))
    cc=cross_correlate_masked(a,b,valid,mask,mode='full',overlap_ratio=.8)
    j,i=np.unravel_index(np.argmax(cc),cc.shape);dy=j-(g.shape[0]-1);dx=i-(g.shape[1]-1)
    def sub(v):
        a,b,c=v;return float(.5*(a-c)/(a-2*b+c))
    dx+=sub(cc[j,i-1:i+2]);dy+=sub(cc[j-1:j+2,i]);d2=np.array([-dx,-dy])
    row.update(masked_NCC_recovered_coarse=d2.tolist(),masked_NCC_error_native=float(np.linalg.norm(d2-imp)*4))
    reports.append(row);print(json.dumps(row),flush=True)
rep=dict(source=str(RUNS['vixen']/'2-ldic/LDIC_G.fits'),decimation=4,full_canvas=True,annulus_solar_radii=[1.3,8],reports=reports,
 limitation='Same observed image with imposed translations; not a measurement of historical pointing errors; 4x grid used only for diagnostic cost.')
(OUT/'A0_phase_guard.json').write_text(json.dumps(rep,indent=2))
