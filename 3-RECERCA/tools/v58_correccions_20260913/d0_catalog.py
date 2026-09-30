from common58 import *
import pandas as pd
from scipy.spatial import cKDTree
claim()
cat=Path('/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17/xmatch/cat2_sony.csv')
c=pd.read_csv(cat);print('catalog',len(c))
M=np.asarray(json.loads((R/'research/tools/v29/cau_final/direct_grid_receipt.json').read_text())['common_to_final'])[:,:2]
L=json.loads(Path('/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/019_VIXEN_CIENCIA_20260827T212404Z/4-rebuts/F1.2_sol_llenc.json').read_text())['llenc'];print(L)
stars=json.loads((V42/'cau/estrelles_v42.json').read_text())['estrelles'];obs=np.array([[s['x'],s['y']] for s in stars]);sky=c[['xi_as','eta_as']].to_numpy();sc=L['escala_arcsec_px']
# common canvas is north-up: east left, north up. Test handedness explicitly against known measured stars.
for sx in [-1,1]:
 for sy in [-1,1]:
  pred=(sky*np.array([sx,sy])/sc)@M.T+np.array([CX,CY]);dist,ix=cKDTree(pred).query(obs);print(sx,sy,'n<80',sum(dist<80),'dist',dist.round(1).tolist())
  if sum(dist<80)>12:
   k=dist<80;A=np.c_[sky[ix[k]],np.ones(k.sum())];coef=np.linalg.lstsq(A,obs[k],rcond=None)[0];pred2=np.c_[sky,np.ones(len(c))]@coef;d2,i2=cKDTree(pred2).query(obs);print('fitted',d2.round(2).tolist(),coef)
   c['x_pred']=pred2[:,0];c['y_pred']=pred2[:,1];c.to_csv(O/'catalog_projected.csv',index=False);save('D0_catalog_projection.json',dict(source=str(cat),sha256=sha(cat),known_stars=len(stars),initial_signs=[sx,sy],matched=k.tolist(),residual_px=d2.tolist(),matrix=coef.tolist(),note='astrometric catalog projected from equatorial tangent coordinates; empirical affine fit to already measured V42 stars, star fitting only; does not transform photographic data'))
