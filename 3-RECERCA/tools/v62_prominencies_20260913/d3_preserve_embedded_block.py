from pathlib import Path
import struct,json,shutil
from psd_tools.psd.tagged_blocks import TaggedBlock
O=Path.cwd()/'output/v62_prominencies_20260913'
def positions(p):
 with p.open('rb') as f:
  f.seek(26)
  def rd(fmt):return struct.unpack('>'+fmt,f.read(struct.calcsize(fmt)))[0]
  for _ in range(2):n=rd('I');f.seek(n,1)
  lmpos=f.tell();ll=rd('Q');end=f.tell()+ll;nn=rd('Q');f.seek(nn,1);g=rd('I');f.seek(g,1);blocks={}
  while f.tell()<end:
   pos=f.tell();sig=f.read(4);key=f.read(4);fmt=TaggedBlock._length_format(key,2);n=rd(fmt);stop=pos+8+struct.calcsize(fmt)+((n+3)//4)*4;blocks[key]=(pos,stop);f.seek(stop)
 return lmpos,ll,blocks
source=O/'V61_Pere_input.psb';stage=O/'V62_work.psb';dest=O/'V62_preserved_work.psb';assert not dest.exists();sp,sl,sb=positions(source);tp,tl,tb=positions(stage);a,b=tb[b'lnk2'];c,d=sb[b'lnk2'];delta=(d-c)-(b-a)
def copy(f,g,n):
 while n:
  q=f.read(min(n,8*1024*1024));assert q;g.write(q);n-=len(q)
with stage.open('rb') as f,source.open('rb') as s,dest.open('xb') as g:
 copy(f,g,tp);g.write(struct.pack('>Q',tl+delta));f.seek(8,1);copy(f,g,a-(tp+8));s.seek(c);copy(s,g,d-c);f.seek(b);shutil.copyfileobj(f,g,8*1024*1024)
(O/'D3_block_preservation.json').write_text(json.dumps(dict(source_block=[c,d],staged_block=[a,b],byte_difference=delta,explanation='Preserve native embedded-file descriptor and payload byte for byte; psd-tools serialization shortened native block',output=str(dest)),indent=2));print('PRESERVED',delta,dest.stat().st_size)
