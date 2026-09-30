"""A33: verificació d'un PSB nou (rebut d'escriptura a argv[1]) contra V69.psb: estructura, canals intactes byte a byte, canals canviats = intenció, blocs globals i compost; lectura amb psd-tools; vistes del fitxer escrit."""
import sys, os, json, struct, hashlib, logging, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad')
from psb69 import PSB
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'
esc0=json.load(open(sys.argv[1])); A=esc0['font']['path']; B=esc0['nou']['path']
esc=esc0; CANVIS={int(k):v for k,v in esc['canvis'].items()}; FONTS={int(k):v for k,v in esc['fonts'].items()}; OCULTES=esc['ocultes']; ROI=esc['roi']; x0,y0,x1,y1=ROI
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
    if la['id'] in OCULTES:
        if lb['visible']: err(f"{la['id']} hauria de ser oculta")
    elif la['visible']!=lb['visible']: err(f"capa {la['id']}: visibilitat canviada")
    if la['id'] in CANVIS: pass
    elif la['name']!=lb['name']: err(f"capa {la['id']}: nom canviat {la['name']!r} → {lb['name']!r}")
    for cid,(offa,na) in la['chans'].items():
        offb,nb=lb['chans'][cid]
        if la['id'] in CANVIS and f'c{cid}' in CANVIS[la['id']]:
            fa,_=pa.channel(la['id'],cid); fb,org=pb.channel(la['id'],cid); v=np.load(FONTS[la['id']])[f'c{cid}']
            ox,oy=org; hgt,wid=fa.shape; xa,ya=max(x0,ox),max(y0,oy); xb,yb=min(x1,ox+wid),min(y1,oy+hgt)
            dins_ok=np.array_equal(fb[ya-oy:yb-oy,xa-ox:xb-ox],v[ya-y0:yb-y0,xa-x0:xb-x0]); m=np.ones(fa.shape,bool); m[ya-oy:yb-oy,xa-ox:xb-ox]=False; fora_ok=np.array_equal(fa[m],fb[m])
            if not (dins_ok and fora_ok): err(f"capa {la['id']} canal {cid}: dins {dins_ok} fora {fora_ok}")
            n_ch+=1
        else:
            if na!=nb or h(A,offa,na)!=h(B,offb,nb): err(f"capa {la['id']} canal {cid}: dades canviades")
            else: n_id+=1
print('canals intactes byte a byte:',n_id,'· canals canviats verificats (ROI = intenció, fora = V69):',n_ch)
# blocs globals: tot el que hi ha després del bloc Lr16 (fins a la secció d'imatge) ha de ser idèntic; i tot el d'abans del camp de longitud de Lr16 llevat de la longitud de L&M
def blocs(path):
    with open(path,'rb') as f:
        f.seek(26); n=struct.unpack('>I',f.read(4))[0]; f.seek(n,1); n=struct.unpack('>I',f.read(4))[0]; f.seek(n,1); lm=f.tell(); lml=struct.unpack('>Q',f.read(8))[0]; end=lm+8+lml
        n=struct.unpack('>Q',f.read(8))[0]; f.seek(n,1); n=struct.unpack('>I',f.read(4))[0]; f.seek(n,1)
        while f.tell()+12<=end:
            pos=f.tell(); sig,key=struct.unpack('>4s4s',f.read(8)); big=key in (b'LMsk',b'Lr16',b'Lr32',b'Layr',b'Mt16',b'Mt32',b'Mtrn',b'Alph',b'FMsk',b'lnk2',b'FEid',b'FXid',b'PxSD',b'cinf'); n=struct.unpack('>Q' if big else '>I',f.read(8 if big else 4))[0]; st=f.tell()
            if key==b'Lr16': lenpos=st-8; f.seek(0); pre=f.read(lenpos); f.seek(st+(n+3)//4*4); post=f.read(end-f.tell()); return lm,pre,post,end
            f.seek(st+(n+3)//4*4)
lmA,preA,postA,endA=blocs(A); lmB,preB,postB,endB=blocs(B)
if preA[:lmA]!=preB[:lmB] or preA[lmA+8:]!=preB[lmB+8:]: err('capçalera/recursos/blocs anteriors a Lr16 diferents')
if postA!=postB: err('blocs globals després de Lr16 diferents')
else: print('blocs globals després de Lr16 idèntics (%d bytes); capçalera i recursos idèntics'%len(postA))
# compost: fora de la ROI idèntic; dins = intenció
Ca=pa.composite(); Cb=pb.composite(); m=np.ones(Ca.shape[:2],bool); m[y0:y1,x0:x1]=False
print('compost fora de la ROI idèntic:',np.array_equal(Ca[m],Cb[m]))
v=np.load(esc0.get('compost',SP+'/roi_compost_v71.npz')); Cc=v['C'].astype(np.float64)/65535; a=v['a'].astype(np.float64)/65535; esp=np.clip(Cc*a[...,None]+(1-a[...,None]),0,1)
d=np.abs(Cb[y0:y1,x0:x1,:3].astype(float)-esp*65535).max(); da=np.abs(Cb[y0:y1,x0:x1,3].astype(float)-a*65535).max(); print('compost dins la ROI: |dif| màx RGB %.1f DN16, alfa %.1f'%(d,da))
if d>1 or da>1: err('compost ROI')
# psd-tools llegeix el fitxer sencer
from psd_tools import PSDImage
ps=PSDImage.open(B); print('psd-tools: %dx%d, %d capes, profunditat %d, perfil ICC %d bytes'%(ps.width,ps.height,len(list(ps)),ps.depth,len(ps._record.image_resources.get_data(1039)) if ps._record.image_resources.get_data(1039) else 0))
for l in ps:
    lid=l.layer_id
    if lid in (51,76,218,3): print('  ',lid,repr(l.name),'visible',l.visible,'op',l.opacity,l.blend_mode)
l30=[l for l in ps if l.layer_id==30][0]; arr=l30.numpy('color'); v30=np.load(FONTS[30])['c0']; bb=l30.bbox
print('psd-tools capa 30 canal R (caixa) = intenció:',np.array_equal((arr[...,0]*65535+.5).astype(np.uint16),v30[bb[1]-y0:bb[3]-y0,bb[0]-x0:bb[2]-x0]))
# vistes del fitxer escrit: llenç sencer 1/6 i ROI 1:1 (sRGB)
from PIL import Image, ImageCms
src=ImageCms.ImageCmsProfile(SP+'/AdobeRGB.icc'); dst=ImageCms.createProfile('sRGB')
def srgb(arr): return ImageCms.profileToProfile(Image.fromarray(np.uint8(np.clip(arr,0,1)*255+.5)),src,dst,outputMode='RGB')
tag=os.path.basename(B).replace('.psb',''); srgb(Cb[::6,::6,:3].astype(np.float32)/65535).save(SP+f'/v_{tag}_llenc_x6.png'); srgb(Cb[y0:y1,x0:x1,:3].astype(np.float32)/65535).save(SP+f'/v_{tag}_roi_1a1.png')
rep['canals_intactes']=n_id; rep['canals_canviats']=n_ch; json.dump(rep,open(esc0.get('rebut',sys.argv[1]).replace('.json','_verificacio.json'),'w'),indent=1,ensure_ascii=False); print('VERIFICACIÓ',('PASSA' if rep['ok'] else 'FALLA'),rep['errors'])
