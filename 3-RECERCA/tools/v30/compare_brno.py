"""Compare actual historical/current composites, frozen geometry and color convention.

Brno is only a judge. This script never contributes pixels to the product.
"""
import gc,hashlib,json,struct,sys,warnings
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from psd_tools.psd.header import FileHeader
D=Path(__file__).parent;ROOT=D.parents[2];AUD=ROOT/'research/tools/auditoria_estructura'
CT=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
sys.path.insert(0,str(AUD));import nucli as N
REG=AUD/'registre2.json';GEO=ROOT/'research/tools/v25_lineal/cau_v25/geometria_v27.json'
reg=json.loads(REG.read_text());M=np.asarray(json.loads(GEO.read_text())['M_llenc_a_v23']);ANGLE=float(np.arctan2(M[1,0],M[0,0]))
CX,CY,RS=5361.768111973117,3775.747534140857,440.60304883027544
RAD=np.round(np.arange(1.2,9.01,.2),2);NTH=1440;RANGES=[(1.2,3),(3,5),(5,9.01)]
BRNO=['TSE_2026_200mm_DHS.png','TSE_2026_400mm_DHS.png','TSE_2026_530mm_DHS.png','TSE2026_Trigaza_800mm.png']
SOURCES={'V27_merged':CT/'Documentacio i QA/superseded_20260905/V27.psb','V28_merged':CT/'V28.psb','V29_before03_merged':CT/'Documentacio i QA/V29_abans_correccio_03_20260905/V29.psb','V29_corrected':ROOT/'research/tools/v29_c03_fix/composite.npy','V30_r4':D/'cau/composite_default_r4.npy'}
def fingerprint(p):
    p=Path(p);st=p.stat();h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    assert (st.st_size,st.st_mtime_ns)==(p.stat().st_size,p.stat().st_mtime_ns)
    return {'path':str(p),'bytes':st.st_size,'sha256':h.hexdigest()}
class LinearLuminance:
    def __init__(self,a,planar=False,den=1):self.a=a;self.planar=planar;self.den=den;self.shape=a.shape[1:] if planar else a.shape[:2]
    def __getitem__(self,idx):
        y,x=idx
        rgb=np.stack([self.a[c,y,x] for c in range(3)],axis=-1).astype('float64')/self.den if self.planar else np.asarray(self.a[idx],dtype='float64')/self.den
        rgb=N.srgb_a_lineal(rgb);return (rgb[...,0]+2*rgb[...,1]+rgb[...,2])/4
def sample_source(p):
    meta=fingerprint(p)
    if p.suffix=='.npy':
        a=np.load(p,mmap_mode='r');assert a.shape==(7506,10551,3);obj=LinearLuminance(a)
    else:
        with p.open('rb') as f:
            hdr=FileHeader.read(f);assert (hdr.height,hdr.width,hdr.depth,int(hdr.color_mode))==(7506,10551,16,3)
            for fmt in ('>I','>I','>Q' if hdr.version==2 else '>I'):
                length=struct.unpack(fmt,f.read(struct.calcsize(fmt)))[0];f.seek(length,1)
            compression=struct.unpack('>H',f.read(2))[0];offset=f.tell()
        assert compression==0 and p.stat().st_size-offset==hdr.channels*hdr.height*hdr.width*2
        a=np.memmap(p,mode='r',dtype='>u2',offset=offset,shape=(hdr.channels,hdr.height,hdr.width));obj=LinearLuminance(a,True,65535)
        meta.update(merged='actual RAW RGB16',offset=offset)
    out=N.mostreja(obj,CY,CX,RS,RAD,NTH,ang0=ANGLE);del obj;a._mmap.close();del a;gc.collect();print('read '+p.name,flush=True)
    return out,meta
def estr(p,degree):
    m=np.isfinite(p);s=degree/360*NTH;num=gaussian_filter1d(np.where(m,p,0),s,axis=1,mode='wrap');den=gaussian_filter1d(m.astype(float),s,axis=1,mode='wrap')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning);return N.estructura(np.where(m,num/np.maximum(den,1e-12),np.nan))
def avg(a):
    with warnings.catch_warnings():warnings.simplefilter('ignore',RuntimeWarning);return np.nanmean(a,axis=0)
def summary(a):return [float(np.nanmedian(a[(RAD>=lo)&(RAD<hi)])) for lo,hi in RANGES]
def main():
    B={};hashes=[]
    for name in BRNO:
        hashes.append(fingerprint(Path(N.BRNO_DIR)/name));im,*_=N.carrega_brno(name);r=reg[name];B[name]=N.mostreja(im,r['cy'],r['cx'],r['R_sol_px'],RAD,NTH,ang0=np.deg2rad(r['gir_deg']));del im
    P={}
    for tag,p in SOURCES.items():P[tag],meta=sample_source(p);hashes.append(meta)
    rep={'method':'linear luminance after sRGB decoding of both inputs; angular Gaussian normalized by observed support; per-ring Pearson then mean refs then radial median','angle_deg':float(np.degrees(ANGLE)),'radial_samples':RAD.tolist(),'ranges':RANGES,'results':{},'caveat':'Beyond5R not validated, null often exceeds correlation. No claim global superiority over V27. Angular smoothing does not validate micrograin.'}
    for deg in (1.,4.5):
        eb={k:estr(p,deg) for k,p in B.items()};control=avg(np.stack([N.corr_per_anell(eb[a],eb[b]) for j,a in enumerate(BRNO) for b in BRNO[j+1:]]));rows={'BrnoBrno':{'r':summary(control),'per_ring':control.tolist()}}
        for tag,p in P.items():
            en=estr(p,deg);c=avg(np.stack([N.corr_per_anell(en,eb[b]) for b in BRNO]));null=avg(np.stack([N.corr_per_anell(np.roll(en,NTH//2,axis=1),eb[b]) for b in BRNO]));rows[tag]={'r':summary(c),'null180':summary(null),'per_ring':c.tolist(),'null_per_ring':null.tolist()}
        rep['results'][str(deg)]=rows
    for p in (REG,GEO,AUD/'nucli.py',Path(N.GEO_BRNO)):hashes.append(fingerprint(p))
    rep['inputs']=hashes;(D/'cau/brno_comparison.json').write_text(json.dumps(rep,indent=2)+'\n');print('actual-source Brno comparison saved',flush=True)
if __name__=='__main__':main()
