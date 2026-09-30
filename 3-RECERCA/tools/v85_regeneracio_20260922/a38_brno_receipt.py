"""Persist the peer-reviewed Brno angular-morphology diagnostic. No refitting."""
from a16_build_psb import *
from scipy.ndimage import map_coordinates,gaussian_filter1d

def main():
 meta=json.loads((R/'4-RESULTATS/v82_capes_brno_20260918/registre_v82.json').read_text());geo=json.loads((R/'3-RECERCA/tools/estudi_druckmuller/geometria.json').read_text());caps=json.loads((R/'4-RESULTATS/v82_capes_brno_20260918/capes_v82.json').read_text())
 rs=meta['RS_V'];cx,cy=meta['SUN_V'];rr=np.geomspace(1.15,2.4,60);n=2880;theta=np.arange(n)*2*np.pi/n;xx=cx+rr[:,None]*rs*np.cos(theta);yy=cy+rr[:,None]*rs*np.sin(theta)
 support=np.load(O/'domain_v1/sources/support.npy',mmap_mode='r');valid0=map_coordinates(support,[yy,xx],order=1,output=np.float32)>.999;del support
 psb=PSB(O/'V84_Pere_input.psb')
 def norm(a):
  z=a-np.median(a,axis=1,keepdims=True);return z/np.maximum(np.median(abs(z),axis=1,keepdims=True),1e-9)
 def band(a,lo,hi):
  f=np.fft.rfft(norm(a));f[:,:lo]=0;f[:,hi+1:]=0;return np.fft.irfft(f,n=n)
 def cor(a,b):return np.sum(a*b,axis=1)/np.sqrt(np.sum(a*a,axis=1)*np.sum(b*b,axis=1))
 ops=['P04_WOW','P03_MGN','P05_WOW_bilateral','01','04','05','06'];samples={};hashes={}
 for op in ops:
  samples[op]={}
  for run in ['baseline','selected']:
   p=(O/'filters_baseline/products/filters' if run=='baseline' else O/'filters_selected')/(op+'_u16.npy');a=np.load(p,mmap_mode='r');samples[op][run]=map_coordinates(a,[yy,xx],order=1,output=np.float32);del a;hashes[str(p.relative_to(R))]=sha(p)
 refs=[(230,'TSE_2026_200mm_DHS.png'),(231,'TSE_2026_400mm_DHS.png'),(232,'TSE_2026_530mm_DHS.png'),(233,'TSE2026_Trigaza_800mm.png')];counts=[];rows=[]
 for lid,name in refs:
  layer=psb.layer(lid);assert [layer[k] for k in ['left','top','right','bottom']]==caps[name]['bbox'];ref,org=psb.channel(lid,1);b=map_coordinates(ref,[yy-org[1],xx-org[0]],order=1,output=np.float32);del ref
  m=meta['imatges'][name];reg=m[caps[name]['tria']];A=np.vstack([reg['A_png_a_v'],[0,0,1]]);coord=np.linalg.inv(A)@np.stack([xx.ravel(),yy.ravel(),np.ones(xx.size)]);u,v=coord[:2].reshape(2,*xx.shape);g=geo[name];f0,f1,c0,c1=g['marc'];valid=valid0&(u>c0+1)&(u<c1-1)&(v>f0+1)&(v<f1-m['peu_files']-1);valid&=np.hypot(u-(g['cx']+c0),v-(g['cy']+f0))>g['R_lluna_px']+4;keep=valid.all(axis=1)
  counts.append({'reference':lid,'rings':int(keep.sum()),'samples':int(keep.sum()*n),'radial_min':float(rr[keep].min()),'radial_max':float(rr[keep].max())});sigma=np.maximum(n/(2*np.pi*rr*rs)*reg['escala']*.45,.3)
  for op in ops:
   z={run:np.stack([gaussian_filter1d(samples[op][run][i],s,mode='wrap') for i,s in enumerate(sigma)]) for run in samples[op]}
   for lo,hi in [(13,30),(31,80),(81,200)]:
    br=band(b[keep],lo,hi);f={run:band(z[run][keep],lo,hi) for run in z};c={run:cor(f[run],br) for run in z};base,e=c['baseline'],c['selected'];dd=e-base
    row={'ref':lid,'op':op,'band':[lo,hi],'baseline':float(base.mean()),'selected':float(e.mean()),'delta':float(dd.mean()),'selfcorr':float(cor(f['selected'],f['baseline']).mean()),'up':int((dd>1e-8).sum()),'down':int((dd< -1e-8).sum()),'same':int((abs(dd)<=1e-8).sum())};rows.append(row)
    if lid==233:
     row['radial']=[]
     for r0,r1 in [(1.15,1.35),(1.35,1.8),(1.8,2.400001)]:
      s=(rr[keep]>=r0)&(rr[keep]<r1);d=dd[s];row['radial'].append({'r':[r0,min(r1,2.4)],'n':int(s.sum()),'baseline':float(base[s].mean()),'selected':float(e[s].mean()),'delta':float(d.mean()),'up':int((d>1e-8).sum()),'down':int((d< -1e-8).sum())})
  print('BRNO_DONE',lid,flush=True)
 save(O/'BRNO_FINAL_QA.json',{'scope':'angular morphology at frozen V82 registration; not color or photometric truth','independent_peer_review':'limb_diagnosis original stdin runs; root persisted same diagnostic for final selected products','input_hashes':hashes,'counts':counts,'rows':rows,'scientific_PASS':None,'limitations':['no measured optical PSF; nominal Gaussian0.45PNG pixel sampling equalization only','four correlated published composites from same team','no evaluation below1.15R','median/MAD ring normalization removes radial pedestal','no new acceptance threshold fitted']})
if __name__=='__main__':guard();main()
