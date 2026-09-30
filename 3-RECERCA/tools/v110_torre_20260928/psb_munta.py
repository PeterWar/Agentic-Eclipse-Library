"""Non-clobber PSB assembly preserving every untouched record and channel byte."""
from pathlib import Path
import sys,json,io,copy,struct,hashlib,time
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB,llegeix_registres,rid,enc,q_blocs,sha,renomena
from psd_tools.psd.layer_and_mask import LayerRecord,ChannelInfo,LayerFlags
from psd_tools.constants import Tag,BlendMode
def assemble(cfg):
 assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_V110_TORRE_PISA_20260928'
 assert not cfg.get('new'), 'V110 forbids new flattened-composite layers'
 contract_path=ROOT/'4-RESULTATS/v110_torre_20260928/CONTRACTE_TORRE.json'
 assert sha(contract_path)=='839f2468705eb8e1dd55b19d84670913bb2c2de5ff2d6e71d27186b4cc2ae0b5'
 contract=json.loads(contract_path.read_text())
 assert cfg['source']==contract['base']['path'] and cfg['sha256']==contract['base']['sha256']
 assert cfg.get('hide')==[307]
 assert cfg.get('import')==[
  {'source':cfg['source'],'id':41,'new_id':410,'visible':False,'name':contract['original_names']['410']},
  {'source':cfg['source'],'id':42,'new_id':411,'visible':False,'name':contract['original_names']['411']},
  {'source':contract['manual']['path'],'id':308}], 'Untraced imported layer'
 assert sha(contract['manual']['path'])==contract['manual']['sha256']
 if cfg.get('replace'):
  expected={str(lid):{**{str(cid):contract['replacement'][str(lid)]['path'] for cid in [0,1,2]},'name':contract['replacement'][str(lid)]['name']} for lid in (41,42)}
  assert cfg['replace']==expected,'Only declared source-operator RGB replacements permitted'
  for spec in contract['replacement'].values():assert sha(spec['path'])==spec['sha256']
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
      a=q_blocs(np.load(v[key],mmap_mode='r'));f=cache/f'L{lid}_c{key}.bin';f.write_bytes(enc(a));ch.length=f.stat().st_size;channels[i]=(f,0,ch.length)
    if 'name' in v:renomena(rec,v['name'])
   buf=io.BytesIO();rec.write(buf,version=2);raw=buf.getvalue()
  records.append((raw,channels,lid))
 for spec in cfg.get('import',[]):
  ps=PSB(spec['source']);ss=llegeix_registres(Path(spec['source']))
  rec,raw=next((r,b) for r,b in ss['recs'] if rid(r)==spec['id']);channels=source_channels(ps,rec)
  newid=spec.get('new_id',rid(rec));assert newid not in all_ids
  if newid!=rid(rec) or 'visible' in spec or 'name' in spec:
   rec=copy.deepcopy(rec);rec.tagged_blocks.set_data(Tag.LAYER_ID,newid)
   if 'visible' in spec:rec.flags.visible=spec['visible']
   if 'name' in spec:renomena(rec,spec['name'])
   buf=io.BytesIO();rec.write(buf,version=2);raw=buf.getvalue()
  records.append((raw,channels,newid));all_ids.add(newid)
  info['layers'].append(dict(id=newid,import_source=spec['source'],source_id=spec['id'],visible=bool(rec.flags.visible)))
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
