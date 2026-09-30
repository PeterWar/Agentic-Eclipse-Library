"""Freeze the user-saved V49 and measure its changes without editing pixels."""
from reveal_common import *
from psd_tools import PSDImage
from PIL import Image
import shutil
expected='fc22af4660c7ac7aeb10a1433f1c159a91968fed70646c4b9200bb5bf7748366'
assert sha(SOURCE)==expected and not SNAP.exists()
p=subprocess.run(['/bin/cp','-c',str(SOURCE),str(SNAP)],capture_output=True,text=True)
if p.returncode:
    assert not SNAP.exists();shutil.copyfile(SOURCE,SNAP)
assert sha(SNAP)==sha(SOURCE)==expected
s=PSDImage.open(SNAP);old=PSDImage.open(OLD);rows=[]
for l,o in zip(s,old):
    assert l.name==o.name
    compressed=[dict(id=int(i.id),sha256=hashlib.sha256(c.data).hexdigest()) for i,c in zip(l._record.channel_info,l._channels)]
    rows.append(dict(name=l.name,bbox=list(l.bbox),kind=l.kind,visible=l.visible,old_visible=o.visible,opacity=l.opacity,blend=str(l.blend_mode),channels=compressed,has_mask=l.has_mask(),tags=[str(t) for t in l._record.tagged_blocks.keys()]))
l=next(l for l in s if l.name==NAME);o=next(l for l in old if l.name==NAME);new=np.stack([channel(l,c) for c in range(3)],-1);previous=np.stack([channel(o,c) for c in range(3)],-1);np.save(OUT/'A0_Pere_moon_RGB16.npy',new);np.save(OUT/'A0_previous_moon_RGB16.npy',previous)
mask=channel(l,-2);oldmask=channel(o,-2);alpha=channel(l,-1);oldalpha=channel(o,-1)
np.save(OUT/'A0_inherited_mask_roi.npy',mask[Y0:Y0+N,X0:X0+N]);mask_same=bool(np.array_equal(mask,oldmask));alpha_same=bool(np.array_equal(alpha,oldalpha))
yy,xx=np.mgrid[:N,:N];r=np.hypot(xx-CX,yy-CY);stats=[]
for lo,hi in [(0,350),(350,420),(420,435),(435,449),(449,454),(454,460)]:
    use=(r>=lo)&(r<hi);a=new[use].astype(float).mean(-1);b=previous[use].astype(float).mean(-1)
    stats.append(dict(radius=[lo,hi],median_before_DN16=float(np.median(b)),median_Pere_DN16=float(np.median(a)),median_ratio=float(np.median(a/np.maximum(b,1))),delta_percentiles_DN16=np.percentile(a-b,[1,50,99]).tolist()))
Image.fromarray((new>>8).astype('uint8')).save(OUT/'A0_Pere_source.png');Image.fromarray((previous>>8).astype('uint8')).save(OUT/'A0_previous_source.png')
save('A0_reference.json',dict(method=__doc__,source=str(SOURCE),snapshot=str(SNAP),sha256=expected,bytes=SOURCE.stat().st_size,previous_source=str(OLD),previous_sha256=sha(OLD),canvas=list(s.size),depth=s.depth,layers=rows,source_mask_decoded_exact=mask_same,source_alpha_decoded_exact=alpha_same,source_rgb_changed=not np.array_equal(new,previous),source_regions=stats,CameraRaw='User reports exposure and blacks increased. Saved layer is raster pixels, no smart-filter descriptor; exact new slider values not asserted. Freeze actual saved RGB as aesthetic authority.',recommendation='Preserve this revealed face and enabled corona. Diagnose bright limb upstream; no painted ring or artificial darkening mask.',new_photographic_version=False))
assert mask_same and alpha_same
print('REFERENCE',expected,'mask and alpha unchanged; source RGB changed',flush=True);print(stats,flush=True)
