"""A25: verificació de V70.psb contra V69.psb: estructura, canals intactes byte a byte, canals canviats = intenció, blocs globals i compost; lectura amb psd-tools; vistes del fitxer escrit."""
import sys, os, json, struct, hashlib, logging, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from psb69 import PSB
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
A='/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V69.psb'; B='/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V70.psb'
esc=json.load(open(SP+'/a23_escriptura.json')); CANVIS={int(k):v for k,v in esc['canvis'].items()}; ROI=esc['roi']; x0,y0,x1,y1=ROI
pa,pb=PSB(A),PSB(B); rep={'ok':True,'errors':[]}
def err(m): rep['ok']=False; rep['errors'].append(m); print('ERROR',m)
assert (pa.width,pa.height,pa.channels,pa.depth,pa.mode)==(pb.width,pb.height,pb.channels,pb.depth,pb.mode)
assert len(pa.layers)==len(pb.layers)==27
def h(path,off,n):
    hh=hashlib.sha256()
    with open(path,'rb') as f:
        f.seek(off); rem=n
        while rem>0: b=f.read(min(rem,64<<20)); hh.update(b); rem-=len(b)
    return hh.hexdigest()
n_id=0; n_ch=0
for la,lb in zip(pa.layers,pb.layers):
    for k in ('id','left','top','right','bottom','opacity','blend','clipping','mask'):
        if la[k]!=lb[k]: err(f"capa {la['id']}: {k} {la[k]} != {lb[k]}")
    if la['id']==218:
        if lb['visible']: err('218 hauria de ser oculta')
    elif la['visible']!=lb['visible']: err(f"capa {la['id']}: visibilitat canviada")
    if la['id'] in CANVIS:
        if not lb['name'].endswith(' V70 '+esc['noms'][str(la['id'])]) and (' · V70' not in lb['name']): err(f"capa {la['id']}: nom sense sufix V70: {lb['name']!r}")
    elif la['name']!=lb['name']: err(f"capa {la['id']}: nom canviat {la['name']!r} → {lb['name']!r}")
    for cid,(offa,na) in la['chans'].items():
        offb,nb=lb['chans'][cid]
        if la['id'] in CANVIS and f'c{cid}' in CANVIS[la['id']]:
            fa,_=pa.channel(la['id'],cid); fb,org=pb.channel(la['id'],cid); v=np.load(SP+f"/roi_L{la['id']}_v70.npz")[f'c{cid}']
            ox,oy=org; hgt,wid=fa.shape; xa,ya=max(x0,ox),max(y0,oy); xb,yb=min(x1,ox+wid),min(y1,oy+hgt)
            dins_ok=np.array_equal(fb[ya-oy:yb-oy,xa-ox:xb-ox],v[ya-y0:yb-y0,xa-x0:xb-x0]); m=np.ones(fa.shape,bool); m[ya-oy:yb-oy,xa-ox:xb-ox]=False; fora_ok=np.array_equal(fa[m],fb[m])
            if not (dins_ok and fora_ok): err(f"capa {la['id']} canal {cid}: dins {dins_ok} fora {fora_ok}")
            n_ch+=1
        else:
            if na!=nb or h(A,offa,na)!=h(B,offb,nb): err(f"capa {la['id']} canal {cid}: dades canviades")
            else: n_id+=1
print('canals intactes byte a byte:',n_id,'· canals canviats verificats (ROI = intenció, fora = V69):',n_ch)
# blocs globals després de Lr16 i seccions anteriors
with open(A,'rb') as f, open(B,'rb') as g:
    f.seek(26); n=struct.unpack('>I',f.read(4))[0]; f.seek(n,1); n=struct.unpack('>I',f.read(4))[0]; f.seek(n,1); lm=f.tell()
    f.seek(0); g.seek(0); assert f.read(lm)==g.read(lm), 'capçalera/recursos diferents'
    f.seek(lm+8); g.seek(lm+8); assert f.read(20052-lm-8)==g.read(20052-lm-8), 'info de capes/màscara global/Mt16 diferents'
    f.seek(20052); la=struct.unpack('>Q',f.read(8))[0]; g.seek(20052); lb=struct.unpack('>Q',g.read(8))[0]
    ea=20060+(la+3)//4*4; eb=20060+(lb+3)//4*4; f.seek(ea); g.seek(eb); ga=f.read(pa.image_data_offset-ea); gb=g.read(pb.image_data_offset-eb)
    if ga!=gb: err('blocs globals (LMsk…cinf) diferents')
    else: print('blocs globals LMsk/Pat2/CAI/OCIO/GenI/FMsk/cinf idèntics (%d bytes)'%len(ga))
# compost: fora de la ROI idèntic; dins = intenció
Ca=pa.composite(); Cb=pb.composite(); m=np.ones(Ca.shape[:2],bool); m[y0:y1,x0:x1]=False
print('compost fora de la ROI idèntic:',np.array_equal(Ca[m],Cb[m]))
v=np.load(SP+'/roi_compost_v70.npz'); Cc=v['C'].astype(np.float64)/65535; a=v['a'].astype(np.float64)/65535; esp=np.clip(Cc*a[...,None]+(1-a[...,None]),0,1)
d=np.abs(Cb[y0:y1,x0:x1,:3].astype(float)-esp*65535).max(); da=np.abs(Cb[y0:y1,x0:x1,3].astype(float)-a*65535).max(); print('compost dins la ROI: |dif| màx RGB %.1f DN16, alfa %.1f'%(d,da))
if d>1 or da>1: err('compost ROI')
# psd-tools llegeix el fitxer sencer
from psd_tools import PSDImage
ps=PSDImage.open(B); print('psd-tools: %dx%d, %d capes, profunditat %d, perfil ICC %d bytes'%(ps.width,ps.height,len(list(ps)),ps.depth,len(ps._record.image_resources.get_data(1039)) if ps._record.image_resources.get_data(1039) else 0))
for l in ps:
    lid=l.layer_id
    if lid in (51,76,218,3): print('  ',lid,repr(l.name),'visible',l.visible,'op',l.opacity,l.blend_mode)
l51=[l for l in ps if l.layer_id==51][0]; arr=l51.numpy('color'); v51=np.load(SP+'/roi_L51_v70.npz')['c0']
print('psd-tools capa 51 canal R ROI = intenció:',np.array_equal((arr[y0:y1,x0:x1,0]*65535+.5).astype(np.uint16),v51))
# vistes del fitxer escrit: llenç sencer 1/6 i ROI 1:1 (sRGB)
from PIL import Image, ImageCms
src=ImageCms.ImageCmsProfile(SP+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
srgb(Cb[::6,::6,:3].astype(np.float32)/65535).save(SP+'/v_V70_llenc_x6.png'); srgb(Cb[y0:y1,x0:x1,:3].astype(np.float32)/65535).save(SP+'/v_V70_roi_1a1.png')
srgb(Ca[y0:y1,x0:x1,:3].astype(np.float32)/65535).save(SP+'/v_V69_roi_1a1.png')
rep['canals_intactes']=n_id; rep['canals_canviats']=n_ch; json.dump(rep,open(SP+'/a25_verificacio.json','w'),indent=1,ensure_ascii=False); print('VERIFICACIÓ',('PASSA' if rep['ok'] else 'FALLA'),rep['errors'])
