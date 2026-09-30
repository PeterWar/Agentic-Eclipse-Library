"""Fixed upper green-region evidence test; no photographic image modification.
Full angular transforms avoid filtering the artificial edge of a selected ROI.
Only correlation receives the user's mask. LROC is a judge, never pixel input.
"""
from pathlib import Path
import sys,json,numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from comu45 import *
from scipy.ndimage import map_coordinates,distance_transform_edt,label
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
OUT=ROOT/'output/earthshine_compatibility_20260911'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_COMPATIBILITY_20260911'
mask0=np.load(ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz')['green'];lab,_=label(mask0);target=int(lab[313,630]);assert target>0;mask=lab==target
rr=np.arange(370.,435.,.5);nt=1440;th=np.arange(nt)*2*np.pi/nt;coords=[CYT+rr[:,None]*np.sin(th),CXT+rr[:,None]*np.cos(th)]
lrfile=ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy';lr=np.load(lrfile);bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox']
L=np.zeros((N,N));oy,ox=bb[1]-Y0,bb[0]-X0;L[oy:oy+lr.shape[0],ox:ox+lr.shape[1]]=lr[...,:3].mean(-1)
raw={'L':L};paths={}
for key,filename,field in [('V','vixen_reference.npy',None),('S','sony_reference.npy',None),('Vlong','epoch_vixen_3.npz','g'),('SA8','epoch_sony_A_1.npz','g'),('SB8','epoch_sony_B_2.npz','g')]:
    p=CAU45/filename;v=np.load(p);raw[key]=(v if field is None else v[field]).astype(float);paths[key]=dict(path=str(p),sha256=sha(p))
valids={k:np.isfinite(a)&(a>0) for k,a in raw.items()};common=np.logical_and.reduce([map_coordinates(v.astype(float),coords,order=1,mode='constant',cval=0)>.999 for v in valids.values()])
weight=(map_coordinates(mask.astype(float),coords,order=1,mode='constant')>.999)*common
freq=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*rr[:,None])
def corr(a,b,w):
    ok=(w>0)&np.isfinite(a)&np.isfinite(b);ww=w[ok];a=a[ok];b=b[ok];a=a-np.sum(a*ww)/ww.sum();b=b-np.sum(b*ww)/ww.sum()
    return float(np.sum(ww*a*b)/max(np.sqrt(np.sum(ww*a*a)*np.sum(ww*b*b)),1e-30))
Y,X=np.mgrid[:N,:N];radius=np.hypot(X-CXT,Y-CYT);x=(X-CXT)/500;y=(Y-CYT)/500
result={};spectra={};bandimages={}
pairs=[('VS','V','S'),('VL','V','L'),('SL','S','L'),('VlongSA','Vlong','SA8'),('VlongSB','Vlong','SB8'),('VlongL','Vlong','L'),('SAL','SA8','L'),('SBL','SB8','L')]
for mode in ['linear','log']:
    pol={}
    for key,a in raw.items():
        valid=valids[key];ix=distance_transform_edt(~valid,return_distances=False,return_indices=True);g=a[tuple(ix)]
        if mode=='log':g=np.log(np.maximum(g,1e-30))
        mm=valid&(radius<435);A=np.stack([np.ones(mm.sum()),x[mm],y[mm]],1);co=np.linalg.lstsq(A,g[mm],rcond=None)[0]
        pol[key]=map_coordinates(g-(co[0]+co[1]*x+co[2]*y),coords,order=3,mode='nearest')
    bands={}
    for lo,hi in [(8,16),(16,24),(24,40),(40,64)]:
        keep=(freq>=1/hi)&(freq<=1/lo);b={k:np.fft.irfft(np.fft.rfft(v,axis=1)*keep,n=nt,axis=1) for k,v in pol.items()};rows={}
        for name,a,c in pairs:
            r=corr(b[a],b[c],weight);null=[corr(b[a],np.roll(b[c],nt*j//12,axis=1),weight) for j in range(1,12)];ceiling=max(map(abs,null));rows[name]=dict(r=r,null_max_abs=ceiling,pass_null=bool(r>ceiling))
        rows['triple_pass']=bool(all(rows[p]['pass_null'] for p in ['VS','VL','SL']));bands[f'{lo}_{hi}']=rows
        if mode=='linear' and lo in [16,24]:
            for k,v in b.items():bandimages[f'{lo}_{k}']=v
        print(mode,lo,hi,'triple',rows['triple_pass'],{k:round(rows[k]['r'],3) for k in ['VS','VL','SL','VlongSA','VlongL','SAL']},flush=True)
    result[mode]=bands
rep=dict(mask='Upper user green component, bbox [466,272,800,373], selection fixed before testing',mask_pixels=int(mask.sum()),polar_support=int(weight.sum()),radius_range=[370,435],methods='Full angular FFT bands; Cartesian plane only; native common coordinates unchanged; 11 rotated nulls; no fit or registration optimised on the marked area',paths=paths,LROC=dict(path=str(lrfile),sha256=sha(lrfile)),results=result,limits=['Local texture at these scales only; not the last lunar pixels','Existing observed V45 sources, not a newly recovered or delivered image','Same-sensor FPN is not independent; joint V/S/L evidence is required','Correlations do not establish diffraction-limited resolution or CameraRaw preservation for a future edit'])
(OUT/'E0_green_judge.json').write_text(json.dumps(rep,indent=2))
np.savez_compressed(OUT/'E0_green_bands.npz',radii=rr,theta=th,weight=weight,**bandimages)
fig,axs=plt.subplots(2,3,figsize=(13,6),layout='constrained');sel=(th>np.deg2rad(237))&(th<np.deg2rad(286))
for row,lo in enumerate([16,24]):
    for col,k in enumerate(['V','S','L']):
        a=bandimages[f'{lo}_{k}'];scale=np.percentile(abs(a[weight>0]),97);axs[row,col].imshow(a[:,sel],cmap='gray',vmin=-scale,vmax=scale,origin='lower',extent=[237,286,370,435],aspect='auto');axs[row,col].set_title(f'{k}: banda {lo}–{24 if lo==16 else 40} px');axs[row,col].set_xlabel('Angle lunar (°)');axs[row,col].set_ylabel('Radi (px)')
fig.suptitle('Diagnòstic de textura — cada panell amb contrast normalitzat; no és una proposta estètica')
fig.savefig(OUT/'vistes/E0_green_comparison.png',dpi=140);plt.close(fig)
