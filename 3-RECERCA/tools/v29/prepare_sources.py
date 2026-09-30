"""Fresh LDIC sources, retaining the temporal limb and no texture suppression.

No inpainting, texture cloning, Fourier notches or radial detail fade.
This stage does not authorize unqualified low-weight pixels for final display.
"""
from common import *
from inspect_inputs import sha

def main():
    rad,theta=coords(); receipt={'sources':{},'geometry':{'common_shape':[H,W],'common_sun_xy':[W/2,H/2],'final_sun_xy':[CX,CY],'M':M,'note':'M retained as intensity-fitted; corrected metadata only, no blind 0.5 pixel shift.'}}
    for name,path in RUNS.items():
        log('load '+name); run=comu.Run.obre(str(path))
        planes=[]; ps=[]; src=[]
        for c in comu.CANALS:
            fp=path/f'2-ldic/LDIC_{c}.fits'; planes.append(fits.getdata(fp).astype(np.float32)); ps.append(fits.getdata(path/f'2-ldic/PES_{c}.fits').astype(np.float32)); src.append({'file':str(fp),'sha256':sha(fp)})
        cam=np.stack(planes,axis=-1); del planes
        valid=np.all(np.isfinite(cam)&(cam>0),axis=-1)&np.logical_and.reduce([p>0 for p in ps])
        outer=comu.mascara_dada(ps[1],rad)&valid
        support=outer | (valid & (rad<1.12*RS))
        np.save(CAU/f'{name}_support.npy',support)
        np.save(CAU/f'{name}_weight_G.npy',ps[1]); del ps
        _,total=comu.lluminancia(np.nan_to_num(cam,nan=0),run.matriu,run.color['guany']); del cam
        total=np.where(support[...,None],total,0).astype(np.float32)
        np.save(CAU/f'{name}_total.npy',total); del total
        sky=np.stack([fits.getdata(path/f'2-ldic/CEL_{c}.fits').astype(np.float32) for c in comu.CANALS],axis=-1)
        skyvalid=np.all(np.isfinite(sky),axis=-1)
        # The tiny newly exposed limb has no sky-decomposition sample. A local
        # normalized low-frequency sky estimate is explicitly marked in receipt.
        if np.any(support&~skyvalid):
            for c in range(3):
                v=np.nan_to_num(sky[...,c],nan=0); missing=support&~skyvalid
                # Only inner 1200-square ROI needs this interpolation.
                sl=(slice(int(H/2-600),int(H/2+600)),slice(int(W/2-600),int(W/2+600)))
                est=normgauss(v[sl],skyvalid[sl].astype(np.float32),24)
                piece=v[sl]; piece[missing[sl]]=est[missing[sl]]; sky[...,c]=v
        _,sky=comu.lluminancia(np.nan_to_num(sky,nan=0),run.matriu,run.color['guany'])
        np.save(CAU/f'{name}_sky.npy',sky.astype(np.float32)); del sky
        receipt['sources'][name]={'ldic':src,'matrix':run.matriu,'gain':run.color['guany'],'support_pixels':int(support.sum()),'inner_added_pixels':int((support&~outer).sum()),'sky_interpolation':'normalized Gaussian sigma24 px only for missing near-limb sky; LDIC radiance never filled'}
        del support,valid,outer,skyvalid
    savejson(CAU/'fresh_sources.json',receipt); log('fresh sources ready')

if __name__=='__main__': main()
