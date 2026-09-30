"""Separate the global display-level response from local boundary changes.

One scalar offset equalizes the median difference inside r<350. This is only
a diagnostic normalization of the historical replay, not a new source, a
preserved Camera Raw recipe, or an accepted tonal correction.
"""
from reveal_common import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

delta=np.load(OUT/'B2_historical_display_delta_DN16.npy')
previous=np.load(OUT/'A0_previous_moon_RGB16.npy').astype(float).mean(-1)
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY)
a=np.arctan2(y-CY,x-CX)%(2*np.pi)
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
d=r-np.interp(a,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi)
global_response=float(np.median(delta[r<350]));local=delta-global_response
rows=[]
for label,use in [('face_r350',r<350),('inner_30_80',(d>=-80)&(d<-30)),('limb_6_25',(d>=-25)&(d<-6)),('last_3_inside',(d>=-3)&(d<0)),('outside_0_3',(d>=0)&(d<3))]:
    rows.append(dict(region=label,pixels=int(use.sum()),normalized_delta_DN16=np.percentile(local[use],[1,50,99]).tolist(),median_fraction_of_previous_display=float(np.median(local[use]/np.maximum(previous[use],1)))))
profiles=[]
for lo in np.arange(-100,6,.5):
    use=(d>=lo)&(d<lo+.5)
    profiles.append([float(lo+.25),float(np.median(delta[use])),float(np.median(local[use]))])
p=np.array(profiles)
fig,ax=plt.subplots(figsize=(9,4.5),layout='constrained')
ax.plot(p[:,0],p[:,1],label='Canvi de Camera Raw: píxels amagats modificats')
ax.plot(p[:,0],p[:,2],label='Després d’igualar la mediana de la cara lunar')
ax.axhline(0,c='k',lw=.6);ax.axvline(0,c='k',lw=.6,ls=':')
ax.set(xlabel='Distància a la vora observada (px; negatiu dins la Lluna)',ylabel='Canvi de lluminositat de pantalla (DN16)',title='Prova diagnòstica amb Camera Raw històric; cap correcció publicada')
ax.legend(fontsize=8);fig.savefig(OUT/'B3_boundary_global_vs_local.png',dpi=160);plt.close(fig)
save('B3_normalized_result.json',dict(method=__doc__,global_median_response_DN16=global_response,regions=rows,radial_profile=profiles,interpretation='Large absolute darkening is predominantly a global level change. After matching the core median, the median change in the -25..-6 px band is near zero. This auxiliary perturbation does not justify a limb correction; the residual spatial response and newest baked user CR are not validated.',publication='NONE; do not apply the diagnostic offset or auxiliary field to V49.'))
print('GLOBAL RESPONSE',global_response,flush=True)
print(json.dumps(rows,ensure_ascii=False,indent=2),flush=True)
