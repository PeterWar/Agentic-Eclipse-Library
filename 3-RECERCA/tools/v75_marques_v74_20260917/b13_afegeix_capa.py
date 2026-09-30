"""B13: escriu un PSB nou = PSB font + UNA capa nova a dalt de la pila (normal, sense màscara), amb RGB i alfa donats a la ROI (4377,2777)–(6377,4777).
Plantilla del registre: l'última capa del fitxer (una capa ràster simple de Photoshop). Canals codificats ZIP-predicció; la resta del fitxer byte a byte; compost regenerat (raw) amb el retall.
Paràmetres JSON: src, dst, rebut, capa (npz amb R,G,B,A uint16 2000², i 'compost' RGB uint16 2000² per al retall del compost), nom (unicode), nom_curt (≤31), id."""
import sys, os, io, json, struct, zlib, time, hashlib, copy, logging, numpy as np
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; sys.path.insert(0,NEW)
from psb69 import PSB
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.psd.tagged_blocks import TaggedBlock
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
BIG={x.value for x in TaggedBlock._BIG_KEYS}
P=json.load(open(sys.argv[1])); SRC=P['src']; DST=P['dst']; assert not os.path.exists(DST),'no-clobber'
x0,y0,x1,y1=P.get('roi',[4377,2777,6377,4777]); v=np.load(P['capa']); NEWID=int(P['id'])
p=PSB(SRC); t0=time.time()
def codifica(arr):
    a=arr.astype(np.uint16); d=a.copy(); d[:,1:]=(a[:,1:].astype(np.int32)-a[:,:-1].astype(np.int32))&0xFFFF; return struct.pack('>H',3)+zlib.compress(d.astype('>u2').tobytes(),6)
nou={-1:codifica(v['A']),0:codifica(v['R']),1:codifica(v['G']),2:codifica(v['B'])}
for cid,b in nou.items(): assert np.array_equal(p._decode(b,x1-x0,y1-y0),v[{-1:'A',0:'R',1:'G',2:'B'}[cid]])
print('canals nous codificats:',{k:len(b) for k,b in nou.items()},flush=True)
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
    assert lr,'sense Lr16'; lr_pos,lr_lenpos,lr_data,lr_len=lr; lr_end_pad=lr_data+(lr_len+3)//4*4
    f.seek(lr_data); count=rf(f,'h')[0]; recs=[LayerRecord.read(f,version=2) for _ in range(abs(count))]; rec_end=f.tell()
    assert rec_end==min(vv[0] for l in p.layers for vv in l['chans'].values())
    ids=[int(r.tagged_blocks.get_data(Tag.LAYER_ID)) for r in recs]; assert NEWID not in ids, 'id ja existeix'
    tpl_id=int(P.get('plantilla',ids[-1])); nr=copy.deepcopy(recs[ids.index(tpl_id)])
    # sense màscara: fora el canal -2 i les dades de màscara; queden -1,0,1,2
    nr.channel_info=[c for c in nr.channel_info if int(c.id)!=-2]; nr.mask_data=None
    assert [int(c.id) for c in nr.channel_info]==[-1,0,1,2], 'la plantilla ha de tenir els canals -1,0,1,2 (té %s)'%[int(c.id) for c in nr.channel_info]
    nr.top,nr.left,nr.bottom,nr.right=y0,x0,y1,x1
    for c in nr.channel_info: c.length=len(nou[int(c.id)])
    nr.name=P['nom_curt']; nr.opacity=255; nr.clipping=0; nr.flags.visible=True
    nr.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME,P['nom']); nr.tagged_blocks.set_data(Tag.LAYER_ID,NEWID)
    recs.append(nr); buf=io.BytesIO()
    for r in recs: r.write(buf,version=2)
    recbytes=buf.getvalue(); total_ch=sum(c.length for r in recs for c in r.channel_info); new_lr_len=2+len(recbytes)+total_ch; new_lr_pad=(new_lr_len+3)//4*4
    new_lm_len=lm_len+(new_lr_pad-(lr_end_pad-lr_data)); newcount=count-1 if count<0 else count+1
    print('Lr16 %d → %d; L&M %d → %d; capes %d → %d'%(lr_len,new_lr_len,lm_len,new_lm_len,abs(count),abs(newcount)),flush=True)
    C=p.composite(); a=(C[y0:y1,x0:x1,3].astype(np.float64)/65535) if C.shape[2]>=4 else np.ones((y1-y0,x1-x0)); st=C[y0:y1,x0:x1,:3].astype(np.float64)/65535
    true=np.clip((st-(1-a[...,None]))/np.maximum(a[...,None],1e-6),0,1); al=v['A'].astype(np.float64)/65535; T=v['compost'].astype(np.float64)/65535
    bl=al[...,None]*T+(1-al[...,None])*true; C[y0:y1,x0:x1,:3]=np.uint16(np.round(np.clip(bl*a[...,None]+(1-a[...,None]),0,1)*65535))
    with open(DST,'wb') as g:
        f.seek(0); g.write(f.read(lm_start)); g.write(struct.pack('>Q',new_lm_len)); f.seek(lm_start+8); g.write(f.read(lr_lenpos-(lm_start+8)))
        g.write(struct.pack('>Q',new_lr_len)); g.write(struct.pack('>h',newcount)); g.write(recbytes)
        for L in p.layers:
            for cid,(off,n) in L['chans'].items():
                f.seek(off); rem=n
                while rem>0: b=f.read(min(rem,64<<20)); g.write(b); rem-=len(b)
        for cid in (-1,0,1,2): g.write(nou[cid])
        g.write(b'\0'*(new_lr_pad-new_lr_len)); f.seek(lr_end_pad); rem=lm_end-lr_end_pad
        while rem>0: b=f.read(min(rem,64<<20)); g.write(b); rem-=len(b)
        img_off=g.tell(); g.write(struct.pack('>H',0))
        for k in range(C.shape[2]): g.write(np.ascontiguousarray(C[...,k]).astype('>u2').tobytes())
print('escrit; compost (raw) a',img_off,'mida',os.path.getsize(DST),'(%.0fs)'%(time.time()-t0))
with open(DST,'rb') as g: sha=hashlib.file_digest(g,'sha256').hexdigest()
with open(SRC,'rb') as g: sha0=hashlib.file_digest(g,'sha256').hexdigest()
json.dump(dict(font=dict(path=SRC,sha256=sha0,bytes=os.path.getsize(SRC)),nou=dict(path=DST,sha256=sha,bytes=os.path.getsize(DST)),capa=dict(id=NEWID,nom=P['nom'],bbox=[x0,y0,x1,y1],canals={str(k):len(b) for k,b in nou.items()}),roi=[x0,y0,x1,y1],quan=time.strftime('%Y-%m-%dT%H:%M:%S')),open(P['rebut'],'w'),indent=1,ensure_ascii=False)
print('SHA font',sha0); print('SHA nou',sha)
