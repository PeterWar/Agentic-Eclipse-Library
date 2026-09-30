"""Independent ICC chromaticity and native P01 clipping measurements; TMP only."""
from pathlib import Path
import json, struct, hashlib, sys
import numpy as np
import tifffile
ROOT=Path('/Users/USUARI/Desktop/Eclipse 2026')
P=Path('/private/tmp/v105_root_pilots_20260926')
OUT=Path('/private/tmp/v105_qa_20260926')
sys.path.insert(0,str(ROOT/'3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat
q=np.load(P/'P04/Q_OBSERVED.npz'); base=np.load(P/'P04/BASE_ROI.npz')
y0,y1,x0,x1=map(int,q['box']);box=(x0,y0,x1,y1)
old=Estat(ROOT/'4-RESULTATS/v103_banda_20260926/E/estat_v103').rgb(3,box).astype(float)
new=base['base_rgb_u16'].astype(float)/65535;w=base['replacement_weight']
icc=Path('/private/tmp/v105_base_sources_20260926/V104_embedded.icc').read_bytes()
gammas={}
for j in range(struct.unpack_from('>I',icc,128)[0]):
    tag,offset,length=struct.unpack_from('>4sII',icc,132+12*j)
    if tag in [b'rTRC',b'gTRC',b'bTRC']:
        assert icc[offset:offset+4]==b'curv'
        assert struct.unpack_from('>I',icc,offset+8)[0]==1
        gammas[tag.decode()]=struct.unpack_from('>H',icc,offset+12)[0]/256
gamma=gammas['rTRC']; assert len(set(gammas.values()))==1
def srgb_decode(a):return np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4)
def chrom(a):return a/np.maximum(a.sum(-1)[...,None],1e-30)
def st(a):
    a=np.asarray(a);a=a[np.isfinite(a)]
    return {'n':int(a.size),'p01_p16_p50_p84_p99':np.percentile(a,[1,16,50,84,99]).tolist()if len(a)else None,
     'min':float(a.min())if len(a)else None,'max':float(a.max())if len(a)else None}
yy,xx=np.mgrid[y0:y1,x0:x1];cx,cy,r=q['centre'];d=np.hypot(xx-cx,yy-cy)-r
th=np.degrees(np.arctan2(-(yy-cy),xx-cx))%360
origlin=old**gamma;newlin=new**gamma
valid=(w>0)&np.all(old>.01,-1)
report={'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in [P/'P04/make_base_scalar.py']if p.exists()},
 'ICC_TRC_gamma':gammas,'ICC_TRC_is_srgb':False,
 'P04_config':json.loads(str(base['configuration_json'])),
 'P04_chroma':{},'P01_native_clip':{}}
for lo,hi in [(0,3),(3,10),(10,25),(25,50),(50,150)]:
    m=valid&(d>=lo)&(d<hi)
    true_delta=chrom(newlin)-chrom(origlin)
    pseudo_delta=chrom(srgb_decode(new))-chrom(srgb_decode(old))
    report['P04_chroma'][f'{lo}-{hi}']={
      'linear_AdobeRGB_chromaticity_absolute_difference':{c:st(true_delta[...,i][m])for i,c in enumerate('RGB')},
      'pseudolinear_srgb_chromaticity_absolute_difference':{c:st(pseudo_delta[...,i][m])for i,c in enumerate('RGB')},
      'true_linear_G_over_R_relative_percent':st(100*((newlin[...,1]/np.maximum(newlin[...,0],1e-30))/(origlin[...,1]/np.maximum(origlin[...,0],1e-30))-1)[m]),
      'true_linear_B_over_R_relative_percent':st(100*((newlin[...,2]/np.maximum(newlin[...,0],1e-30))/(origlin[...,2]/np.maximum(origlin[...,0],1e-30))-1)[m])}
nb=P/'P01/native'
oldnative=tifffile.imread(nb/'baseline_lluna.tif');newnative=tifffile.imread(nb/'V105_reobert_lluna.tif')
assert oldnative.dtype==np.uint16 and newnative.shape==oldnative.shape==(1550,1550,3)
yn,xn=np.mgrid[3000:4550,4600:6150];dn=np.hypot(xn-cx,yn-cy)-r
tn=np.degrees(np.arctan2(-(yn-cy),xn-cx))%360
alpha=np.load('/private/tmp/eclipse_v104_diagnosi_20260926/L258.npz')['c-1'].astype(float)/65535
for i,c in enumerate('RGB'):
    newclip=(newnative[...,i]==65535)&(oldnative[...,i]<65535)
    oldclip=oldnative[...,i]==65535
    ny,nx=np.nonzero(newclip)
    report['P01_native_clip'][c]={'old_clipped':int(oldclip.sum()),'new_total_clipped':int((newnative[...,i]==65535).sum()),
       'newly_clipped':int(newclip.sum()),'old_values_at_new_clip':st(oldnative[...,i][newclip]),
       'd_presentation':st(dn[newclip]),'display_alpha':st(alpha[newclip]),
       'bounding_global_xyxy':[int(nx.min()+4600),int(ny.min()+3000),int(nx.max()+4601),int(ny.max()+3001)] if len(nx) else None,
       'by_sector30deg':{str(k):int((newclip&(tn>=k)&(tn<k+30)).sum())for k in range(0,360,30)},
       'by_band':{f'{a}-{b}':int((newclip&(dn>=a)&(dn<b)).sum())for a,b in [(-10,0),(0,2),(2,5),(5,10),(10,25),(25,50),(50,150),(150,1000)]},
       'outside150':int((newclip&(dn>=150)).sum()),'opaque_moon':int((newclip&(alpha>=.95)).sum())}
report['P01_outside150_composite_delta_DN']={c:st(newnative[...,i][dn>=150].astype(int)-oldnative[...,i][dn>=150].astype(int))for i,c in enumerate('RGB')}
report['note']='P01 clipping and nonlocal composite response do not establish that observed RAW data are clipped. They are native presentation failures.'
(OUT/'P04_COLOR_AND_P01_CLIP_AUDIT.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'ICC_TRC_gamma':gammas,'P01_native_clip':report['P01_native_clip'],
 'P04_chroma_0_3':report['P04_chroma']['0-3']},indent=2))
