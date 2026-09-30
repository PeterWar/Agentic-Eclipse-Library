"""Reproduce comparable metrics and technical figures, no PSB modifications."""
from c0_gradient_pilot import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
z=np.load(OUT/'C5_signed_frequency_compositor.npz');g=np.load(OUT/'C0_gradient_pilot.npz');ref=np.load(ROOT/'research/tools/v45_earthshine_20260910/cau/vixen_reference.npy')
sources={'V45 font Vixen':ref,'Radiància67':z['base'],'Candidat8–16':z['band8_16'],'Sensibilitat4–8':z['band4_8']}
rep={k:metrics(v[215:300,585:815]) for k,v in sources.items()};rep['Presa curta']=metrics(g['coronal_geometry_short']);(OUT/'C6_comparable_metrics.json').write_text(json.dumps(rep,indent=2))
fig,axs=plt.subplots(2,2,figsize=(13,6),layout='constrained')
for ax,(key,v) in zip(axs.ravel(),sources.items()):
    ax.imshow(np.log10(np.maximum(v[215:300,585:815],1)),cmap='gray',vmin=2.6,vmax=5.2,interpolation='nearest',extent=[585,815,300,215]);ax.set(xlim=(620,780),ylim=(273,240),title=key);ax.set_aspect('equal')
fig.suptitle('Candidat a l’origen · sense Camera Raw · no és un nou PSB');fig.savefig(OUT/'vistes/C6_candidate_top.png',dpi=140);plt.close(fig)
fig,axs=plt.subplots(1,3,figsize=(13,4.5),layout='constrained')
for ax,key in zip(axs,sources):
    ax.imshow(np.arcsinh(sources[key]/20),cmap='gray',vmin=3.5,vmax=5,interpolation='nearest');ax.set(xlim=(200,1200),ylim=(1200,200),title=key)
fig.suptitle('Fonts tècniques completes · mateixa corba · estètica Camera Raw pendent');fig.savefig(OUT/'vistes/C6_whole_moon.png',dpi=140);plt.close(fig)
