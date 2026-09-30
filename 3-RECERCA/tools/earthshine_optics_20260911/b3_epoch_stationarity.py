"""Test whether a static lunar HDR is a consistent forward scene at the limb.
Compare lunar registration with ephemeris-derived solar translation and the
opposite-translation control. This is a diagnostic only; no product warping.
"""
from optics_common import *
from scipy.ndimage import map_coordinates
import sys
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from comu45 import f2,comu,RUNS,COMMON_TO_FINAL

ctx=f2.Ctx(comu.Run.obre(str(RUNS['vixen'])));pos=json.loads((RUNS['vixen']/'4-rebuts/F1.3_registre.json').read_text())['fotogrames']
rawmeta=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'];meta={m['stem']:m for m in rawmeta if m['tren']=='vixen'}
fm=json.loads((SRC/'B1_full_native_ensemble.json').read_text())['source_frames'];GG=np.load(SRC/'compositor_cache/G.npy',mmap_mode='r');WW=np.load(SRC/'compositor_cache/W.npy',mmap_mode='r')
A=COMMON_TO_FINAL[:2,:2]@np.array([[ctx.ca,-ctx.sa],[ctx.sa,ctx.ca]])/ctx.k
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);theta=np.arctan2(y-CY,x-CX);reports=[]
for epoch in ['vixen_2','vixen_5']:
    ids=[i for i,m in enumerate(fm) if m['epoch']==epoch];centres=[];source=[]
    for i in ids:
        m=meta[fm[i]['stem']];p=pos[m['nom']];sun=np.array([CX,CY])-A@np.array([p['lluna_dx'],p['lluna_dy']])+np.array(m['native']['shift']);centres.append(sun);source.append(dict(stem=m['stem'],exp=m['exp'],time_C2=m['t_mid_C2'],solar_center_in_lunar_grid=sun.tolist()))
    centres=np.array(centres);reference=centres.mean(0);shifts=reference-centres
    arrays={};weights={}
    for case,sign in [('moon',0),('sun',1),('opposite',-1)]:
        gs=[];ws=[]
        for i,shift in zip(ids,shifts):
            d=shift*sign;co=[y-d[1],x-d[0]];g=np.asarray(GG[i],float);w=np.asarray(WW[i],float)
            if sign:
                valid=map_coordinates((w>0).astype(float),co,order=1,mode='constant',cval=0)>.999
                g=map_coordinates(g,co,order=1,mode='nearest');w=map_coordinates(w,co,order=1,mode='constant',cval=0)*valid
            gs.append(g);ws.append(w)
        arrays[case]=np.array(gs);weights[case]=np.array(ws)
    # Same per-frame conservative weights in all three diagnostics.
    w=np.minimum.reduce(list(weights.values()));den=w.sum(0);count=(w>0).sum(0);valid=(count>=3)&(den>0);rows=[];maps={}
    for case in arrays:
        mean=(w*arrays[case]).sum(0)/np.maximum(den,1e-30);res=(w*(arrays[case]-mean)**2).sum(0)/np.maximum(count-1,1);maps[case]=np.where(valid,res,np.nan)
        regions=[]
        for lo,hi in [(0,350),(350,435),(435,449),(449,454),(454,480),(500,650)]:
            m=valid&(r>=lo)&(r<hi);regions.append(dict(radius=[lo,hi],pixels=int(m.sum()),effective_residual_quantiles=np.percentile(res[m],[50,90,99]).tolist()))
        rows.append(dict(registration=case,regions=regions))
    reports.append(dict(epoch=epoch,frames=source,solar_drift_span_xy=(centres.max(0)-centres.min(0)).tolist(),diagnostics=rows))
    np.savez_compressed(OUT/f'B3_{epoch}_stationarity.npz',**maps)
    print(epoch,'solar drift span',reports[-1]['solar_drift_span_xy'],flush=True)
save('B3_epoch_stationarity.json',dict(method=__doc__,epochs=reports,limits=['Effective FPN-inflated source weights; diagnostic residuals are not calibrated chi-square','Solar translation control resamples sources; the opposite control has equal displacement magnitude','Near the lunar boundary solar registration changes the occultation geometry and is not a solution','Residuals can also contain seeing, photometric calibration error and subpixel sampling; motion is not the only possible cause']))
