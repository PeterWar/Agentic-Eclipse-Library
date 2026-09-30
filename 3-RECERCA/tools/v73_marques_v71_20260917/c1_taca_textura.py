"""C1: la textura de la taca: amplitud i correlació amb LROC i amb el RAW per bandes (8–16, 16–32, 32–64 px) dins la regió marcada contra la resta del disc; mapa local de correlació capa~LROC (finestres 96 px, banda 8–48)."""
import sys, json, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'; S3='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
sys.path.insert(0,NEW)
from scipy.ndimage import gaussian_filter, uniform_filter
from PIL import Image
CX,CY,RS=998.88,998.41,456.0; Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); disc=rr<RS-20
L69=np.dstack([np.load(OLD+'/roi_L30.npz')[c] for c in ('c0','c1','c2')]).astype(np.float64).mean(-1)/65535
L72=np.dstack([np.load(NEW+'/roi72_L30.npz')[c] for c in ('c0','c1','c2')]).astype(np.float64).mean(-1)/65535
L62=np.dstack([np.load(NEW+'/roi71_L62.npz')[c] for c in ('c0','c1','c2')]).astype(np.float64).mean(-1)/65535; v62=np.load(NEW+'/roi71_L62.npz')['c-1']>30000
M=np.load(OLD+'/raw_disc_norm_2000.npy').astype(np.float64); Mv=np.isfinite(M); M=np.nan_to_num(M,nan=1.0)
m7=np.load(NEW+'/marques_219.npz'); Mk=np.zeros((2000,2000),np.float32); mx,my=int(m7['x0'])-4377,int(m7['y0'])-2777; Mk[my:my+m7['A'].shape[0],mx:mx+m7['A'].shape[1]]=m7['A']/65535
R7=np.zeros((2000,2000),bool); R7[3928-2777:4132-2777,5187-4377:5418-4377]=Mk[3928-2777:4132-2777,5187-4377:5418-4377]>0.03
resta=disc&v62&~R7&Mv; dins=R7&v62&Mv
def band(A,lo,hi): return gaussian_filter(A,lo)-gaussian_filter(A,hi)
print('banda      | amplitud rms capa72 dins/resta | corr capa72~LROC dins / resta | corr capa72~RAW dins / resta | corr RAW~LROC dins / resta | corr capa69~capa72 dins')
for lo,hi in ((4,8),(8,16),(16,32),(32,64)):
    b72=band(L72,lo,hi); b69=band(L69,lo,hi); b62=band(L62,lo,hi); bM=band(M,lo,hi)
    c=lambda a,b,m: np.corrcoef(a[m],b[m])[0,1]
    print(f'{lo:2d}–{hi:2d} px   | {b72[dins].std()/b72[resta].std():5.2f}                       | {c(b72,b62,dins):+.3f} / {c(b72,b62,resta):+.3f}            | {c(b72,bM,dins):+.3f} / {c(b72,bM,resta):+.3f}          | {c(bM,b62,dins):+.3f} / {c(bM,b62,resta):+.3f}        | {c(b69,b72,dins):+.3f}')
# mapa local de correlació capa72~LROC (banda 8–48) en finestres de 96 px
b72=band(L72,8,48); b62=band(L62,8,48); w=96
num=uniform_filter(b72*b62,w); d1=uniform_filter(b72*b72,w); d2=uniform_filter(b62*b62,w); cmap=num/np.sqrt(np.maximum(d1*d2,1e-12)); cmap[~(disc&v62)]=0
print('correlació local capa72~LROC 8–48 px: mediana al disc %.2f · dins la marca %.2f · percentil 10 del disc %.2f'%(np.median(cmap[disc&v62&(rr<RS-70)]),np.median(cmap[R7]),np.percentile(cmap[disc&v62&(rr<RS-70)],10)))
bM2=band(M,8,48); num=uniform_filter(bM2*b62,w); d1=uniform_filter(bM2*bM2,w); cmapR=num/np.sqrt(np.maximum(d1*d2,1e-12)); cmapR[~(disc&v62&Mv)]=0
print('correlació local RAW~LROC 8–48 px: mediana al disc %.2f · dins la marca %.2f'%(np.median(cmapR[disc&v62&Mv&(rr<RS-70)]),np.median(cmapR[R7&Mv])))
# vistes ×2 de la regió (finestra 400 px centrada a la marca): capa69 | capa72 | RAW σ2 | LROC (banda 8–64 + suau), i mapa de correlació local
cx,cy=int(np.mean(np.nonzero(R7)[1])),int(np.mean(np.nonzero(R7)[0])); x0,y0=cx-200,cy-200
def pb(A,mask): h=band(A,3,64); s=np.std(h[mask]); return np.clip(0.5+h/(4*s),0,1)
pan=np.concatenate([pb(L69,disc)[y0:y0+400,x0:x0+400],pb(L72,disc)[y0:y0+400,x0:x0+400],pb(M,disc&Mv)[y0:y0+400,x0:x0+400],pb(L62,disc&v62)[y0:y0+400,x0:x0+400],np.clip(0.5+cmap[y0:y0+400,x0:x0+400]/2,0,1)],1)
Image.fromarray(np.uint8(pan*255)).resize((pan.shape[1]*2,pan.shape[0]*2),Image.Resampling.NEAREST).save(S3+'/v_C1_taca_textura.png')
Image.fromarray(np.uint8(np.clip(0.5+cmap/2,0,1)*255)).save(S3+'/v_C1_corrmap_lroc.png'); print('fet')
