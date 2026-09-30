from pathlib import Path
import numpy as np,json,shutil
O=Path('/private/tmp/v105_root_pilots_20260926');R=Path('/Users/USUARI/Desktop/Eclipse 2026');p=O/'P06';assert not p.exists();p.mkdir()
z=np.load(O/'P05/Q_OBSERVED.npz');q={k:z[k]for k in z.files}
src=R/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja';old=np.load(src/'A3C_franja_silueta.npz');cfg=json.loads((src/'A3C_FRANJA_SILUETA.json').read_text())['escales']
y0,y1,x0,x1=map(int,q['box']);yy,xx=np.mgrid[y0:y1,x0:x1];cx,cy,r=q['centre'];d=np.hypot(xx-cx,yy-cy)-r
s=np.clip((d-12)/13,0,1);w=(1-s*s*(3-2*s))*q['observed'];newG=q['E_observed'][...,1]
for key in ['G','V']:
    measured=newG*cfg['c_'+key][0];q[key]=np.where(w>0,(1-w)*old[key]+w*measured,old[key]).astype(np.float32)
    assert np.array_equal(q[key][d>=25],old[key][d>=25],equal_nan=True)
q['G_domain']=np.where(d<25,q['domini_E']&np.isfinite(q['G'])&(q['G']>0),old['domini']);q['domini']=q['G_domain']
q['beta']=np.where(d<25,q['G_domain'].astype(np.float32),old['beta']);q['dins_franja']=q['beta']>0
np.savez_compressed(p/'Q_OBSERVED.npz',**q)
for f in ['BASE_ROI.npz','BASE.json']:
    shutil.copyfile(O/'P05'/f,p/f)
rep={'reason':'Historic old E*scale is not identical to old G/V at164 redprominence pixels. Blend actual endpoints directly to avoid25px discontinuity.','formula':'G/V = (1-w)*oldG/V + w*observed_E_G*legacy_constant; w=1-smoothstep(d12,25). No RGBcolour splice.','source':'P05 observed data and L_scalar, allunchanged; BASE byte-identicalP05','remaining_nonpositive_join_G':int(((d>=12)&(d<25)&q['domini_E']&(q['G']<=0)).sum()),'outside25_scalar_exact':True,'L_unchanged':bool(np.array_equal(q['L_scalar'],z['L_scalar'],equal_nan=True)),'domains_differ':int((q['L_domain']!=q['G_domain']).sum())}
(p/'ENDPOINTS.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2))
