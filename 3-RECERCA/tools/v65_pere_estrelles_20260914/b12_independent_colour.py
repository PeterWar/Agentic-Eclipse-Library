from pathlib import Path
import numpy as np,json,ast
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';A=O/'arrays';P=R/'output/v62_prominencies_20260913';tree=ast.parse((R/'research/tools/eclipse_determinista/comu.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['a_lineal']],type_ignores=[]),'pure','exec'))
old=a_lineal(np.stack([np.load(A/f'L3_C{c}.npy') for c in range(3)],-1)/65535);new=a_lineal(np.load(A/'B11_base_k0.9.npy')/65535);son=np.load(P/'arrays/B1_sony_linear.npy');gain=np.array(json.loads((P/'C1_colour_validation.json').read_text())['held_out_Sony'][0]['Sony_global_gain']);ref=son/np.maximum(son[...,1:2],1e-8)*gain;oldratio=old/np.maximum(old[...,1:2],1e-8);newratio=new/np.maximum(new[...,1:2],1e-8);y,x=np.mgrid[2777:4777,4377:6377];lm=np.load(A/'L30_C-2.npy')/65535;rows=[]
for m in json.loads((O/'A3_marks.json').read_text()):
 if m['index'] not in [1,3,4,5,6]:continue
 x0,y0,x1,y1=m['bbox'];ok=(x>=x0-14)&(x<x1+14)&(y>=y0-14)&(y<y1+14)&(son>0).all(-1)&(new>0).all(-1)&(lm<.1)&np.any(old!=new,-1)
 if not ok.any():rows.append(dict(mark=m['index'],pixels=0));continue
 erold=np.median(abs(np.log(oldratio[ok]/ref[ok])),axis=0);ernew=np.median(abs(np.log(newratio[ok]/ref[ok])),axis=0);rows.append(dict(mark=m['index'],pixels=int(ok.sum()),R_B_median_abs_log_error_before=erold[[0,2]].tolist(),R_B_median_abs_log_error_after=ernew[[0,2]].tolist(),both_improve=bool(np.all(ernew[[0,2]]<erold[[0,2]]))))
rep=dict(reference='Sony physical-linear source, gain frozen at V62 and unchanged. Vixen-derived colour estimate remains source. Pixel comparison uses existing registration; no transformation fitted.',marks=rows,scope='Photographic highlight/gamut handling only; no new absolute astronomical registration claim.');(O/'B12_independent_colour.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2))
