"""External judge of frozen FPN model, including all-pilot refit."""
from common import *
from scipy.fft import rfft2,irfft2
from spectral import fft_stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
claim();j=json.loads((OUT/'B1_fpn_pilot.json').read_text());d=json.loads((OUT/'B0_fpn_design.json').read_text());z=np.load(OUT/'arrays/B1_fpn_pilot.npz');n=512;sl=np.s_[444:956,444:956];win=z['window'];y,x=np.mgrid[:n,:n]/n*2-1;B=np.stack([x**i*y**j for i in range(4) for j in range(4-i)],-1);bw=B.reshape(-1,10)*win.ravel()[:,None]
def encode(a):
    c=np.linalg.lstsq(bw,a.ravel()*win.ravel(),rcond=None)[0];return rfft2((a-B@c)*win)
def gm(z):return (z['G1']*z['G1_q']+z['G2']*z['G2_q'])/np.maximum(z['G1_q']+z['G2_q'],1e-30)
weights=[];source=np.zeros((n,n));den=0
for stem in d['names']:
    q=np.load(OUT/'native'/('vixen_'+stem+'.npz'));w=1/np.median((q['G1_var'][sl]+q['G2_var'][sl])/4);weights.append(w);source+=w*gm(q)[sl];den+=w
source/=den;weights=np.array(weights);weights/=weights.sum();Y=z['raw_fft'];idx=z['freq_indices'];sh=np.array(d['shifts_common']);fy=np.fft.fftfreq(n)[:,None];fx=np.fft.rfftfreq(n)[None,:];phase=np.exp(2j*np.pi*(sh[:,0,None,None]*fx+sh[:,1,None,None]*fy)).reshape(len(sh),-1)[:,idx]
assert j['selected']['kind']=='fixed';lam=j['selected']['ridge'];rho=np.sum(weights[:,None]*phase,axis=0);YY=Y.reshape(len(sh),-1)[:,idx];b0=np.sum(weights[:,None]*YY,axis=0);b1=np.sum(weights[:,None]*phase.conj()*YY,axis=0);dd=1+lam-abs(rho)**2
S=(b0*(1+lam)-rho*b1)/dd;D=(b1-rho.conj()*b0)/dd
ff=np.average(Y,weights=weights,axis=0);base=ff.copy();ff.ravel()[idx]=S
delta=irfft2(ff-base,s=(n,n));delta=np.divide(delta,win,out=np.zeros_like(delta),where=win>.2)
np.savez_compressed(OUT/'arrays/B2_fpn_all.npz',base=base,scene=ff,delta=delta,source=source,detector_coeff=D)
sony=np.load(ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'][sl];g67=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/B1_stacks.npz')['all'][sl]
l=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];lr=np.zeros((N,N));oy,ox=bb[1]-Y0,bb[0]-X0;lr[oy:oy+l.shape[0],ox:ox+l.shape[1]]=l[...,:3].mean(-1);lr=lr[sl]
F={'baseline_training':z['baseline'],'FPN_training':z['scene'],'baseline_all':base,'FPN_all':ff,'G67':encode(g67),'Sony':encode(sony),'LROC':encode(lr)};rows=[]
for band in [[16,24],[24,40],[40,64]]:
    for name in F:
        if name in ['Sony','LROC']:continue
        vs=fft_stats(F[name],F['Sony'],band,n)[0];vl=fft_stats(F[name],F['LROC'],band,n)[0]
        ns=[fft_stats(F[name],encode(np.rot90(sony,i)),band,n)[0] for i in [1,2,3]];nl=[fft_stats(F[name],encode(np.rot90(lr,i)),band,n)[0] for i in [1,2,3]]
        row=dict(band=band,candidate=name,Sony=vs,LROC=vl,null_Sony=max(map(abs,ns)),null_LROC=max(map(abs,nl)),pass_null=vs>max(map(abs,ns)) and vl>max(map(abs,nl)));rows.append(row);print(row,flush=True)
save('B2_fpn_external.json',dict(rows=rows,method=__doc__,scope='Single central512 patch, 2D Fourier amplitudes; no full-disc claim',model_sha256=sha(OUT/'B1_model_selected.json')))
# Full-frame reference plus faithful diagnostic maps, fixed numerical scales.
fig=plt.figure(figsize=(14,10),layout='constrained');gs=fig.add_gridspec(2,3)
full=plt.imread(ROOT/'output/earthshine_v54_detail_20260913/vistes/E3_Photoshop_V54_full.png');ax=fig.add_subplot(gs[0,:2]);ax.imshow(full);ax.set_title('V54 preservada · llenç sencer');ax.axis('off')
ax=fig.add_subplot(gs[0,2]);c=np.array(d['shifts_common']);ax.plot(c[:,0],c[:,1],'o-');ax.set_title('Deriva real, píxels del llenç');ax.set_aspect('equal');ax.set_xlabel('X');ax.set_ylabel('Y')
freq=np.hypot(fx,fy);H=(freq>=1/64)&(freq<=1/16)
for col,(name,Ff) in enumerate([('Apilat verd · 16–64 px',base),('Pilot separat · 16–64 px',ff),('Diferència del pilot',ff-base)]):
    a=irfft2(Ff*H,s=(n,n));ax=fig.add_subplot(gs[1,col]);ax.imshow(a,cmap='gray',vmin=-2,vmax=2);ax.set_title(name+'\n±2 unitats G; mateixa escala');ax.axis('off')
fig.savefig(OUT/'vistes/B2_fpn_diagnostic.png',dpi=140);plt.close(fig)
