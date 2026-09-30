"""Composition cause ablation: additive display weight versus Moon coverage.
V44 additive display response was reused as NORMAL alpha in V45..V49. Replace
only that non-geometric support by the already measured Vixen pixel coverage.
Same contour, centre, canvas and exact saved Pere RGB. This is a diagnostic;
independent boundary and visible/prominence checks are required before V50.
"""
from common50 import *
from PIL import Image,ImageDraw
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');old=np.load(V49/'A0_inherited_mask_roi.npy').astype(float)/65535;rgb=np.load(V49/'A0_Pere_moon_RGB16.npy').astype(float);bg=np.load(V49/'A2_sense_font_lunar_RGB16.npy').astype(float);actual=np.load(V49/'A2_Pere_actual_RGB16.npy').astype(float)
y,x=np.mgrid[:N,:N];phi=np.arctan2(y-CY,x-CX)%(2*np.pi);r=np.hypot(x-CX,y-CY);d=r-np.interp(phi*len(edge)/(2*np.pi),np.arange(len(edge)),edge,period=len(edge));masks={};rows=[]
for q in [4,16]:
 geo=np.zeros((N,N));offsets=(np.arange(q)+.5)/q-.5
 # Only boundary pixels require quadrature; exact constant coverage elsewhere.
 geo[d<-2]=1;band=abs(d)<=2;xx=x[band];yy=y[band];cov=np.zeros(len(xx))
 for oy in offsets:
  for ox in offsets:
   a=np.arctan2(yy+oy-CY,xx+ox-CX)%(2*np.pi);limit=np.interp(a*len(edge)/(2*np.pi),np.arange(len(edge)),edge,period=len(edge));cov+=np.hypot(xx+ox-CX,yy+oy-CY)<limit
 geo[band]=cov/(q*q);masks[q]=np.minimum(old,geo)
new=masks[16];comp=bg*(1-new[...,None])+rgb*new[...,None];base=bg*(1-old[...,None])+rgb*old[...,None];err=float(np.max(abs(base-actual)));assert err<=4,err
np.save(OUT/'K0_geometric_mask_u16.npy',np.rint(new*65535).astype(np.uint16));np.save(OUT/'K0_composite_RGB16.npy',np.rint(comp).astype(np.uint16))
before=Image.fromarray(np.rint(np.clip(actual/257,0,255)).astype('uint8'));after=Image.fromarray(np.rint(np.clip(comp/257,0,255)).astype('uint8'));before.save(OUT/'K0_before.png');after.save(OUT/'K0_after.png')
for label,box in {'top':(370,170,990,365),'right':(1040,430,1220,940),'bottom':(400,1030,970,1230),'left':(165,420,365,960)}.items():
 a=before.crop(box);b=after.crop(box);c=Image.new('RGB',(a.width*2,a.height));c.paste(a,(0,0));c.paste(b,(a.width,0));c.save(OUT/f'K0_{label}.png')
for lo,hi in [(-1000,-6),(-6,-2),(-2,-.5),(-.5,0),(0,2),(2,4),(4,8)]:
 use=(d>=lo)&(d<hi);rows.append(dict(distance=[lo,hi],pixels=int(use.sum()),old_equivalent_alpha=float(old[use].sum()),new_equivalent_alpha=float(new[use].sum()),old_luma=np.percentile(actual.mean(-1)[use],[5,50,95]).tolist(),new_luma=np.percentile(comp.mean(-1)[use],[5,50,95]).tolist()))
save('K0_geometric_coverage.json',dict(method=__doc__,saved_Pere_RGB_unchanged=True,baseline_reproduction_max_DN16=err,subpixel_quadrature=16,original_export_quadrature=4,quadrature_difference_equivalent_pixels=float(np.sum(abs(masks[16]-masks[4]))),mask_never_increases=bool(np.all(new<=old)),regions=rows,status='Composition diagnostic, not yet a delivered correction'))
print('DONE',err,rows,flush=True)
