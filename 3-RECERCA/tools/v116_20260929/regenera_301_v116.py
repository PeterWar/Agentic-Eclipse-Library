"""regenera_301_v116 (V116, 29-09: còpia de regenera_301_v115.py amb la font de l'alfa = 1-PHOTOSHOP/V115.psb de Pere (04:25); abans: V114.psb; abans: còpia de v112_20260928/regenera_301.py amb V112.psb; la mateixa recepta a5_cantonada) · Original presentation-only corner dependency, driven by an owned native lower-stack render."""
from pathlib import Path
import sys,json,numpy as np,tifffile,importlib.util
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[1]/'v108_20260926/cadena'))
from comu_v108 import PSB,q_blocs,sha
ROOT=Path(__file__).resolve().parents[3]
O=ROOT/'4-RESULTATS/v112_claude_20260928';inp=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('corner',ROOT/'3-RECERCA/tools/v86_neta_20260923/a5_cantonada.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
source=ROOT/'1-PHOTOSHOP/V115.psb';p=PSB(str(source));box=(7356,4320,9348,6263);x0,y0,x1,y1=box
im=tifffile.memmap(inp,mode='r');assert im.shape==(7506,10551,3) and im.dtype.kind=='u' and im.dtype.itemsize==2
sub=im[y0:y1,x0:x1].astype(np.float32)/65535.;rgb,alpha,receipt=mod.calcula(sub)
raw_alpha=np.round(alpha*65535).astype('uint16');raw_alpha[0,0]=max(raw_alpha[0,0],1);raw_alpha[-1,-1]=max(raw_alpha[-1,-1],1);candidate_alpha=q_blocs(raw_alpha)
original_alpha,org=p.channel(301,-1);assert org==(x0,y0)
ad=candidate_alpha.astype('int32')-original_alpha.astype('int32')
receipt.update(source_sha256=sha(source),input_native=str(inp),input_sha256=sha(inp),producer_sha256=sha(Path(mod.__file__)),box=box,alpha_exact=bool(np.array_equal(candidate_alpha,original_alpha)),alpha_different=int(np.count_nonzero(ad)),alpha_max_abs_DN=int(abs(ad).max()),meaning='Presentation-only sky continuation; original existing alpha is preserved only if exact recipe equality is demonstrated.')
(out/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert receipt['alpha_exact'],receipt
for cid in (0,1,2):
 raw=np.round(np.clip(rgb[...,cid],0,1)*65535).astype('uint16');np.save(out/f'raw_c{cid}.npy',raw);np.save(out/f'L301_c{cid}.npy',q_blocs(raw))
np.save(out/'alpha_from_recipe.npy',candidate_alpha);print(json.dumps(receipt),flush=True)
