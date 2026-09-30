"""Pas 6. Dos gràfics estàtics per al PDF (paleta validada: blau #2a78d6, taronja #eb6834; tinta #0b0b0b / #52514e)."""
import numpy as np, matplotlib; matplotlib.use('Agg')
from comu import IMG, TREBALL
import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'Avenir Next','svg.fonttype':'path','font.size':8.5,'axes.edgecolor':'#9a9994','axes.linewidth':0.6,
    'xtick.color':'#52514e','ytick.color':'#52514e','axes.labelcolor':'#52514e','text.color':'#0b0b0b'})
BLAU,TAR='#2a78d6','#eb6834'; TINTA,TINTA2='#0b0b0b','#52514e'
def net(ax):
    for s in ('top','right'): ax.spines[s].set_visible(False)
    ax.grid(axis='y',color='#e4e3df',lw=0.6); ax.set_axisbelow(True); ax.tick_params(length=2.5,width=0.6)
# --- 1) quocient entre dues exposicions consecutives ---
d=np.load(TREBALL/'lineal_quocient.npz'); x=d['x']*100
fig,ax=plt.subplots(figsize=(3.55,2.55)); net(ax)
ax.plot(x,d['q_lin'],color=BLAU,lw=2,solid_capstyle='round'); ax.plot(x,d['q_dev'],color=TAR,lw=2,solid_capstyle='round')
ax.set_xscale('log'); ax.set_xlim(0.1,25); ax.set_ylim(0,4.6); ax.set_xticks([0.1,1,10,25]); ax.set_xticklabels(['0,1 %','1 %','10 %','25 %'])
ax.set_yticks([0,1,2,3,4]); ax.set_yticklabels(['0','1×','2×','3×','4×'])
ax.set_xlabel('Brillantor del punt a la foto curta (% de la saturació)'); 
ax.text(0.105,4.17,'Dada lineal: sempre 4,00×',color=TINTA,fontsize=8.5,fontweight='demibold',va='bottom')
ax.text(0.105,2.47,'Foto revelada: entre 1,85× i 2,32×,\nsegons la brillantor',color=TINTA,fontsize=8.5,fontweight='demibold',va='bottom',linespacing=1.25)
ax.plot([],[],color=BLAU,lw=2,label='lineal'); ax.plot([],[],color=TAR,lw=2,label='revelada (gamma + contrast)')
ax.legend(loc='lower left',frameon=False,fontsize=8,handlelength=1.4,borderaxespad=0.2,labelcolor=TINTA2)
ax.set_title('Guany real d\'una foto amb 4× més temps',loc='left',fontsize=9.2,fontweight='demibold',pad=8)
fig.tight_layout(pad=0.4); fig.savefig(IMG/'graf_quocient.svg'); plt.close(fig)
# --- 2) anells falsos ---
d=np.load(TREBALL/'lineal_anells.npz'); r=d['r']; k=r>=1.08
fig,ax=plt.subplots(figsize=(3.55,2.55)); net(ax)
ax.axhline(0,color='#9a9994',lw=0.6)
ax.plot(r[k],d['pB'][k],color=TAR,lw=1.6,solid_capstyle='round',label='composta sobre fotos revelades'); ax.plot(r[k],d['pA'][k],color=BLAU,lw=2,solid_capstyle='round',label='composta en lineal')
ax.set_xlim(1.0,4.0); ax.set_ylim(-3,3); ax.set_yticks([-2,-1,0,1,2]); ax.set_yticklabels(['−2 %','−1 %','0','+1 %','+2 %'])
ax.set_xticks([1,1.5,2,2.5,3,3.5,4]); ax.set_xticklabels(['1','1,5','2','2,5','3','3,5','4'])
ax.set_xlabel('Distància al centre del Sol (radis solars)')
ax.annotate('una costura\nper cada canvi\nd\'exposició',xy=(2.19,1.25),xytext=(2.75,1.55),fontsize=8,color=TINTA2,ha='left',va='center',linespacing=1.2,arrowprops=dict(arrowstyle='-',color='#9a9994',lw=0.6,shrinkA=2,shrinkB=3))
ax.legend(loc='lower right',frameon=False,fontsize=8,handlelength=1.4,borderaxespad=0.2,labelcolor=TINTA2)
ax.set_title('Anells falsos en una corona sense cap estructura',loc='left',fontsize=9.2,fontweight='demibold',pad=8)
fig.tight_layout(pad=0.4); fig.savefig(IMG/'graf_anells.svg'); plt.close(fig)
print('fet')
