from pathlib import Path
import struct,json,hashlib,ctypes as C,ctypes.util
import numpy as np
from scipy.ndimage import map_coordinates,binary_erosion,binary_dilation
O=Path('/private/tmp/v105_base_sources_20260926');D=Path('/private/tmp/eclipse_v104_diagnosi_20260926')
sources={'original':'/Volumes/Crucial/Capes interiors/CapesInteriors.psb','V5':'/Volumes/Crucial/Capes interiors/CapesInteriorsV5.psb','V104':'/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V104.psb'}
def icc(path):
 with open(path,'rb') as f:
  f.seek(26);n=struct.unpack('>I',f.read(4))[0];f.seek(n,1);n=struct.unpack('>I',f.read(4))[0];data=f.read(n)
 pos=0
 while pos<len(data):
  sig=data[pos:pos+4];rid=struct.unpack_from('>H',data,pos+4)[0];pos+=6
  n=data[pos];pos+=((n+1)+1)//2*2;n=struct.unpack_from('>I',data,pos)[0];pos+=4;value=data[pos:pos+n];pos+=(n+1)//2*2
  if rid==1039:return value
 raise KeyError('no embedded ICC')
profiles={k:icc(p) for k,p in sources.items()}
lib=C.CDLL(ctypes.util.find_library('lcms2'));lib.cmsOpenProfileFromMem.argtypes=[C.c_void_p,C.c_uint32];lib.cmsOpenProfileFromMem.restype=C.c_void_p
lib.cmsCreateTransform.argtypes=[C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32];lib.cmsCreateTransform.restype=C.c_void_p
lib.cmsDoTransform.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint32];lib.cmsDeleteTransform.argtypes=[C.c_void_p];lib.cmsCloseProfile.argtypes=[C.c_void_p]
lib.cmsGetProfileInfoASCII.argtypes=[C.c_void_p,C.c_int,C.c_char_p,C.c_char_p,C.c_void_p,C.c_uint32];lib.cmsGetProfileInfoASCII.restype=C.c_uint32
buffers={k:C.create_string_buffer(v) for k,v in profiles.items()};handles={k:lib.cmsOpenProfileFromMem(v,len(profiles[k])) for k,v in buffers.items()}
receipt={'library':ctypes.util.find_library('lcms2'),'engine':'LittleCMS native 16-bit interleaved RGB, TYPE_RGB_16','intent':'relative colorimetric (1)','black_point_compensation':False,'flags':'cmsFLAGS_NOOPTIMIZE 0x0100; preserve ICC transfer functions near black without optimized coarse shapers','profiles':{}}
for k,b in profiles.items():
 out=O/f'{k}_embedded.icc';out.write_bytes(b);buf=C.create_string_buffer(256);lib.cmsGetProfileInfoASCII(handles[k],0,b'en',b'US',buf,256)
 receipt['profiles'][k]={'source':sources[k],'file':str(out),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'description':buf.value.decode(errors='replace')}
TYPE_RGB_16=(4<<16)|(3<<3)|2
def convert(a,src,dst):
 a=np.ascontiguousarray(a,dtype=np.uint16);out=np.empty_like(a);transform=lib.cmsCreateTransform(handles[src],TYPE_RGB_16,handles[dst],TYPE_RGB_16,1,0x0100)
 assert transform
 lib.cmsDoTransform(transform,a.ctypes.data_as(C.c_void_p),out.ctypes.data_as(C.c_void_p),a.shape[0]*a.shape[1]);lib.cmsDeleteTransform(transform);return out
ox,oy=2764,1475;orig=np.load(O/'09_original_CapesInteriors_RGB.npy',mmap_mode='r')[oy:oy+1600,ox:ox+1600];v5=np.load(O/'09_CapesInteriorsV5_RGB.npy',mmap_mode='r')[oy:oy+1600,ox:ox+1600]
ident=convert(orig,'original','original');receipt['identity_RGB16_max_DN']=int(np.max(np.abs(ident.astype(int)-orig.astype(int))))
converted={'original':convert(orig,'original','V104'),'V5':convert(v5,'V5','V104')}
receipt['original_V5_profiles_identical']=profiles['original']==profiles['V5']
for k,v in converted.items():np.save(O/f'09_{k}_crop_AdobeRGB1998_uint16.npy',v)
by,ey,bx,ex=3077,4477,4677,6077;yy,xx=np.mgrid[by:ey,bx:ex];box=[by,ey,bx,ex]
a=np.load(D/'L303.npz');ref=np.stack([a[f'c{c}'] for c in range(3)],-1)[77:1477,77:1477].astype(float)/65535
r=json.loads((O/'original09_siftseed_to_current303_registration.json').read_text());H=np.array(r['target_canvas_to_source_local']);sx=H[0,0]*xx+H[0,1]*yy+H[0,2];sy=H[1,0]*xx+H[1,1]*yy+H[1,2]
mask_native=np.any(orig!=v5,axis=-1);edit=map_coordinates(mask_native.astype(float),[sy,sx],order=1,mode='constant',cval=0)>0.5
interior_edit=binary_erosion(edit,iterations=2);control=binary_dilation(edit,iterations=35)&~binary_dilation(edit,iterations=5)
warped={k:np.stack([map_coordinates(v[...,c].astype(float)/65535,[sy,sx],order=1,mode='constant',cval=np.nan,prefilter=False) for c in range(3)],-1) for k,v in converted.items()}
receipt['patch_compare']={'edited_pixels_target':int(edit.sum()),'interior_edit_pixels':int(interior_edit.sum()),'same_transform_both_sources':True,'metrics':{}}
for k,v in warped.items():
 receipt['patch_compare']['metrics'][k]={}
 for label,z in [('edit',edit),('interior_edit',interior_edit),('adjacent_control',control)]:
  e=v[z]-ref[z];receipt['patch_compare']['metrics'][k][label]={'n':int(z.sum()),'RMSE_RGB_DN16':np.sqrt(np.mean(e**2,axis=0)).__mul__(65535).tolist(),'median_abs_RGB_DN16':np.median(np.abs(e),axis=0).__mul__(65535).tolist(),'median_error_RGB_DN16':np.median(e,axis=0).__mul__(65535).tolist()}
 np.savez_compressed(O/f'09_{k}_AdobeRGB1998_registered_to_current303.npz',RGB=v.astype('float32'),support_sampled=np.isfinite(v).all(-1),box=box,source_manual_patch=edit,metadata_json=json.dumps({'profile_receipt':'ICC_AND_PATCH_RECEIPT.json','registration':'original09_siftseed_to_current303_registration.json','source':k,'color_space':'Adobe RGB (1998)','interpolation':'bilinear after native 16-bit ICC conversion'}))
# Independent common E2975 geometry from direct coronal fit, no lunar contour fitting.
r=json.loads((O/'original09_direct_to_E2975_registration.json').read_text());H=np.array(r['target_canvas_to_source_local']);sx=H[0,0]*xx+H[0,1]*yy+H[0,2];sy=H[1,0]*xx+H[1,1]*yy+H[1,2]
q=np.load(O/'572A2975.npz')
for k,v in converted.items():
 rgb=np.stack([map_coordinates(v[...,c].astype(float)/65535,[sy,sx],order=1,mode='constant',cval=np.nan,prefilter=False) for c in range(3)],-1).astype('float32')
 np.savez_compressed(O/f'09_{k}_AdobeRGB1998_registered_to_E2975.npz',RGB=rgb,support_sampled=np.isfinite(rgb).all(-1),dreal2975=q['dreal'],valid_RGB2975=q['valid_rgb'],box=box,metadata_json=json.dumps({'profile_receipt':'ICC_AND_PATCH_RECEIPT.json','registration':'original09_direct_to_E2975_registration.json','source':k,'color_space':'Adobe RGB (1998)','interpolation':'bilinear after native 16-bit ICC conversion','physical_support_note':'support_sampled is geometric; dreal2975 is separate physical diagnosis, not original stack support'}))
(O/'ICC_AND_PATCH_RECEIPT.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
for h in handles.values():lib.cmsCloseProfile(h)
