"""Build a reversible V105 research stage from Pere's current V104.
Only RGB of base3 changes inside the declared ROI, name3, visibility303.
Every other layer record/channel is copied exactly; native save required.
"""
import argparse,sys,json,hashlib,struct,zlib,io,copy,time
from pathlib import Path
import numpy as np
R=Path('/Users/USUARI/Desktop/Eclipse 2026')
sys.path.insert(0,str(R/'3-RECERCA/tools/v71_marques_v69_20260916'))
from psb69 import PSB,BIG_KEYS,_rf
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.constants import Tag

def sha(p):
    with open(p,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def records(path):
    with open(path,'rb') as f:
        f.seek(26)
        for _ in range(2):n=_rf(f,'I')[0];f.seek(n,1)
        lmpos=f.tell();lmlen=_rf(f,'Q')[0];lmend=f.tell()+lmlen
        assert _rf(f,'Q')[0]==0
        n=_rf(f,'I')[0];f.seek(n,1)
        while f.tell()+12<=lmend:
            sig,key=_rf(f,'4s4s');fmt='Q' if key in BIG_KEYS else 'I'
            lenpos=f.tell();n=_rf(f,fmt)[0];start=f.tell()
            if key==b'Lr16':break
            f.seek(start+(n+3)//4*4)
        count=_rf(f,'h')[0];rs=[]
        for _ in range(abs(count)):
            pos=f.tell();rec=LayerRecord.read(f,version=2);end=f.tell();f.seek(pos)
            rs.append((rec,f.read(end-pos)))
    return dict(lmpos=lmpos,lmlen=lmlen,lenpos=lenpos,start=start,end=start+(n+3)//4*4,count=count,recs=rs)
def encode(a):
    d=np.asarray(a,np.uint16).copy();d[:,1:]-=d[:,:-1].copy()
    return struct.pack('>H',3)+zlib.compress(d.astype('>u2').tobytes(),6)
def copyrange(dst,src,off,n):
    src.seek(off)
    while n:
        b=src.read(min(16<<20,n));assert b;dst.write(b);n-=len(b)
def run():
    ap=argparse.ArgumentParser();ap.add_argument('roi');ap.add_argument('output');ap.add_argument('--source',default=str(R/'1-PHOTOSHOP/V104.psb'));a=ap.parse_args()
    src=Path(a.source);dst=Path(a.output);assert not dst.exists()
    expected='da2b0792db66e91e93a064540feaceafc25ea9cfc6e328d54d3c8980eabc60fa'
    assert sha(src)==expected,'Source changed'
    q=np.load(a.roi);rgb=q['base_rgb_u16'];x0,y0,x1,y1=map(int,q['box_xyxy'])
    assert rgb.dtype==np.uint16 and rgb.shape==(y1-y0,x1-x0,3)
    p=PSB(str(src));s=records(src);out=[];cache=dst.parent/(dst.stem+'_channels');cache.mkdir(exist_ok=False)
    changes=[]
    for r0,raw in s['recs']:
        lid=int(r0.tagged_blocks.get_data(Tag.LAYER_ID));r=copy.deepcopy(r0);fs=[]
        if lid==3:
            # Hidden original base, including its alpha, mask, mode and bounds.
            old=copy.deepcopy(r0);old.flags.visible=False;old.name='Base V104 referencia';old.tagged_blocks.set_data(Tag.LAYER_ID,304)
            old.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME,'00 Base V104 original · referencia oculta')
            f=io.BytesIO();old.write(f,version=2)
            out.append((f.getvalue(),[(str(src),*p.layer(3)['chans'][int(c.id)]) for c in old.channel_info]))
        for c in r.channel_info:
            cid=int(c.id)
            if lid==3 and cid in (0,1,2):
                ch,origin=p.channel(3,cid);assert origin==(0,0)
                ch[y0:y1,x0:x1]=rgb[...,cid]
                f=cache/f'base_{cid}.bin';f.write_bytes(encode(ch));del ch
                fs.append((str(f),0,f.stat().st_size));c.length=f.stat().st_size
            else:fs.append((str(src),*p.layer(lid)['chans'][cid]))
        if lid==3:
            name='00 Base · fotografia observada V105';r.name='00 Base V105';r.tagged_blocks.set_data(Tag.UNICODE_LAYER_NAME,name)
            changes.append(dict(id=3,change='RGB ROI and name',box_xyxy=[x0,y0,x1,y1]))
        if lid==303:
            r.flags.visible=False;changes.append(dict(id=303,change='hidden reference; all pixels and geometry unchanged'))
        if lid in (3,303):
            f=io.BytesIO();r.write(f,version=2);raw=f.getvalue()
        out.append((raw,fs))
    recbytes=b''.join(x[0] for x in out);newlen=2+len(recbytes)+sum(f[2] for _,fs in out for f in fs);pad=(newlen+3)//4*4
    newlm=s['lmlen']+pad-(s['end']-s['start']);opened={}
    with src.open('rb') as f,dst.open('xb') as g:
        copyrange(g,f,0,s['lmpos']);g.write(struct.pack('>Q',newlm));copyrange(g,f,s['lmpos']+8,s['lenpos']-s['lmpos']-8)
        count=s['count']+(-1 if s['count']<0 else 1)
        g.write(struct.pack('>Q',newlen));g.write(struct.pack('>h',count));g.write(recbytes)
        for _,fs in out:
            for path,off,n in fs:
                if path not in opened:opened[path]=open(path,'rb')
                copyrange(g,opened[path],off,n)
        g.write(b'\0'*(pad-newlen));copyrange(g,f,s['end'],src.stat().st_size-s['end'])
    for f in opened.values():f.close()
    new=PSB(str(dst));assert len(new.layers)==len(p.layers)+1 and not new.layer(303)['visible'] and not new.layer(304)['visible']
    for c in (0,1,2):assert np.array_equal(new.channel_box(3,c,(x0,y0,x1,y1)),rgb[...,c])
    rep=dict(source=str(src),source_sha256=expected,stage=str(dst),stage_sha256=sha(dst),changes=changes,unchanged_layers=len(p.layers)-2,composite='STALE: MUST recompose in native Photoshop before delivery',input_roi=str(Path(a.roi).resolve()),input_sha256=sha(a.roi))
    dst.with_suffix('.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep),flush=True)
if __name__=='__main__':run()
