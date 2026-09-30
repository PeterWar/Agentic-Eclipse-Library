from pathlib import Path
import ast,struct,json,shutil
from psd_tools.psd.tagged_blocks import TaggedBlock
R=Path.cwd();O=R/'output/v63_encaix_contorn_20260913'
tree=ast.parse((R/'research/tools/v62_prominencies_20260913/d3_preserve_embedded_block.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'pure_block_tools','exec'))
source=O/'V62_input.psb';stage=O/'V63_pilot_serialized.psb';dest=O/'V63_pilot.psb';assert not dest.exists();sp,sl,sb=positions(source);tp,tl,tb=positions(stage);a,b=tb[b'lnk2'];c,d=sb[b'lnk2'];delta=(d-c)-(b-a)
with stage.open('rb') as f,source.open('rb') as s,dest.open('xb') as g:
 copy(f,g,tp);g.write(struct.pack('>Q',tl+delta));f.seek(8,1);copy(f,g,a-(tp+8));s.seek(c);copy(s,g,d-c);f.seek(b);shutil.copyfileobj(f,g,8*1024*1024)
(O/'B3_block.json').write_text(json.dumps(dict(source=str(source),dest=str(dest),native_embedded_block_preserved=True,delta=delta),indent=2)+'\n');print('PRESERVED',delta,flush=True)
