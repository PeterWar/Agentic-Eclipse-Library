# Native extraction reused from verified prior pilot; parent SHA256 6db0e9d3b43fd2463873f819b0f2f0a66be4c5ed20d5daba8fd1fbe5bec51c85
"""Local exposure-bridge registration on bright observed coronal structures.
No lunar halo/edge, zero-filled annulus, source edits or PSB writes.
Offsets measure residuals of the existing SOLAR geometry, in final pixels.
"""
import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from b1_native import *
from scipy.ndimage import gaussian_filter
from scipy.optimize import least_squares
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=ROOT/'output/earthshine_compatibility_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_COMPATIBILITY_20260911'
names=[2969,2970,2971,2972,2974,2975,2976,2977,2978,2979,2980,2981,2988,2989,2990,2993,2994,2995,2996,3000,3001,3002]
cache=OUT/'coronal_patches.npz';metaout=OUT/'B0_patch_meta.json'
S=224;PAD=40;CORE=144;RG=5
patches=[dict(radius=float(rad),angle=int(deg),x=CX+rad*RS*np.cos(np.deg2rad(deg)),y=CY+rad*RS*np.sin(np.deg2rad(deg))) for rad in [1.65,2.5,3.5] for deg in range(0,360,30)]
if not cache.exists():
    ctx=f2.Ctx(comu.Run.obre(str(RUNS['vixen'])))
    pos=json.loads((RUNS['vixen']/'4-rebuts/F1.3_registre.json').read_text())['fotogrames']
    kq=json.loads((RUNS['vixen']/'4-rebuts/F2.2_coherencia.json').read_text())['k']
    inv=cv2.invertAffineTransform(COMMON_TO_FINAL);fcorr,frep=B.flat_ripple_correction(ctx,'vixen')
    xx=np.concatenate([np.mgrid[0:S,0:S][1].astype(np.float32)+p['x']-S/2 for p in patches],axis=1)
    yy=np.concatenate([np.mgrid[0:S,0:S][0].astype(np.float32)+p['y']-S/2 for p in patches],axis=1)
    qx=inv[0,0]*xx+inv[0,1]*yy+inv[0,2];qy=inv[1,0]*xx+inv[1,1]*yy+inv[1,2]
    dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k
    values={};rows=[]
    for n in names:
        nom=f'572A{n}.CR3';v=pos[nom]
        with rawpy.imread(ctx.ruta[nom]) as rr:raw=rr.raw_image.astype(np.float32)
        dark=ctx.dark(v['exp']);num=np.zeros_like(xx);den=num.copy();rawnum=num.copy();minsupport=np.ones_like(xx,dtype=bool)
        rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']).astype(np.float32);ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']).astype(np.float32)
        for i in range(4):
            if comu.IDX_CANAL[i]!=1:continue
            oy,ox=ctx.orig[i];rp=raw[oy::2,ox::2]
            pl=comu.calibra_pla(rp,dark[oy::2,ox::2],ctx.flat[oy::2,ox::2],v['exp'],ctx.wb,ctx.mc,i)
            if fcorr is not None:pl*=fcorr[i]
            mx=((rx-ox)*.5).astype(np.float32);my=((ry-oy)*.5).astype(np.float32)
            rn=(rp-ctx.cfg['pedestal_dn'])/(ctx.cfg['saturacio_dn']-ctx.cfg['pedestal_dn'])
            ix=np.floor(mx).astype(int);iy=np.floor(my).astype(int)
            valid=np.maximum.reduce([rn[iy,ix],rn[iy+1,ix],rn[iy,ix+1],rn[iy+1,ix+1]])<.75
            # No partial-neighbour brightness weighting in the radiance.
            num+=cv2.remap(pl*kq.get(nom,1),mx,my,cv2.INTER_LINEAR);den+=1
            rawnum+=cv2.remap(rp-ctx.cfg['pedestal_dn'],mx,my,cv2.INTER_LINEAR);minsupport&=valid
        g=num/den;rdn=rawnum/den
        values[str(n)]=np.array(np.split(g,len(patches),axis=1))
        values[f'{n}_rawdn']=np.array(np.split(rdn,len(patches),axis=1))
        values[f'{n}_valid']=np.array(np.split(minsupport,len(patches),axis=1))
        rows.append(dict(frame=nom,exp=v['exp'],source=str(ctx.ruta[nom]),sha256=sha(Path(ctx.ruta[nom])),solar_center=[v['sol_x'],v['sol_y']],f1_adjustment=v.get('desplacament_px')))
        print('rendered',n,flush=True)
    np.savez_compressed(cache,**values);metaout.write_text(json.dumps(dict(patches=patches,frames=rows,size=S,core=CORE,search=RG,source_radiometry='Native calibrated G, flat, existing k. No phi field: registration uses high-pass coronal structures; no image product.'),indent=2))
