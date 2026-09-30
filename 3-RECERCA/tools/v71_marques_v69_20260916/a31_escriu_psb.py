"""A31: escriu un PSB nou (paràmetres en JSON: dst, canvis {lid: [canals]}, fonts {lid: npz}, noms {lid: sufix}, ocultes [lids], compost npz) a partir de V69.psb: bytes idèntics fora del bloc Lr16 (registres reserialitzats, canals modificats recodificats ZIP-predicció) i del compost (retall ROI sobre blanc). V69 intacte."""
import sys, os, io, json, struct, zlib, time, hashlib, logging, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from psb69 import PSB
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
P=json.load(open(sys.argv[1])); SRC='/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V69.psb'; DST=P['dst']
assert not os.path.exists(DST), 'no-clobber: el destí ja existeix'
ROI=(4377,2777,6377,4777); x0,y0,x1,y1=ROI
CANVIS={int(k):v for k,v in P['canvis'].items()}; FONTS={int(k):v for k,v in P['fonts'].items()}; OCULTES=P.get('ocultes',[]); COMPOST=P['compost']
NOMS={int(k):v for k,v in P['noms'].items()}
p=PSB(SRC); t0=time.time()
def codifica(arr):
    """ZIP amb predicció (codi 3) d'un array uint16 (h,w): delta per files sobre big-endian u16."""
    a=arr.astype(np.uint16); d=a.copy(); d[:,1:]=(a[:,1:].astype(np.int32)-a[:,:-1].astype(np.int32))&0xFFFF
    return struct.pack('>H',3)+zlib.compress(d.astype('>u2').tobytes(),6)
nou={}   # (lid,cid) -> bytes
for lid,chs in CANVIS.items():
    L=p.layer(lid); v=np.load(FONTS[lid])
    for ch in chs:
        cid=int(ch[1:]); full,org=p.channel(lid,cid); ox,oy=org; h,w=full.shape
        xa,ya=max(x0,ox),max(y0,oy); xb,yb=min(x1,ox+w),min(y1,oy+h)
        full=full.copy(); full[ya-oy:yb-oy,xa-ox:xb-ox]=v[ch][ya-y0:yb-y0,xa-x0:xb-x0]
        b=codifica(full); nou[(lid,cid)]=b
        # comprovació: descodifica i compara
        back=p._decode(b,w,h); assert np.array_equal(back,full),'codificació no reversible'
        print(f'  capa {lid} canal {cid}: {L["chans"][cid][1]} → {len(b)} bytes  ({time.time()-t0:.0f}s)',flush=True)
# registres
with open(SRC,'rb') as f:
    f.seek(26); n=struct.unpack('>I',f.read(4))[0]; f.seek(n,1); n=struct.unpack('>I',f.read(4))[0]; f.seek(n,1)
    lm_start=f.tell(); lm_len=struct.unpack('>Q',f.read(8))[0]; lm_end=lm_start+8+lm_len
    f.seek(20052); lr_len=struct.unpack('>Q',f.read(8))[0]; lr_data=20060; lr_end=lr_data+lr_len; lr_end_pad=lr_data+(lr_len+3)//4*4
    f.seek(lr_data); count=struct.unpack('>h',f.read(2))[0]; rec_start=f.tell(); recs=[LayerRecord.read(f,version=2) for _ in range(abs(count))]; rec_end=f.tell()
    assert rec_end==p.layers[0]['chans'][-1][0]
    for r in recs:
        lid=int(r.tagged_blocks.get_data(Tag.LAYER_ID))
        if lid in CANVIS:
            for c in r.channel_info:
                if (lid,int(c.id)) in nou: c.length=len(nou[(lid,int(c.id))])
            old=str(r.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME)); r.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME,old+' · '+NOMS[lid])
        if lid in OCULTES: r.flags.visible=False
    buf=io.BytesIO()
    for r in recs: r.write(buf,version=2)
    recbytes=buf.getvalue()
    total_ch=sum(c.length for r in recs for c in r.channel_info); new_lr_len=2+len(recbytes)+total_ch; new_lr_pad=(new_lr_len+3)//4*4
    new_lm_len=lm_len+(new_lr_pad-(lr_end_pad-lr_data))
    print('Lr16: %d → %d bytes; L&M: %d → %d; registres %d → %d bytes'%(lr_len,new_lr_len,lm_len,new_lm_len,rec_end-rec_start,len(recbytes)),flush=True)
    with open(DST,'wb') as g:
        f.seek(0); g.write(f.read(lm_start)); g.write(struct.pack('>Q',new_lm_len)); f.seek(lm_start+8); g.write(f.read(20052-(lm_start+8)))
        g.write(struct.pack('>Q',new_lr_len)); g.write(struct.pack('>h',count)); g.write(recbytes)
        for L in p.layers:
            for cid,(off,n) in L['chans'].items():
                if (L['id'],cid) in nou: g.write(nou[(L['id'],cid)])
                else:
                    f.seek(off); rem=n
                    while rem>0: b=f.read(min(rem,64<<20)); g.write(b); rem-=len(b)
        g.write(b'\0'*(new_lr_pad-new_lr_len))
        f.seek(lr_end_pad); rem=lm_end-lr_end_pad
        while rem>0: b=f.read(min(rem,64<<20)); g.write(b); rem-=len(b)
        img_off_new=g.tell(); assert lm_end==p.image_data_offset
        f.seek(lm_end); rem=os.path.getsize(SRC)-lm_end
        while rem>0: b=f.read(min(rem,64<<20)); g.write(b); rem-=len(b)
    print('copiat; compost a offset',img_off_new,'(%.0fs)'%(time.time()-t0),flush=True)
# retall del compost (raw, planar RGBA big-endian) sobre blanc
W,H,C=p.width,p.height,p.channels; assert C==4
v=np.load(COMPOST); Cc=v['C'].astype(np.float64)/65535; a=v['a'].astype(np.float64)/65535
rgbw=np.clip(Cc*a[...,None]+(1-a[...,None]),0,1); planes=[(rgbw[...,k]*65535+.5).astype('>u2') for k in range(3)]+[(a*65535+.5).astype('>u2')]
with open(DST,'r+b') as g:
    for k in range(4):
        for y in range(y0,y1):
            g.seek(img_off_new+2+((k*H+y)*W+x0)*2); g.write(planes[k][y-y0].tobytes())
print('compost retallat. Mida final',os.path.getsize(DST),'(%.0fs)'%(time.time()-t0))
with open(DST,'rb') as g: sha=hashlib.file_digest(g,'sha256').hexdigest()
with open(SRC,'rb') as g: sha69=hashlib.file_digest(g,'sha256').hexdigest()
json.dump(dict(V69=dict(path=SRC,sha256=sha69,bytes=os.path.getsize(SRC)),nou=dict(path=DST,sha256=sha,bytes=os.path.getsize(DST)),canvis={str(k):v for k,v in CANVIS.items()},fonts={str(k):v for k,v in FONTS.items()},noms={str(k):v for k,v in NOMS.items()},ocultes=OCULTES,image_data_offset=img_off_new,roi=ROI),open(P['rebut'],'w'),indent=1,ensure_ascii=False)
print('SHA V69',sha69); print('SHA nou',sha)
