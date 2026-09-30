"""S1: llegir de la V49 congelada (només lectura) les tres capes visibles a la ROI lunar, recompondre la ROI
amb el model de fusió (base amb màscara → 09 LIGHTEN → lunar NORMAL amb alfa·màscara) i comparar amb
l'exportació real de Photoshop (A2_Pere_actual). També: vora de la DADA de la base sota la seva màscara."""
import json, hashlib, numpy as np, time
from pathlib import Path
from psd_tools import PSDImage
ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026'); HERE=Path(__file__).resolve().parent; CAU=HERE/'cau'; CAU.mkdir(exist_ok=True)
OUT=ROOT/'output/earthshine_v50_temporal_20260912'; V=ROOT/'output/earthshine_v49_pere_reveal_20260912'
SRC=V/'V49_Pere_referencia_20260912.psb'; X0,Y0,N=4677,3077,1400
CX=699.568111973117; CY=699.6475341408573
t0=time.time()
s=PSDImage.open(SRC); assert s.size==(10551,7506) and s.depth==16 and len(s)==26
def chan(l,cid):
    ids=[int(c.id) for c in l._record.channel_info]; i=ids.index(cid); cd=l._channels[i]
    if cid==-2: md=l._record.mask_data; w,h=md.right-md.left,md.bottom-md.top; box=(md.left,md.top,md.right,md.bottom)
    else: w,h=l.width,l.height; box=(l.left,l.top,l.right,l.bottom)
    a=np.frombuffer(cd.get_data(w,h,16,2),dtype='>u2').reshape(h,w).astype(np.uint16); return a,box
def roi(a,box):
    l,t,r,b=box; out=np.zeros((N,N)+a.shape[2:],np.uint16)
    ys=slice(max(Y0,t),min(Y0+N,b)); xs=slice(max(X0,l),min(X0+N,r))
    out[ys.start-Y0:ys.stop-Y0, xs.start-X0:xs.stop-X0]=a[ys.start-t:ys.stop-t, xs.start-l:xs.stop-l]; return out
L=list(s); base=L[1]; l09=L[7]; lun=L[25]
assert base.name=='00 Base corba (total) · V42' and l09.name=='09 1/60 x2' and lun.name.startswith('V49 · graella verda')
rec={}
for nm,l in (('base',base),('l09',l09),('lun',lun)):
    md=l._record.mask_data
    rec[nm]=dict(name=l.name,bbox=list(l.bbox),blend=str(l.blend_mode),opacity=l.opacity,visible=l.visible,
                 mask=None if md is None else dict(box=[md.left,md.top,md.right,md.bottom],bg=md.background_color,flags=str(md.flags)),
                 channels=[int(c.id) for c in l._record.channel_info])
    print(nm,rec[nm],flush=True)
    for cid in rec[nm]['channels']:
        a,box=chan(l,cid); r=roi(a,box); np.save(CAU/f'{nm}_ch{cid}_roi.npy',r)
        print('  ch',cid,box,'roi min/max',int(r.min()),int(r.max()),f'{time.time()-t0:.0f}s',flush=True)
        del a
json.dump(rec,open(CAU/'s1_records.json','w'),ensure_ascii=False,indent=1)
# --- recomposició de la ROI ---
f=lambda nm,c: np.load(CAU/f'{nm}_ch{c}_roi.npy').astype(np.float64)/65535
B=np.stack([f('base',c) for c in (0,1,2)],-1); Ba=f('base',-1)*f('base',-2)
S=np.stack([f('l09',c) for c in (0,1,2)],-1); Sa=f('l09',-1)
Lr=np.stack([f('lun',c) for c in (0,1,2)],-1); La=f('lun',-1)*f('lun',-2)
# backdrop: base sobre transparent
Ca=Ba; Cc=B*Ba[...,None]  # premultiplicat
# 09 LIGHTEN: resultat = (1-ab)*Cs + ab*max(Cs,Cb), alfa = as+ab-as*ab (font opaca dins del seu rectangle)
Cb=np.where(Ca[...,None]>0, Cc/np.maximum(Ca[...,None],1e-9),0)
mix=(1-Ca[...,None])*S+Ca[...,None]*np.maximum(S,Cb)
Cc=Sa[...,None]*mix+(1-Sa[...,None])*Cc; Ca=Sa+Ca-Sa*Ca
# lunar NORMAL
Cc=La[...,None]*Lr+(1-La[...,None])*Cc; Ca=La+Ca-La*Ca
comp=np.where(Ca[...,None]>0,Cc/np.maximum(Ca[...,None],1e-9),0)
pere=np.load(V/'A2_Pere_actual_RGB16.npy').astype(np.float64)/65535
d=np.abs(comp-pere)*65535
print('RECOMPOSICIÓ vs Photoshop: max DN16',d.max(),'p99.9',np.percentile(d,99.9),'mitjana',d.mean(),'alfa min',Ca.min())
np.save(CAU/'recomp_v49_roi.npy',np.rint(comp*65535).astype(np.uint16))
# --- vora de la dada de la base sota la màscara ---
f4=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy'); th=np.linspace(0,2*np.pi,1440,endpoint=False)
from scipy.ndimage import map_coordinates
rr=np.arange(430,482,0.25); x=CX+np.cos(th)[:,None]*rr; y=CY+np.sin(th)[:,None]*rr
Pg=map_coordinates(B[...,1],[y.ravel(),x.ravel()],order=1,mode='nearest').reshape(1440,-1)*65535
Pm=map_coordinates(f('base',-2),[y.ravel(),x.ravel()],order=1,mode='nearest').reshape(1440,-1)
dada=np.full(1440,np.nan); m50=np.full(1440,np.nan)
for i in range(1440):
    p=Pg[i]; out=np.median(p[(rr>=f4[i]+8)&(rr<f4[i]+14)]); k=np.where(p>=0.5*out)[0]; 
    if len(k): dada[i]=rr[k[0]]
    q=Pm[i]; k=np.where(q>=0.5)[0]
    if len(k): m50[i]=rr[k[0]]
sec=np.arange(1440)//120
res=dict(dada_base_menys_F4_per_sector=[float(np.nanmedian((dada-f4)[sec==s])) for s in range(12)],
         mascara_base_50_menys_F4_per_sector=[float(np.nanmedian((m50-f4)[sec==s])) for s in range(12)],
         base_G_mediana_d0_3_per_sector=[float(np.median(Pg[sec==s][:, (rr>=0)&(rr<3)])) if False else float(np.nanmedian([np.median(Pg[i][(rr>=f4[i])&(rr<f4[i]+3)]) for i in np.where(sec==s)[0]])) for s in range(12)],
         base_G_mediana_d3_8_per_sector=[float(np.nanmedian([np.median(Pg[i][(rr>=f4[i]+3)&(rr<f4[i]+8)]) for i in np.where(sec==s)[0]])) for s in range(12)],
         base_G_mediana_d8_14_per_sector=[float(np.nanmedian([np.median(Pg[i][(rr>=f4[i]+8)&(rr<f4[i]+14)]) for i in np.where(sec==s)[0]])) for s in range(12)],
         recomposicio_max_DN16=float(d.max()),recomposicio_p999_DN16=float(np.percentile(d,99.9)),source_sha256=hashlib.sha256(SRC.read_bytes()).hexdigest() if False else 'fc22af4660c7ac7aeb10a1433f1c159a91968fed70646c4b9200bb5bf7748366 (no recalculat)')
np.savez(OUT/'S1_base_dada.npz',theta=th,f4=f4,dada=dada,mask50=m50)
json.dump(res,open(OUT/'S1_capes.json','w'),ensure_ascii=False,indent=1)
for k,v in res.items(): print(k, np.round(v,2).tolist() if isinstance(v,list) else v)
print('fet',f'{time.time()-t0:.0f}s')
