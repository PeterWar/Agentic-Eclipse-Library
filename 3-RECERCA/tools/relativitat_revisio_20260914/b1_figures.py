from a1_inputs import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
TEAL='#087f83';NAVY='#182e48';GOLD='#c17620';GREY='#93a0ad'
F=O/'figures';F.mkdir(exist_ok=True)
def save(fig,name):
    fig.savefig(F/(name+'.png'),bbox_inches='tight',facecolor='white');fig.savefig(F/(name+'.pdf'),bbox_inches='tight',facecolor='white');plt.close(fig)
def main():
    d=pd.read_csv(O/'A3_analysis_sample.csv');geo=pd.read_csv(O/'A3_geometry_forecasts.csv')
    fig,ax=plt.subplots(figsize=(8,3.8));samples=['old_literal','old_identified','V65_eligible5','V65_eligible10'];labels=['Estudi antic\n38 + 24 fonts','Antigues identificades\n38 + 22 estrelles','Nova selecció SNR ≥ 5\n43 + 22 estrelles','Selecció SNR ≥ 10\n21 + 10 estrelles']
    for j,(kind,lab,col) in enumerate([('similarity','Similitud: trasllat, gir i escala',TEAL),('radial','Afí + termes radials de grau 3',GOLD)]):
        vals=[float(geo[(geo.source=='combined_conditional')&(geo['sample']==s)&(geo.kind==kind)].sigma_epsilon.iloc[0]) for s in samples]
        bars=ax.bar(np.arange(4)+(j-.5)*.33,vals,.31,label=lab,color=col)
        for b,v in zip(bars,vals):ax.text(b.get_x()+b.get_width()/2,v+.025,f'{v:.3f}',ha='center',fontsize=9)
    ax.axhline(.1,color=NAVY,ls='--',lw=1,label='Objectiu 5σ GR / mitja deflexió: σ(ε) ≤ 0,10');ax.set_xticks(range(4),labels);ax.set_ylabel('Incertesa prevista σ(ε)');ax.set_ylim(0,1.9);ax.legend(fontsize=8,loc='upper left');ax.grid(axis='y',alpha=.14);ax.set_axisbelow(True);fig.tight_layout();save(fig,'01_forecast')
    fig,ax=plt.subplots(figsize=(7.5,4.6));a=d[d.use5].drop_duplicates('TYC');strong=set(d[d.use10].TYC);s=a.TYC.isin(strong)
    x=a.x0/946.66;y=a.y0/946.66
    ax.scatter(x[~s],y[~s],s=20,facecolors='none',edgecolors=GREY,label='28 fonts: llindar 5, no 10')
    ax.scatter(x[s],y[s],s=18,color=TEAL,label='23 fonts: llindar 10')
    ax.add_patch(Circle((0,0),1,color=NAVY));
    for r in [3,6,9,12]:ax.add_patch(Circle((0,0),r,fill=False,color=GREY,lw=.5,ls=':'))
    for hip in [46335,46345]:
        q=a[a.HIP==hip].iloc[0];ax.annotate('HIP '+str(hip),(q.x0/946.66,q.y0/946.66),xytext=(30,15 if hip==46335 else -35),textcoords='offset points',fontsize=9,arrowprops=dict(arrowstyle='-',color=NAVY))
    ax.set_aspect('equal');ax.set_xlim(-13,14);ax.set_ylim(-10,11);ax.set_xlabel('Coordenada horitzontal / radi solar');ax.set_ylabel('Cap al zenit / radi solar');ax.legend(loc='lower left',fontsize=8);fig.tight_layout();save(fig,'02_field2026')
    fig,ax=plt.subplots(figsize=(7.8,3.9));f=pd.read_csv(O/'A4_Hipparcos_2027_field.csv');a=f[f.V<=8]
    x=a.x_as/3600;y=a.y_as/3600
    ax.scatter(x,y,s=np.clip((9-a.V)**2*9,10,150),color=TEAL,zorder=3)
    rs=945.177/3600;ax.add_patch(Circle((0,0),rs,color=NAVY));
    for width,height,col,label in [(7968*3.202/3600,5320*3.202/3600,GREY,'Sony: 7,09° × 4,73°'),(6960*2.1495/3600,4640*2.1495/3600,GOLD,'Vixen: 4,16° × 2,77°')]:
        ax.add_patch(Rectangle((-width/2,-height/2),width,height,fill=False,color=col,lw=1.5,label=label))
    for hip,name,offset in [(43206,'HIP 43206\n1,80 R☉',(16,-30)),(42911,'δ Cancri\n3,11 R☉',(-65,20))]:
        q=f[f.HIP==hip].iloc[0];ax.annotate(name,(q.x_as/3600,q.y_as/3600),xytext=offset,textcoords='offset points',fontsize=8,arrowprops=dict(arrowstyle='-',color=NAVY))
    ax.set_aspect('equal');ax.set_xlim(-4.2,4.2);ax.set_ylim(-3.4,3.4);ax.set_xlabel('Est del Sol (graus)');ax.set_ylabel('Nord del Sol (graus)');ax.legend(loc='lower left',fontsize=8);fig.tight_layout();save(fig,'03_field2027')
    sc=pd.read_csv(O/'A4_2027_conditional_scenarios.csv');fig,ax=plt.subplots(figsize=(7.8,3.6))
    for tag,col in [('Sony',TEAL),('Vixen',GOLD)]:
        a=sc[(sc.source==tag)&(sc.V_limit==8)&(sc.kind=='radial')];ax.plot(a.per_star_sigma_arcsec*1000,a.sigma_epsilon*100,'o-',color=col,label=f'{tag}: {int(a.n.iloc[0])} estrelles, termes radials lliures')
    ax.axhline(10,color=NAVY,ls='--',lw=1);ax.text(135,10.7,'Objectiu 10%',fontsize=9);ax.set_xlabel('Error independent per estrella, després de combinar RAW (mas)');ax.set_ylabel('σ(ε), percentatge');ax.set_ylim(0,27);ax.grid(alpha=.15);ax.legend(fontsize=8);fig.tight_layout();save(fig,'04_scenarios2027')
    print('Four scientific figures generated; no image raster edited.')
if __name__=='__main__':main()
