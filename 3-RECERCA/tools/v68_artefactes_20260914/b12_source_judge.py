from pathlib import Path
import numpy as np,json,ast
from scipy.fft import rfft2
R=Path.cwd();O=R/'output/v68_artefactes_20260914';A=O/'arrays';N=1400;CX=699.568111973117;CY=699.6475341408573
s=ast.parse((R/'research/tools/earthshine_v56_three_routes_20260913/spectral.py').read_text());exec(compile(ast.Module(body=[n for n in s.body if isinstance(n,ast.FunctionDef) and n.name in ['tiles','tile_fft','fft_stats']],type_ignores=[]),'pure','exec'))
z=np.load(A/'B9_fine_detector.npz');p=np.load(A/'B10_photo_pilot.npz');sony=np.load(R/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'];lroc=np.load(R/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((R/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];lr=np.zeros((N,N));oy,ox=bb[1]-3077,bb[0]-4677;lr[oy:oy+lroc.shape[0],ox:ox+lroc.shape[1]]=lroc[...,:3].mean(-1)
raw={'source_before':z['raw_baseline'],'source_after':z['source'],'photo_before':p['old'].mean(-1),'photo_after':p['candidate'].mean(-1),'Sony':sony,'LROC':lr};out=[]
for ti,t in enumerate(tiles()):
 F={k:tile_fft(a,t) for k,a in raw.items()}
 for band in [[4,8],[8,16],[16,24],[24,40],[40,64]]:
  for label in ['source','photo']:
   q={'tile':ti,'parity':t['parity'],'band':band,'label':label}
   for ref in ['Sony','LROC']:
    q[ref+'_before']=fft_stats(F[label+'_before'],F[ref],band)[0];q[ref+'_after']=fft_stats(F[label+'_after'],F[ref],band)[0]
   out.append(q)
summary=[]
for label in ['source','photo']:
 for band in [[4,8],[8,16],[16,24],[24,40],[40,64]]:
  q=[x for x in out if x['label']==label and x['band']==band and x['parity']==1];ss=dict(label=label,band=band,n=len(q))
  for ref in ['Sony','LROC']:
   ss[ref+'_before']=float(np.mean([x[ref+'_before'] for x in q]));ss[ref+'_after']=float(np.mean([x[ref+'_after'] for x in q]))
  summary.append(ss)
(O/'B12_source_judge.json').write_text(json.dumps(dict(rows=out,summary=summary,limits=['Sony independent of Vixen-only source producer; photo already contains wide Sony component, so photo comparison is retention.','Overlapping tiles share calibration and are not independent statistical trials.']),indent=2)+'\n');print(json.dumps(summary,indent=2))
