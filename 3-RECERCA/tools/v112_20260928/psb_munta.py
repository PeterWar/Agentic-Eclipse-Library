"""Non-clobber PSB assembly preserving every untouched record and channel byte."""
from pathlib import Path
import sys,json,io,copy,struct,hashlib,time
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB,llegeix_registres,rid,enc,q_blocs,sha,renomena
from psd_tools.psd.layer_and_mask import LayerRecord,ChannelInfo,LayerFlags
from psd_tools.constants import Tag,BlendMode
if sys.flags.optimize: raise RuntimeError('Assertions are required for this scientific assembler')
def assemble(cfg):
 assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V112_ESTRELLES_I_ARTEFACTES_20260928'
 assert not cfg.get('new'), 'No composite-patch layers permitted'
 assert not cfg.get('import'), 'No imported or compensating layers'
 allowed={41,42,45,46}
 if '301' in cfg.get('replace',{}):
  receipt=Path(cfg['corner_receipt']);r=json.loads(receipt.read_text())
  assert r['alpha_exact'] and r['source_sha256']==cfg['sha256']
  assert r['producer_sha256']=='547b57ce273103464aeb5d994a2e9eea6ec3e3ce3f06990d5f08fb3f221bab9c'
  assert r['box']==[7356,4320,9348,6263]
  assert sha(r['input_native'])==r['input_sha256']
  allowed.add(301)
 assert set(map(int,cfg.get('replace',{}))).issubset(allowed)
 assert all(set(v).issubset({'0','1','2'}) for v in cfg.get('replace',{}).values())
 assert set(cfg.get('hide',[])).issubset({412})
 src=Path(cfg['source']);dst=Path(cfg['destination']);assert not dst.exists()
 assert sha(src)==cfg['sha256'],'source identity changed'
 p=PSB(str(src));s=llegeix_registres(src);records=[];all_ids={x['id'] for x in p.layers}
 cache=dst.parent/(dst.stem+'_canals');cache.mkdir(exist_ok=False)
 replaced=cfg.get('replace',{});hidden=set(cfg.get('hide',[])); info={'source':str(src),'sha256_source':cfg['sha256'],'layers':[]}
 def source_channels(ps,rec):return [(Path(ps.path),*ps.layer(rid(rec))['chans'][int(ch.id)]) for ch in rec.channel_info]
 for rec,raw in s['recs']:
  lid=rid(rec);channels=source_channels(p,rec)
  if str(lid) in replaced or lid in hidden:
   rec=copy.deepcopy(rec)
   if lid in hidden:rec.flags.visible=False
   if str(lid) in replaced:
    v=replaced[str(lid)]
    for i,ch in enumerate(rec.channel_info):
     key=str(int(ch.id))
     if key in v:
      a=q_blocs(np.load(v[key],mmap_mode='r'));assert a.shape==(rec.bottom-rec.top,rec.right-rec.left);f=cache/f'L{lid}_c{key}.bin';f.write_bytes(enc(a));ch.length=f.stat().st_size;channels[i]=(f,0,ch.length)
    if 'name' in v:renomena(rec,v['name'])
   buf=io.BytesIO();rec.write(buf,version=2);raw=buf.getvalue()
  records.append((raw,channels,lid))
 total=2+sum(len(b)+sum(n for _,_,n in ch) for b,ch,_ in records);pad=(total+3)//4*4
 lmlen=s['lmlen']+pad-(s['lrpadend']-s['lrstart']);count=len(records)*(1 if s['count']>=0 else -1)
 def cp(f,g,a,b):
  f.seek(a)
  while f.tell()<b:g.write(f.read(min(32<<20,b-f.tell())))
 opened={}
 with src.open('rb') as f,dst.open('xb') as g:
  cp(f,g,0,s['lmpos']);g.write(struct.pack('>Q',lmlen));cp(f,g,s['lmpos']+8,s['lenpos']);g.write(struct.pack('>Qh',total,count))
  for b,_,_ in records:g.write(b)
  for _,chs,_ in records:
   for file,off,n in chs:
    if file not in opened:opened[file]=file.open('rb')
    cp(opened[file],g,off,off+n)
  g.write(b'\0'*(pad-total));cp(f,g,s['lrpadend'],src.stat().st_size)
 for f in opened.values():f.close()
 Q=PSB(str(dst));assert [l['id'] for l in Q.layers]==[lid for _,_,lid in records]
 Sq=llegeix_registres(dst)
 for (r,b),(expect,chs,lid) in zip(Sq['recs'],records):
  assert b==expect
  for c,(file,off,n) in zip(r.channel_info,chs):
   qo,qn=Q.layer(lid)['chans'][int(c.id)];assert qn==n
   ha=hashlib.sha256();hb=hashlib.sha256()
   with file.open('rb') as a,dst.open('rb') as b:
    a.seek(off);b.seek(qo);rem=n
    while rem:
     nn=min(rem,32<<20);ha.update(a.read(nn));hb.update(b.read(nn));rem-=nn
   assert ha.digest()==hb.digest(),(lid,int(c.id))
 assert sha(src)==cfg['sha256'];info.update(destination=str(dst),sha256=sha(dst),bytes=dst.stat().st_size,verification='all records and channels byte-identical to declared source or new encoded raster')
 dst.with_suffix('.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(info,ensure_ascii=False),flush=True)
if __name__=='__main__':assemble(json.loads(Path(sys.argv[1]).read_text()))
