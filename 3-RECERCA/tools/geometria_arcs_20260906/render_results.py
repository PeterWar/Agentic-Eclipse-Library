from geometry import *
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
from PIL import Image,ImageDraw

def read(name):return json.loads(Path(RUN.rebut(name+'.json')).read_text())

# Whole canvas context, no fitted circles drawn as if accepted.
mask=np.load(ROOT/'research/tools/v29/cau_final/fusion_support.npy',mmap_mode='r')
fig,axes=plt.subplots(1,2,figsize=(15,6))
for ax,tag in zip(axes,['01','02']):
    a=np.load(ROOT/f'research/tools/v31/cau/{tag}_final_u16.npy',mmap_mode='r')
    display=np.asarray(a[::6,::6],float)/65535
    ax.imshow(np.where(mask[::6,::6],display,np.nan),cmap='gray',vmin=.3,vmax=.7,
        extent=[0,a.shape[1],a.shape[0],0],interpolation='nearest')
    for r in [2.5*RS,4.5*RS]:ax.add_patch(Circle((CX,CY),r,fill=False,color='cyan',ls='--',lw=.8))
    ax.plot(CX,CY,'+',color='yellow',ms=8)
    for x,y in [(5715,2200),(5130,5160)]:ax.add_patch(Rectangle((x-256,y-256),512,512,fill=False,color='orange',lw=.8))
    ax.set_title('Capa '+tag+' · V31 completa');ax.set_xlabel('x [px]');ax.set_ylabel('y [px]')
fig.suptitle('Cian: només límits de la regió estudiada; groc: centre solar de referència',fontsize=11)
fig.tight_layout();fig.savefig(RUN.vista('01_context_llenc_sencer.png'),dpi=125);plt.close(fig)

# Unaltered native sample panels; fixed display for both layers/locations.
plate=Image.new('RGB',(1024,1084),(20,20,20));draw=ImageDraw.Draw(plate)
for i,(name,x,y) in enumerate([('Nord',5715,2200),('Sud',5130,5160)]):
    for j,tag in enumerate(['01','02']):
        a=np.load(ROOT/f'research/tools/v31/cau/{tag}_final_u16.npy',mmap_mode='r')
        z=np.asarray(a[y-256:y+256,x-256:x+256],float)/65535
        im=Image.fromarray(np.uint8(np.clip((z-.3)/.4,0,1)*255)).convert('RGB')
        plate.paste(im,(j*512,i*542+30));draw.text((j*512+8,i*542+8),f'{name} | {tag} | 1 px = 1 px | gris 0.3..0.7',fill='white')
plate.save(RUN.vista('02_finestres_natives.png'))

fig,axes=plt.subplots(1,2,figsize=(12,5))
for name,label,model in [('synthetic_circle_fine','Cercle conegut','circle_free'),('synthetic_ellipse_fine','El·lipse coneguda','ellipse_free')]:
    rep=read(name);true=np.array(rep['provenance']['true_center'])
    for row in rep['fits']:
        if row['model']==model:
            err=np.array(row['center_xy'])-true
            axes[0].scatter(*err,label=label+f" · partició{row['training_parity']}")
axes[0].set_xlim(-.3,.3);axes[0].set_ylim(.3,-.3);axes[0].set_title('Controls: error respecte del centre conegut')
for ci,(name,label) in enumerate([('01_final_fine','01 fina'),('02_final_fine','02 fina'),('01_final_wide','01 ampla'),('02_final_wide','02 ampla'),('01_H1_fine','Delta H1 de01')]):
    rep=read(name)
    for row in rep['fits']:
        if row['model']=='circle_free':
            p=row['parameters'];axes[1].scatter(*p,color=f'C{ci}',marker='o' if row['training_parity']==0 else 'x',label=label if row['training_parity']==0 else None)
axes[1].set_xlim(-140,140);axes[1].set_ylim(140,-140);axes[1].set_title('Centres reals no acceptats; H1 com a control')
for ax in axes:
    ax.axhline(0,color='gray',lw=.5);ax.axvline(0,color='gray',lw=.5);ax.set_aspect('equal')
    ax.set_xlabel('Desplaçament x [px]');ax.set_ylabel('Desplaçament y [px]');ax.legend(fontsize=8)
fig.tight_layout();fig.savefig(RUN.vista('03_centres_i_controls.png'),dpi=150);plt.close(fig)

fig,ax=plt.subplots(figsize=(11,5))
for name,label in [('01_final','01 final'),('02_final','02 final'),('01_preH1','01 abans H1'),('synthetic_null','Control de soroll')]:
    rep=read(name+'_orientation');ss=[]
    for r in rep['fits']:
        if r['model']=='solar_fixed':ss.extend(r['sectors'])
    ss.sort(key=lambda x:x['sector'])
    ax.plot([(s['sector']+.5)*15 for s in ss],[s['score'] for s in ss],'-o',ms=3,label=label)
ax.axhline(0,color='black',lw=.7);ax.set_xlabel('Angle del sector [graus]');ax.set_ylabel('Alineació de normals: + tangencial / − radial')
ax.set_title('Orientació local respecte del centre solar; no prova cercles sencers');ax.legend()
fig.tight_layout();fig.savefig(RUN.vista('04_orientacio_per_sectors.png'),dpi=150);plt.close(fig)
log('summary figures COMPLETE')
