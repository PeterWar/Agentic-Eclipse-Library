"""Step 7. English versions of the two charts, written to the whitepaper image folder (same data as step 6)."""
import numpy as np, matplotlib; matplotlib.use('Agg')
from comu import ARREL, TREBALL
import matplotlib.pyplot as plt
OUT=ARREL/'6-PUBLICACIO'/'whitepaper'/'font'/'img'; OUT.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'Avenir Next','svg.fonttype':'path','font.size':8.5,'axes.edgecolor':'#9a9994','axes.linewidth':0.6,
    'xtick.color':'#52514e','ytick.color':'#52514e','axes.labelcolor':'#52514e','text.color':'#0b0b0b'})
BLUE,ORANGE='#2a78d6','#eb6834'; INK,INK2='#0b0b0b','#52514e'
def clean(ax):
    for s in ('top','right'): ax.spines[s].set_visible(False)
    ax.grid(axis='y',color='#e4e3df',lw=0.6); ax.set_axisbelow(True); ax.tick_params(length=2.5,width=0.6)
d=np.load(TREBALL/'lineal_quocient.npz'); x=d['x']*100
fig,ax=plt.subplots(figsize=(3.55,2.55)); clean(ax)
ax.plot(x,d['q_lin'],color=BLUE,lw=2,solid_capstyle='round'); ax.plot(x,d['q_dev'],color=ORANGE,lw=2,solid_capstyle='round')
ax.set_xscale('log'); ax.set_xlim(0.1,25); ax.set_ylim(0,4.6); ax.set_xticks([0.1,1,10,25]); ax.set_xticklabels(['0.1 %','1 %','10 %','25 %'])
ax.set_yticks([0,1,2,3,4]); ax.set_yticklabels(['0','1×','2×','3×','4×'])
ax.set_xlabel('Brightness of the point in the short frame (% of saturation)')
ax.text(0.105,4.17,'Linear data: always 4.00×',color=INK,fontsize=8.5,fontweight='demibold',va='bottom')
ax.text(0.105,2.47,'Developed frame: between 1.85× and 2.32×,\ndepending on brightness',color=INK,fontsize=8.5,fontweight='demibold',va='bottom',linespacing=1.25)
ax.plot([],[],color=BLUE,lw=2,label='linear'); ax.plot([],[],color=ORANGE,lw=2,label='developed (gamma + contrast)')
ax.legend(loc='lower left',frameon=False,fontsize=8,handlelength=1.4,borderaxespad=0.2,labelcolor=INK2)
ax.set_title('Real gain of a frame with 4× the exposure',loc='left',fontsize=9.2,fontweight='demibold',pad=8)
fig.tight_layout(pad=0.4); fig.savefig(OUT/'chart_ratio_en.svg'); plt.close(fig)
d=np.load(TREBALL/'lineal_anells.npz'); r=d['r']; k=r>=1.08
fig,ax=plt.subplots(figsize=(3.55,2.55)); clean(ax); ax.axhline(0,color='#9a9994',lw=0.6)
ax.plot(r[k],d['pB'][k],color=ORANGE,lw=1.6,solid_capstyle='round',label='composed from developed frames'); ax.plot(r[k],d['pA'][k],color=BLUE,lw=2,solid_capstyle='round',label='composed in linear light')
ax.set_xlim(1.0,4.0); ax.set_ylim(-3,3); ax.set_yticks([-2,-1,0,1,2]); ax.set_yticklabels(['−2 %','−1 %','0','+1 %','+2 %'])
ax.set_xlabel('Distance from the Sun\'s centre (solar radii)')
ax.annotate('one seam\nper change\nof exposure',xy=(2.19,1.25),xytext=(2.75,1.55),fontsize=8,color=INK2,ha='left',va='center',linespacing=1.2,arrowprops=dict(arrowstyle='-',color='#9a9994',lw=0.6,shrinkA=2,shrinkB=3))
ax.legend(loc='lower right',frameon=False,fontsize=8,handlelength=1.4,borderaxespad=0.2,labelcolor=INK2)
ax.set_title('False rings in a corona with no structure at all',loc='left',fontsize=9.2,fontweight='demibold',pad=8)
fig.tight_layout(pad=0.4); fig.savefig(OUT/'chart_rings_en.svg'); plt.close(fig)
print('done')
