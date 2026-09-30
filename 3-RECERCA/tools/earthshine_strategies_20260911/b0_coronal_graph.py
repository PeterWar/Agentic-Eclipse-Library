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
OUT=ROOT/'output/earthshine_strategies_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_STRATEGIES_20260911'
names=[2970,2976,2977,2978,2979,2994,2995,2996]
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
z=np.load(cache);hp={}
for n in names:
    q=np.log(np.maximum(z[str(n)],1e-6)).astype(np.float32)
    hp[n]=np.array([gaussian_filter(a,2)-gaussian_filter(a,8) for a in q])

def estimate(ref,mov):
    template=ref[PAD:PAD+CORE,PAD:PAD+CORE]
    search=mov[PAD-RG:PAD+CORE+RG,PAD-RG:PAD+CORE+RG]
    cc=cv2.matchTemplate(search,template,cv2.TM_CCOEFF_NORMED)
    j,i=np.unravel_index(np.argmax(cc),cc.shape);x=float(i-RG);y=float(j-RG)
    boundary=i in (0,2*RG) or j in (0,2*RG)
    def sub(a,b,c):return float(np.clip(.5*(a-c)/(a-2*b+c),-.5,.5)) if a-2*b+c<0 else 0.
    if not boundary:x+=sub(*cc[j,i-1:i+2]);y+=sub(*cc[j-1:j+2,i])
    return dict(dx=x,dy=y,r=float(cc[j,i]),boundary=bool(boundary))

def fit(rows):
    if len(rows)<4:return None
    xy=np.array([[a['patch']['x']-CX,a['patch']['y']-CY] for a in rows]);v=np.array([[a['dx'],a['dy']] for a in rows])
    def fun(t):return (v-np.array([t[0]-t[2]*xy[:,1],t[1]+t[2]*xy[:,0]]).T).ravel()
    f=least_squares(fun,[*np.median(v,axis=0),0],loss='huber',f_scale=.3)
    return dict(dx=float(f.x[0]),dy=float(f.x[1]),rotation_rad=float(f.x[2]),residual_rms=float(np.sqrt(np.mean(fun(f.x)**2))),n=len(rows))

pairs=[(2976,2970),(2976,2977),(2977,2978),(2978,2979),(2994,2995),(2995,2996),(2976,2994),(2977,2995),(2978,2996),(2976,2978)]
reports=[];controls=[]
for a,b in pairs:
    rows=[]
    for k,p in enumerate(patches):
        masks=[z[f'{n}_valid'][k] for n in [a,b]]
        dns=[float(np.median(z[f'{n}_rawdn'][k])) for n in [a,b]]
        if min(m.mean() for m in masks)<.995 or min(dns)<64:continue
        d=estimate(hp[a][k],hp[b][k]);d.update(patch=p,index=k,rawdn=dns)
        # Fixed selection before fitting transforms; retain rejected scores.
        d['accepted']=d['r']>=.80 and not d['boundary'];rows.append(d)
    accepted=[d for d in rows if d['accepted']];f=fit(accepted)
    halves=[fit([d for d in accepted if (d['patch']['angle']//30)%2==j]) for j in [0,1]]
    gap=float(np.hypot(halves[0]['dx']-halves[1]['dx'],halves[0]['dy']-halves[1]['dy'])) if all(halves) else None
    rec=dict(reference=a,moving=b,rows=rows,fit=f,halves=halves,half_gap=gap,pass_geometry=bool(f and f['n']>=8 and f['residual_rms']<=.5 and gap is not None and gap<=.5))
    reports.append(rec);print('pair',a,b,'fit',f,'gap',gap,flush=True)
    if accepted:
        k=accepted[0]['index'];base=hp[a][k];moved=cv2.warpAffine(base,np.array([[1,0,3],[0,1,-2]],np.float32),(S,S),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
        d=estimate(base,moved);d.update(pair=[a,b],imposed=[3,-2],error=float(np.hypot(d['dx']-3,d['dy']+2)));controls.append(d)
        opp=(k//12)*12+(k%12+6)%12
        rec['angular_null']=estimate(base,hp[b][opp])
report=dict(strategy='Exposure-overlap graph using bright unsaturated coronal structures in independent angular regions',pairs=reports,controls=controls,
 gates=dict(rawdn_median_min=64,valid_fraction_min=.995,ncc_min=.8,min_regions=8,fit_rms_max=.5,halves_disagreement_max=.5,known_translation_max_error=.1),
 limits='Bright same-sensor structures avoid lunar SNR and annulus-mask failure, but cross-train validation, graph closure and absolute lunar mapping remain required before a new product.')
(OUT/'B1_coronal_graph.json').write_text(json.dumps(report,indent=2))
fig,ax=plt.subplots(figsize=(10,8),layout='constrained')
from astropy.io import fits
with fits.open(RUNS['vixen']/'2-ldic/LDIC_G.fits',memmap=True) as f:g=f[0].data[::8,::8].astype(float)
ax.imshow(np.log10(np.maximum(g,1)),vmin=1,vmax=5,cmap='gray',origin='upper')
ax.set_title('Context complet del llenç Vixen — font de registre solar; no és un producte nou')
ax.set_xlabel('Píxels del llenç comú / 8');ax.set_ylabel('Píxels del llenç comú / 8')
fig.savefig(OUT/'vistes/B0_full_canvas_context.png',dpi=120);plt.close(fig)
