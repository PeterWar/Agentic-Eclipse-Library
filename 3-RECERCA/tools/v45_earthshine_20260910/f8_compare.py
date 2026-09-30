"""Fixed source comparison for the user-marked west limb. Diagnostic crops only."""
from comu45 import *
from f2_temporal import SURFACE
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

def main():
    claim45();sources=[];report=[];sector=(PHI%(2*np.pi)>np.radians(180))&(PHI%(2*np.pi)<np.radians(195))
    for stem,title in [('572A2972','Vixen · C2 +11,4 s · 1/2 s'),('572A2990','Vixen · C2 +73,1 s · 1/2 s')]:
        p=CAU45/f'native_vixen_{stem}.npz';d=np.load(p);g=d['g'];valid=np.isfinite(g)&(d['q']>0);sources.append((g,valid,title))
        ring=sector&(R>440)&(R<449)&SURFACE;last=sector&(R>449)&(R<455)&SURFACE
        report.append(dict(stem=stem,sha256=sha(p),median_G_440_449=float(np.nanmedian(g[ring&valid])),valid_fraction_449_to_observed_edge=float(valid[last].mean()),scope='either nativegreen contributes; fixed sector180–195; physical observed lunar support'))
    f,axs=plt.subplots(1,3,figsize=(12,5.8),gridspec_kw={'width_ratios':[1,1,1.6]},layout='constrained')
    crop=np.s_[590:750,220:345];cmap=plt.colormaps['gray'].copy();cmap.set_bad('#d473d1')
    for ax,(g,v,title) in zip(axs[:2],sources):
        im=ax.imshow(np.ma.array(g[crop],mask=~v[crop]),cmap=cmap,norm=LogNorm(550,25000),origin='upper',interpolation='nearest',extent=(X0+220,X0+345,Y0+750,Y0+590))
        ax.set_title(title,fontsize=11);ax.set_xlabel('x del llenç original');ax.set_ylabel('y del llenç original')
    f.colorbar(im,ax=list(axs[:2]),label='G natiu calibrat · mateixa escala',shrink=.75)
    rr=np.arange(400,455)
    for g,v,title in sources:
        med=[np.nanmedian(g[sector&(R>=r)&(R<r+1)&SURFACE&v]) for r in rr]
        axs[2].plot(rr+.5,med,label=title,lw=1.6)
    for key,label,ls in [('combined_all','Dos trens · tots els instants','--'),('combined_reference','Dos trens · preferència temporal','-')]:
        g=np.load(CAU45/(key+'.npy'));med=[np.nanmedian(g[sector&(R>=r)&(R<r+1)&SURFACE]) for r in rr];axs[2].plot(rr+.5,med,label=label,ls=ls,lw=1.6)
    axs[2].set_yscale('log');axs[2].set_ylim(450,30000);axs[2].set_xlabel('Radi lunar al llenç (px)');axs[2].set_ylabel('Mediana G natiu · sector 180–195°');axs[2].grid(alpha=.2);axs[2].legend(fontsize=8,loc='upper left')
    f.suptitle('Zona lila: menys contaminació en alguns instants tardans; el vel comú continua present',fontsize=13)
    f.text(.02,-.025,'Lila als retalls = sense mostra verda vàlida. Els retalls són diagnòstics; el producte conserva 10551 × 7506 px.\nLa baixada de llum contaminant no demostra, per si sola, textura lunar recuperada.',fontsize=9)
    p=VIS45/'F8_comparacio_temporal_lila.png';f.savefig(p,dpi=160,bbox_inches='tight');plt.close(f)
    savejson(REB45/'F8_temporal_comparison.json',dict(rows=report,F2_sha256=sha(REB45/'F2_temporal.json'),figure=str(p),conclusion='later matched0.5sVixen lower contamination; not whole-limb recovery'))
    print(report,flush=True)
if __name__=='__main__':main()
