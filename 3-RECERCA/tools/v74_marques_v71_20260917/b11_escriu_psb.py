"""B11: escriu un PSB nou a partir d'un PSB font (V71 de Pere): registres reserialitzats, canals canviats recodificats (ZIP-predicció), la resta byte a byte; compost regenerat (raw) amb el retall de la ROI. Estructura localitzada llegint els blocs (cap offset fix)."""
import sys, os, io, json, struct, zlib, time, hashlib, logging, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'
sys.path.insert(0,NEW)
from psb69 import PSB
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.psd.tagged_blocks import TaggedBlock
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
BIG={x.value for x in TaggedBlock._BIG_KEYS}
P=json.load(open(sys.argv[1])); SRC=P['src']; DST=P['dst']; assert not os.path.exists(DST),'no-clobber'
ROI=P['roi'] if 'roi' in P else [4377,2777,6377,4777]; x0,y0,x1,y1=ROI
CANVIS={int(k):v for k,v in P['canvis'].items()}; FONTS={int(k):v for k,v in P['fonts'].items()}; NOMS={int(k):v for k,v in P['noms'].items()}; OCULTES=P.get('ocultes',[])
p=PSB(SRC); t0=time.time()
def codifica(arr):
    a=arr.astype(np.uint16); d=a.copy(); d[:,1:]=(a[:,1:].astype(np.int32)-a[:,:-1].astype(np.int32))&0xFFFF; return struct.pack('>H',3)+zlib.compress(d.astype('>u2').tobytes(),6)
nou={}
for lid,chs in CANVIS.items():
    L=p.layer(lid); v=np.load(FONTS[lid])
    for ch in chs:
        cid=int(ch[1:]); full,org=p.channel(lid,cid); ox,oy=org; h,w=full.shape; xa,ya=max(x0,ox),max(y0,oy); xb,yb=min(x1,ox+w),min(y1,oy+h)
        full=full.copy(); full[ya-oy:yb-oy,xa-ox:xb-ox]=v[ch][ya-y0:yb-y0,xa-x0:xb-x0]; b=codifica(full); nou[(lid,cid)]=b
        assert np.array_equal(p._decode(b,w,h),full); print(f'  capa {lid} canal {cid}: {L["chans"][cid][1]} → {len(b)} bytes ({time.time()-t0:.0f}s)',flush=True)
def rf(f,fmt): n=struct.calcsize('>'+fmt); return struct.unpack('>'+fmt,f.read(n))
with open(SRC,'rb') as f:
    f.seek(26); n=rf(f,'I')[0]; f.seek(n,1); n=rf(f,'I')[0]; f.seek(n,1)
    lm_start=f.tell(); lm_len=rf(f,'Q')[0]; lm_end=lm_start+8+lm_len
    n=rf(f,'Q')[0]; assert n==0,'les capes no són al bloc Lr16'; f.seek(n,1)
    if f.tell()+4<=lm_end: n=rf(f,'I')[0]; f.seek(n,1)
    lr=None
    while f.tell()+12<=lm_end:
        pos=f.tell(); sig,key=rf(f,'4s4s'); fmt='Q' if key in BIG else 'I'; n=rf(f,fmt)[0]; start=f.tell()
        if key==b'Lr16': lr=(pos,f.tell()-(8 if fmt=='Q' else 4),start,n); break
        f.seek(start+(n+3)//4*4)
    assert lr, 'sense Lr16'; lr_pos,lr_lenpos,lr_data,lr_len=lr; lr_end_pad=lr_data+(lr_len+3)//4*4
    f.seek(lr_data); count=rf(f,'h')[0]; recs=[LayerRecord.read(f,version=2) for _ in range(abs(count))]; rec_end=f.tell()
    assert rec_end==p.layers[0]['chans'][-1][0] or rec_end==min(v[0] for l in p.layers for v in l['chans'].values())
    for r in recs:
        lid=int(r.tagged_blocks.get_data(Tag.LAYER_ID))
        if lid in CANVIS:
            for c in r.channel_info:
                if (lid,int(c.id)) in nou: c.length=len(nou[(lid,int(c.id))])
            old=str(r.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME)); r.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME,old+' · '+NOMS[lid])
        if lid in OCULTES: r.flags.visible=False
    buf=io.BytesIO()
    for r in recs: r.write(buf,version=2)
    recbytes=buf.getvalue(); total_ch=sum(c.length for r in recs for c in r.channel_info); new_lr_len=2+len(recbytes)+total_ch; new_lr_pad=(new_lr_len+3)//4*4
    new_lm_len=lm_len+(new_lr_pad-(lr_end_pad-lr_data)); print('Lr16 %d → %d; L&M %d → %d'%(lr_len,new_lr_len,lm_len,new_lm_len),flush=True)
    # compost regenerat (raw) amb el retall
    C=p.composite(); v=np.load(P['compost']); Cc=v['C'].astype(np.float64)/65535; a=v['a'].astype(np.float64)/65535
    rgbw=np.clip(Cc*a[...,None]+(1-a[...,None]),0,1); C[y0:y1,x0:x1,:3]=(rgbw*65535+.5).astype(np.uint16); C[y0:y1,x0:x1,3]=(a*65535+.5).astype(np.uint16)
    with open(DST,'wb') as g:
        f.seek(0); g.write(f.read(lm_start)); g.write(struct.pack('>Q',new_lm_len)); f.seek(lm_start+8); g.write(f.read(lr_lenpos-(lm_start+8)))
        g.write(struct.pack('>Q',new_lr_len)); g.write(struct.pack('>h',count)); g.write(recbytes)
        for L in p.layers:
            for cid,(off,n) in L['chans'].items():
                if (L['id'],cid) in nou: g.write(nou[(L['id'],cid)])
                else:
                    f.seek(off); rem=n
                    while rem>0: b=f.read(min(rem,64<<20)); g.write(b); rem-=len(b)
        g.write(b'\0'*(new_lr_pad-new_lr_len)); f.seek(lr_end_pad); rem=lm_end-lr_end_pad
        while rem>0: b=f.read(min(rem,64<<20)); g.write(b); rem-=len(b)
        img_off=g.tell(); g.write(struct.pack('>H',0))
        for k in range(C.shape[2]): g.write(np.ascontiguousarray(C[...,k]).astype('>u2').tobytes())
print('escrit; compost (raw) a',img_off,'mida',os.path.getsize(DST),'(%.0fs)'%(time.time()-t0))
with open(DST,'rb') as g: sha=hashlib.file_digest(g,'sha256').hexdigest()
with open(SRC,'rb') as g: sha0=hashlib.file_digest(g,'sha256').hexdigest()
json.dump(dict(font=dict(path=SRC,sha256=sha0,bytes=os.path.getsize(SRC)),nou=dict(path=DST,sha256=sha,bytes=os.path.getsize(DST)),canvis={str(k):v for k,v in CANVIS.items()},fonts={str(k):v for k,v in FONTS.items()},noms={str(k):v for k,v in NOMS.items()},ocultes=OCULTES,image_data_offset=img_off,roi=ROI,compost=P['compost']),open(P['rebut'],'w'),indent=1,ensure_ascii=False)
print('SHA font',sha0); print('SHA nou',sha)
