"""Native stellar patches as an external optical witness, no limb pixels used.
Raw visible CFA coordinates; matched dark calibration not assumed from resized
historical star products. Fit local sky as nuisance later; save raw counts and
CFA identities now. Original RAW bytes never written.
"""
from common50 import *
import rawpy,time
P=Path('/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17/vixen');seeds=np.load(P/'cand.npy')[:8];shifts=json.loads((P/'shifts_start.json').read_text());RAW=Path('/Users/USUARI/Desktop/Eclipse 2026/Vixen R6III/Vixen Fase totalitat')
frames={'572A2978':1.,'572A2979':2.,'572A2980':2.,'572A2981':2.,'572A2982':10.,'572A2983':10.,'572A2984':10.,'572A2996':1.}
plan=dict(method=__doc__,frames=frames,stars=list(range(8)),patch_radius=32,linearity_ceiling=13500,training='Stars0,2,4,6; retain other stars and split epoch. First profile all to determine identifiability only; no limb correction based on this extraction.',background='Native observed counts with free local plane; future matched-dark alignment must be proved before use',raw_coordinates='visible, no crop correction inherited from 2x2 star archives')
save('D0_star_plan.json',plan);rows=[]
for stem,exp in frames.items():
 t=time.time();path=RAW/(stem+'.CR3')
 with rawpy.imread(str(path)) as raw:
  im=raw.raw_image_visible.copy();colors=raw.raw_colors_visible.copy();green=[i for i,c in enumerate(raw.color_desc.decode().strip('\0')) if c=='G'];shape=list(im.shape);black=list(raw.black_level_per_channel)
 for index,seed in enumerate(seeds):
  x=seed[0]+shifts[stem][1];y=seed[1]+shifts[stem][2];ix=int(round(x));iy=int(round(y));sl=(slice(iy-32,iy+33),slice(ix-32,ix+33));patch=im[sl];cc=colors[sl];YY,XX=np.mgrid[iy-32:iy+33,ix-32:ix+33];ok=np.isin(cc,green)&(patch<13500);f=OUT/f'D0_star_{stem}_{index}.npz'
  np.savez_compressed(f,x=XX[ok]-x,y=YY[ok]-y,raw=patch[ok],green=cc[ok],exp=exp,seed=np.array([x,y]),shape=shape,black=black)
  rr=np.hypot(XX-x,YY-y);sky=np.median(patch[np.isin(cc,green)&(rr>20)]);peak=patch[np.isin(cc,green)&(rr<5)].max();rows.append(dict(stem=stem,exp=exp,star_index=index,patch=str(f),samples=int(ok.sum()),censored_green=int((np.isin(cc,green)&~ok).sum()),sky_ADU=float(sky),peak_ADU=int(peak),raw_visible_shape=shape))
 receipts=dict(path=str(path),sha256=sha(path),black=black);save(f'D0_raw_{stem}.json',receipts);del im,colors;print(stem,shape,'done',time.time()-t,flush=True)
save('D0_star_inputs.json',dict(plan=plan,rows=rows))
