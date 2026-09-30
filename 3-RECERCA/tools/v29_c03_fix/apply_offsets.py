"""Apply measured constants through the original CFA/HDR weights, G only.

Creates separate layer-03 inputs; accepted V29 sources and layers are read-only.
"""
import os,sys,json
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026')
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from common import *
import f2,rawpy
D=Path(__file__).parent

def main():
    model=json.loads((D/'offset_model.json').read_text());inv=cv2.invertAffineTransform(COMMON_TO_FINAL)
    yy,xx=np.ogrid[:H,:W];qx=(inv[0,0]*xx+inv[0,1]*yy+inv[0,2]).astype('float32');qy=(inv[1,0]*xx+inv[1,1]*yy+inv[1,2]).astype('float32')
    rep={}
    for tag in ['vixen','sony']:
        path=RUNS[tag];run=comu.Run.obre(str(path));ctx=f2.Ctx(run)
        pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];groups=['vixen'] if tag=='vixen' else ['sony_A','sony_B']
        delta={g:np.zeros((H,W,3),np.float32) for g in groups};dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k
        for j,name in enumerate(sorted(pos)):
            group='vixen' if tag=='vixen' else ('sony_A' if int(name[3:8])<=6987 else 'sony_B')
            b=np.array(model['groups'][group]['offsets'][name],np.float32)
            if not np.any(b):continue
            v=pos[name];rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']).astype('float32');ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']).astype('float32');lunar=f2.mascara_lluna(ctx,v,rx,ry)
            with rawpy.imread(ctx.ruta[name]) as raw:plane=raw.raw_image.astype('float32')
            for i in range(4):
                c=comu.IDX_CANAL[i]
                if b[c]==0:continue
                oy,ox=ctx.orig[i];ww=f2.finestra(plane[oy::2,ox::2]-ctx.cfg['pedestal_dn'],v['exp'],ctx.cfg['saturacio_dn'],ctx.cfg['pedestal_dn'])*ctx.valid[oy::2,ox::2]
                mx=((rx-ox)*.5).astype('float32');my=((ry-oy)*.5).astype('float32')
                dd=cv2.remap(ww,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*lunar
                delta[group][...,c]+=b[c]*dd
            if j%5==0:log(f'offset weights {tag} {j+1}/{len(pos)}')
        del dx,dy,rx,ry,lunar,plane,mx,my,dd,ctx
        for g in groups:
            den=np.load(CAU/f'{g}_weights.npy',mmap_mode='r');native=delta.pop(g)/np.maximum(den,1e-20)
            dg=np.einsum('j,hwj->hw',np.asarray(run.matriu)[1],native).astype('float32')*run.color['guany'][1]
            old=np.load(CAU/f'{g}_total.npy',mmap_mode='r')[...,1]
            new=np.nan_to_num(old,nan=0)+dg;np.save(D/f'{g}_corrected_G.npy',new);np.save(D/f'{g}_delta_G.npy',dg)
            good=(den[...,1]>0)&(old>0);rep[g]={'deltaG_p1_p50_p99':np.percentile(dg[good],[1,50,99]).tolist(),'nonpositive_in_original_good':int((good&(new<=0)).sum())};log('corrected source '+g)
            del native,dg,new,old,den,good
    # Reuse the physical pointing support, updating only its same-sky G match.
    a=np.load(D/'sony_A_corrected_G.npy',mmap_mode='r');b=np.load(D/'sony_B_corrected_G.npy',mmap_mode='r')
    pa=np.load(CAU/'sony_A_weights.npy',mmap_mode='r')[...,1];pb=np.load(CAU/'sony_B_weights.npy',mmap_mode='r')[...,1]
    factor=np.load(CAU/'sony_A_relative_factor_1.npy',mmap_mode='r');wa=np.load(CAU/'sony_A_blend_weight.npy',mmap_mode='r')
    r,_=coords();good=(pa>0)&(pb>0)&(a>0)&(b>0)&(r>1.2*RS)
    ghost=np.hypot(xx-GHOST_XY[0],yy-GHOST_XY[1]);good&=ghost>220
    residual=np.where(good,np.log(np.maximum(b,1e-8)/np.maximum(a*factor,1e-8)),0).astype('float32')
    small=(W//8,H//8);weight=cv2.resize(good.astype('float32'),small,interpolation=cv2.INTER_AREA)
    means=cv2.resize(residual,small,interpolation=cv2.INTER_AREA)
    low=gauss(means,16)/np.maximum(gauss(weight,16),1e-8);correction=cv2.resize(low,(W,H),interpolation=cv2.INTER_LINEAR)
    factor=np.asarray(factor)*np.exp(correction);new=np.asarray(a)*factor*wa+np.asarray(b)*(1-wa)
    np.save(D/'sony_corrected_G.npy',new.astype('float32'));np.save(D/'sony_A_factor_G.npy',factor.astype('float32'))
    rep['pointing_match']='same observed sky; original B-primary weights; updated low-frequency ratio at physical overlap; no patch or radial crop'
    savejson(D/'source_correction_receipt.json',rep);log('all corrected G inputs ready')
if __name__=='__main__':main()
