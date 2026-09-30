"""V49 reviewable source-sampling correction; all25 V48 layers preserved.
Only V48 source visibility changes; a new26th source inherits its full mask,
placement, blend and alpha. Same canvas. Not a claim of complete limb recovery.
"""
from full_delta_common import *
import sys,copy,gc,tifffile
from PIL import Image
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from c5_fonts_psb import C,PSDImage,fingerprint
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import Tag,Resource,Compression
NAME='V49 · graella verda nativa · Camera Raw de Pere'
OLDNAME='V48 · fonts CFA completes · Camera Raw de Pere'
TARGET=OUT/'Earthshine_V49.psb'
SOURCE=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V48.psb')
expectedsha='48715be427ebd5ea654eeea746e0a295201f9f0a354e4f5e37fbf40df47443a5'
with SOURCE.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expectedsha
assert not TARGET.exists()
assert json.loads((OUT/'C5_retention.json').read_text())['no_lost_old_triples']
s=PSDImage.open(SOURCE);assert len(s)==25 and s.size==(10551,7506) and s.depth==16 and s.version==2
before=[fingerprint(l) for l in s];l=next(l for l in s if l.name==OLDNAME);assert l.visible and l.opacity==255 and l.blend_mode==C.BlendMode.NORMAL
old=np.stack([C.channel(l,c) for c in range(3)],-1);new=np.load(OUT/'C3_candidate_rgb.npy');assert np.array_equal(old,np.load(SRC/'C3_candidate_rgb.npy'))
m=C.channel(l,-2);md=l._record.mask_data;assert m.shape==(7506,10551) and (md.left,md.top)==(0,0) and not md.flags.mask_disabled and not md.flags.invert_mask
mr=m[Y0:Y0+N,X0:X0+N].astype(float)/65535;assert np.array_equal(m[Y0:Y0+N,X0:X0+N],np.load(SRC/'C4_inherited_mask_roi.npy'));del m
nl=PixelLayer(s,copy.deepcopy(l._record),copy.deepcopy(l._channels))
for tag in (Tag.LAYER_ID,Tag.METADATA_SETTING):
    if tag in nl._record.tagged_blocks:del nl._record.tagged_blocks[tag]
for info,ch in zip(nl._record.channel_info,nl._channels):
    if int(info.id) in [0,1,2]:
        ch.compression=Compression.ZIP;ch.set_data(np.ascontiguousarray(new[...,int(info.id)].astype('>u2')).tobytes(),N,N,16,2);info.length=len(ch.data)+2
s.append(nl);nl.name=NAME;nl.visible=True;l.visible=False
if Resource.THUMBNAIL_RESOURCE in s._record.image_resources:del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
C.finalize_lr16(s)
a=tifffile.imread(SRC/'C4_Photoshop_RGBA.tif');assert a.shape==(7506,10551,4) and a.dtype==np.uint16
alpha=a[...,3].copy();comp=np.empty((7506,10551,3),np.uint16)
for y in range(0,7506,128):
    sl=slice(y,min(y+128,7506));comp[sl]=np.rint(np.clip(a[sl,:,:3].astype(float)*65535/np.maximum(alpha[sl,:,None],1),0,65535)).astype(np.uint16)
del a;assert np.all(alpha[Y0:Y0+N,X0:X0+N]==65535)
roi=comp[Y0:Y0+N,X0:X0+N];baseline=roi.copy();value=roi.astype(float)+(new.astype(float)-old)*mr[...,None];assert value.min()>=0 and value.max()<=65535
roi[:]=np.rint(value).astype(np.uint16);preview_difference=int(np.max(abs(roi.astype(int)-np.load(OUT/'C4_expected_moon.npy').astype(int))));assert preview_difference<=3;np.save(OUT/'E0_expected_moon.npy',roi);np.save(OUT/'E0_inherited_mask_roi.npy',np.rint(mr*65535).astype(np.uint16))
rgba=np.dstack([comp[::4,::4]>>8,alpha[::4,::4]>>8]).astype(np.uint8);Image.fromarray(rgba).save(OUT/'vistes/E0_full_canvas.png')
data=[np.ascontiguousarray(comp[...,c].astype('>u2')).tobytes() for c in range(3)]+[np.ascontiguousarray(alpha.astype('>u2')).tobytes()]
merged=C.ImageData(compression=Compression.RAW);merged.set_data(data,s._record.header);s._record.image_data=merged;s._updated=False;del comp,alpha,data;gc.collect()
with TARGET.open('xb') as f:s.save(f)
save('E0_build.json',dict(method=__doc__,source=str(SOURCE),source_sha256=expectedsha,target=str(TARGET),new_layer=NAME,old_source_layer=OLDNAME,source_layers=before,hidden_in_candidate=[OLDNAME],mask='Complete V48 source mask bytes and geometry inherited; empirical photographic join unchanged',new_photographic_delta=True,science_status='Native sampler improvement, no complete all-limb recovery claim',expected_composite='Actual native V48 RGBA recomposition plus full inherited-mask source delta',baseline_rgba=str(SRC/'C4_Photoshop_RGBA.tif'),preview_RGB_only_difference_max_DN16=preview_difference))
print('BUILT',TARGET,flush=True)
