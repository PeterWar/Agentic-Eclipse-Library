"""Restore photographed substrate under K0 in the exact V49 solar context.
Equivalent to adding the original unmasked layer10 in existing LIGHTEN mode.
Keep current source, prominences and all brighter context pixel channels.
Diagnostic only, not yet geometrically or photographically qualified.
"""
from common50 import *
from PIL import Image
bg=np.load(V49/'A2_sense_font_lunar_RGB16.npy').astype(float);actual=np.load(V49/'A2_Pere_actual_RGB16.npy').astype(float);moon=np.load(V49/'A0_Pere_moon_RGB16.npy').astype(float);mask=np.load(OUT/'K0_geometric_mask_u16.npy').astype(float)/65535;orig=dict(np.load(OUT/'L4_original_10.npz'));solar=np.maximum(bg,orig['rgb']*orig['alpha'][...,None].astype(float)/65535);new=moon*mask[...,None]+solar*(1-mask[...,None]);np.save(OUT/'N2_composite_RGB16.npy',np.rint(np.clip(new,0,65535)).astype(np.uint16));np.save(OUT/'N2_background_RGB16.npy',np.rint(solar).astype(np.uint16))
ims=[Image.fromarray((np.clip(z,0,65535).astype(np.uint16)>>8).astype('uint8')) for z in [actual,new]]
for name,box in {'right':(1040,430,1220,940),'left':(165,420,365,960),'top':(370,170,990,365),'bottom':(400,1030,970,1230),'full':(0,0,N,N)}.items():
 a,b=[im.crop(box) for im in ims];out=Image.new('RGB',(a.width*2,a.height));out.paste(a,(0,0));out.paste(b,(a.width,0));out.save(OUT/f'N2_{name}.png')
save('N2_context_restore.json',dict(method=__doc__,old_solar_channels_never_darken=bool(np.all(solar>=bg)),original_Moon_RGB_exact=True,new_source_substrate='original V42 layer10 RGB, no user mask, same bbox',solar_changed_pixels=int(np.sum(np.any(solar!=bg,axis=-1))),status='diagnostic, no PSB'))
