"""Scientific plots and measured synthesis; no astronomical image modification."""
from native_operator import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fits=json.loads((OUT/'C2_pose_fits.json').read_text())['results'];shape=json.loads((OUT/'C3_shape_validation.json').read_text());texture=json.loads((OUT/'D0_lunar_texture_pose.json').read_text())
colors={'baseline':'#c2732b','pose':'#197f8b','pose_core':'#915aa5'};labels={'baseline':'Geometria inicial','pose':'Translació mesurada','pose_core':'Translació + amplada per presa'};scenes={v:np.load(OUT/f'C2_{v}_scene.npz') for v in colors}
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(3,2,figsize=(13,12),layout='constrained')
for col,stem in enumerate(['572A2976','572A2994']):
    z=np.load(OUT/'matrices'/f'{stem}_observations.npz');rr=np.hypot(z['xy'][:,0]-CX,z['xy'][:,1]-CY);bins=np.arange(430,467,.5);centers=(bins[:-1]+bins[1:])/2;selections=[(rr>=a)&(rr<b) for a,b in zip(bins[:-1],bins[1:])]
    def median(values):return np.array([np.median(values[m]) if m.sum()>=5 else np.nan for m in selections])
    ax=axes[0,col];ax.plot(centers,median(z['g']),'k.',ms=3,label='Mostres natives vàlides')
    for variant in colors:ax.plot(centers,median(scenes[variant][stem]),color=colors[variant],label=labels[variant],lw=1.5)
    ax.set(yscale='log',ylim=(450,350000),xlim=(430,466),title=f'{stem} · 1/15 s reservada · '+('inici' if col==0 else 'final'),ylabel='Radiància verda calibrada [G]');ax.axvspan(449,454,color='#ddd',alpha=.45);ax.grid(alpha=.18);ax.legend(fontsize=8,loc='upper left')
    ax=axes[1,col]
    for variant in colors:
        residual=scenes[variant][stem]-z['g'];weighted=residual**2*z['q']/(z['weight_variance']*14.826313721285086);v=np.array([np.sqrt(np.mean(weighted[m])) if m.sum()>=5 else np.nan for m in selections]);ax.plot(centers,v,color=colors[variant],label=labels[variant])
    ax.set(yscale='log',ylim=(.1,35),xlim=(430,466),xlabel='Radi [píxels del camp lunar de treball]',ylabel='Arrel de l’error quadràtic ponderat');ax.axhline(1,color='#888',ls=':',lw=1);ax.axvspan(449,454,color='#ddd',alpha=.45);ax.grid(alpha=.18)
geo=Geometry(16);yy,xx=np.mgrid[geo.box[1]:geo.box[3]+1,geo.box[0]:geo.box[2]+1];rr=np.hypot(xx-CX,yy-CY);inside=(xx<geo.border(yy))&(xx>=1117)&(xx<=1187)&(yy>=630)&(yy<=770);bins=np.arange(425,455,.5);centers=(bins[:-1]+bins[1:])/2
for variant in colors:
    m=scenes[variant]['lunar'];values=[]
    for a,b in zip(bins[:-1],bins[1:]):
        sel=inside&(rr>=a)&(rr<b);values.append(float(np.median(m[sel])) if sel.sum()>=5 else np.nan)
    axes[2,0].plot(centers,values,color=colors[variant],label=labels[variant])
axes[2,0].set(title='Lluna inferida: sensibilitat a geometria i amplada',xlabel='Radi [píxels]',ylabel='Mediana de radiància latent [G]',ylim=(0,6500));axes[2,0].axvspan(449,454,color='#ddd',alpha=.45);axes[2,0].grid(alpha=.18)
rows=[r for r in shape['summary'] if r['region']=='right' and r['group']!='all'];x=np.arange(len(rows));palette=['#197f8b','#718d3d','#c2732b']
for j,mode in enumerate(['rigid','similarity','affine']):axes[2,1].bar(x+(j-1)*.24,[r['rms'][mode] for r in rows],width=.23,label={'rigid':'Translació','similarity':'+ escala','affine':'+ deformació afí'}[mode],color=palette[j])
axes[2,1].set(xticks=x,xticklabels=['Inici','Final','Altres preses'],ylabel='Error RMS de posició [píxels]',title='Predicció en sectors intercalats de la dreta');axes[2,1].legend(fontsize=8);axes[2,1].grid(axis='y',alpha=.18)
fig.suptitle('Diagnòstic natiu del llimb · cap nova correcció fotogràfica promoguda',fontsize=15)
fig.savefig(OUT/'E0_native_review.png',dpi=140);plt.close(fig)
lookup={r['variant']:r for r in fits};reductions=[]
for stem in ['572A2976','572A2994']:
    def value(v):return next(g for r in lookup[v]['predictions'] if r['stem']==stem for g in r['regions'] if g['radius']==[449,454])['weighted_mean_square']
    base=value('baseline');pose=value('pose');reductions.append(dict(stem=stem,baseline_weighted_MSE=base,pose_weighted_MSE=pose,reduction_percent=100*(1-pose/base)))
save('E0_review.json',dict(method=__doc__,pose_last_ring_reserved=reductions,all_C2_numerical_pass=all(r['numerical_PASS'] for r in fits),affine_candidate_pass=shape['affine_geometry_candidate_PASS'],texture_candidates=sum(r['diagnostic_eligible'] for r in texture['rows']),texture_total=len(texture['rows']),texture_shift_equivariance=texture['control_PASS'],PSB_changed=False,physical_all_limb_PASS=False,plot='E0_native_review.png'))
print(json.dumps(reductions),flush=True)
