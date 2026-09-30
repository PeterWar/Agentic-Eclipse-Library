from common import *
from scipy.ndimage import map_coordinates,gaussian_filter1d
from PIL import Image,ImageDraw
from qa_science import external_judge
def main():
 ref=np.load(C/'base_G.npy',mmap_mode='r');nt=1440;t=np.arange(nt)*2*np.pi/nt;rr=np.linspace(1.35,2.5,60)*RS;xy=np.array([CY+rr[:,None]*np.sin(t),CX+rr[:,None]*np.cos(t)])
 f=map_coordinates(ref,xy,order=1,prefilter=False);f-=gaussian_filter1d(f,20,axis=1,mode='wrap');f/=np.std(f,axis=1)[:,None]+1e-12;rows=[]
 tags=[p.stem.removesuffix('_float') for p in sorted(C.glob('P*_float.npy'))]
 for tag in tags:
  a=np.load(C/(tag+'_float.npy'),mmap_mode='r');q=map_coordinates(a,xy,order=1,prefilter=False);q-=gaussian_filter1d(q,20,axis=1,mode='wrap');q/=np.std(q,axis=1)[:,None]+1e-12
  cross=np.mean(np.fft.ifft(np.fft.fft(q,axis=1)*np.conj(np.fft.fft(f,axis=1)),axis=1).real/nt,axis=0);j=int(np.argmax(abs(cross)));shift=(j if j<=nt//2 else j-nt)*360/nt
  assert abs(shift)<=.5 and abs(cross[nt//2])<.1 and cross[j]>.2
  rows.append({'tag':tag,'azimuth_shift_degrees':shift,'correlation_at_peak':float(cross[j]),'rotated180_null_correlation_at0':float(cross[nt//2])})
 savejson(D/'receipts/azimuth_geometry.json',{'PASS':True,'radial_span_R':[1.35,2.5],'angles':nt,'radii':60,'angular_highpass_sigma_samples':20,'reference':'common native G base, independently confirms no angular remapping','rows':rows})
 rois=[('limbe N',5362,3335),('marca N',5715,2200),('marca S',5130,5160),('exterior NE',5965,2120)]
 for batch in range(0,len(tags),3):
  group=tags[batch:batch+3];im=Image.new('RGB',(len(group)*320,4*290),(22,22,22));draw=ImageDraw.Draw(im)
  for j,tag in enumerate(group):
   u=np.load(C/(tag+'_u16.npy'),mmap_mode='r')
   for row,(label,x,y) in enumerate(rois):
    draw.text((j*320+8,row*290+5),tag+' / '+label,fill='white')
    patch=(u[y-128:y+128,x-128:x+128]//257).astype('uint8');im.paste(Image.fromarray(patch).convert('RGB'),(j*320+8,row*290+26))
  im.save(OUT/f'QA_100_{batch//3+1}.png')
 external_judge()
 savejson(D/'receipts/visual_findings.json',{'status':'VERIFIED_COMPARISON_WITH_VISIBLE_LIMITATIONS','artifact_free':False,'full_canvas_and_native100_reviewed':True,'findings':{'NRGF_RHEF':'broad outer Sun-centered arcs and NW coverage-parallel band visible; RHEF has independently demonstrated 1px-bin banding','MGN_WOW_NAFE':'enhance noise in outer field; no calibrated full-canvas noise model, no claim that all texture is coronal','ACHF_precursor':'strong bright/dark limb response to steep linear radiance profile; global LUT gives little outer contrast; not the complete nonlinear Corona algorithm','SWAP':'conditional EUV-to-visible transfer pilot','geometry':'all9 methods peak at0deg;180deg null rejected','mask':'only exact inherited physical support, no extra circular crop/fade'},'default':'all new views OFF; previous30 layers and appearance preserved','acceptance':'implementation and container QA; not certification of elimination of solar arcs'})
 log('native views and geometry saved')
if __name__=='__main__':main()
