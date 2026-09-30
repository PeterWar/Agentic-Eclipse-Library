from common58 import *
import pandas as pd
from scipy.spatial import cKDTree
claim();P=Path('/Users/USUARI/Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles')
c=pd.read_csv(P/'Work_2026-08-17/xmatch/cat2_sony.csv');sol=json.loads((P/'Resultats_acceptacio_2026-08-17/final_solution.json').read_text())['sony_radial'];x=c.xh_as.to_numpy();y=c.yh_as.to_numpy();A=np.c_[np.ones(len(c)),x,y,x*(x*x+y*y),y*(x*x+y*y)];raw=np.c_[A@sol['px'],A@sol['py']];M=np.asarray(json.loads((R/'research/tools/v29/cau_final/direct_grid_receipt.json').read_text())['common_to_final'])[:,:2];stars=json.loads((V42/'cau/estrelles_v42.json').read_text())['estrelles'];obs=np.array([[s['x'],s['y']] for s in stars]);best=None
for ang in [-90.27,90.27,0]:
 t=np.deg2rad(ang);rot=np.array([[np.cos(t),-np.sin(t)],[np.sin(t),np.cos(t)]]);pred=(raw-[sol['sun_x'],sol['sun_y']])@rot.T/(2.1494813525884373/3.202)@M.T+[CX,CY];dist,ix=cKDTree(pred).query(obs);print(ang,dist.round(1).tolist())
 if best is None or np.median(dist)<best[0]:best=(np.median(dist),pred,dist,ix)
_,pred,dist,ix=best;k=dist<40;print('match',k.sum());assert k.sum()>=12
coef=np.linalg.lstsq(np.c_[pred[ix[k]],np.ones(k.sum())],obs[k],rcond=None)[0];p2=np.c_[pred,np.ones(len(c))]@coef;d2,i2=cKDTree(p2).query(obs);print('after',d2.round(2).tolist());c['x_pred']=p2[:,0];c['y_pred']=p2[:,1];c.to_csv(O/'catalog_projected.csv',index=False);save('D0b_catalog_projection.json',dict(initial_distance_px=dist,refined_distance_px=d2,matched=k,affine=coef,source='original radial astrometric solution on atmospheric horizontal coordinates, propagated through native Sony orientation and existing final grid; small affine recentering to V42 measured stars'))
