"""Lunar cross-camera registration. Fixed inner aperture only at NCC evaluation.
The input field is never multiplied by the common aperture before filtering.
Known translations test estimator equivariance, not astrophysical accuracy.
"""
from comu44 import *
from scipy.ndimage import gaussian_filter, distance_transform_edt, shift
from scipy.signal import fftconvolve

def preprocess(g):
    bad=~np.isfinite(g) | (g <= 0)
    if bad.any():
        ix=distance_transform_edt(bad,return_distances=False,return_indices=True)
        g=g[tuple(ix)]
    z=np.log(np.maximum(g,1e-3)).astype(np.float64)
    return gaussian_filter(z,6)-gaussian_filter(z,24)

def ncc(z,ref,m,rg=10):
    m=m.astype(np.float64); n=m.sum()
    v=(ref-ref[m>0].mean())*m; vv=(v*v).sum()
    def cor(a,b):
        c=fftconvolve(a,b[::-1,::-1],mode='full')
        return c[N-1-rg:N+rg,N-1-rg:N+rg].astype(float)
    sm=cor(m,z); sq=cor(m,z*z)
    cs=cor(v,z)/np.sqrt(np.maximum(vv*(sq-sm*sm/n),1e-30))
    j,i=np.unravel_index(np.argmax(cs),cs.shape)
    dx,dy=float(i-rg),float(j-rg)
    def sub(a,b,c):
        return float(np.clip(.5*(a-c)/(a-2*b+c),-.5,.5)) if a-2*b+c < -1e-10 else 0.
    if 0<i<2*rg:dx+=sub(*cs[j,i-1:i+2])
    if 0<j<2*rg:dy+=sub(*cs[j-1:j+2,i])
    return dict(dx=dx,dy=dy,r=float(cs[j,i]),boundary=bool(i in (0,2*rg) or j in (0,2*rg)))

def main():
    prepare(); fr,contacts=frames(); fr=[m for m in fr if m['exp']>=1]
    raw={m['stem']:np.load(CAU43/f"lluna_{m['tren']}_{m['stem']}_v43.npy",mmap_mode='r')[...,1] for m in fr}
    hp={s:preprocess(g) for s,g in raw.items()}
    aperture=R<.70*RL; cross=ncc(hp['DSC06987'],hp['572A2983'],aperture)
    rep=dict(method='full-field log DoG6-24 then fixed-target-aperture NCC FFT r<0.70R; cross-camera',reference='572A2983',contacts=contacts,controls=[],registre={})
    for s,imp in [('DSC06987',(5,-3)),('572A2982',(4,2)),('DSC06984',(-5,3))]:
        ref=hp['572A2983' if s.startswith('DSC') else 'DSC06987']
        a=ncc(hp[s],ref,aperture)
        # Translate original field and its actual support together; preprocessing unchanged.
        g=shift(raw[s],(imp[1],imp[0]),order=1,cval=np.nan,prefilter=False)
        b=ncc(preprocess(g),ref,aperture)
        rec=dict(stem=s,imposed=imp,recovered=[b['dx']-a['dx'],b['dy']-a['dy']],expected=[-imp[0],-imp[1]])
        rec['error_px']=float(np.hypot(rec['recovered'][0]+imp[0],rec['recovered'][1]+imp[1]));rep['controls'].append(rec)
        print(json.dumps(rec),flush=True)
    alt=(np.floor((PHI%(2*np.pi))/(np.pi/4)).astype(int)%2)==0
    for m in fr:
        s=m['stem'];ref=hp['DSC06987' if m['tren']=='vixen' else '572A2983']
        am=aperture.copy()
        if m['grup']=='sony_B':
            am &= np.hypot(XX+X0-5367, YY+Y0-3545)>100
        d=ncc(hp[s],ref,am)
        h=[ncc(hp[s],ref,am & z) for z in (alt,~alt)]
        if m['tren']=='vixen':
            for q in [d]+h:q['dx']+=cross['dx'];q['dy']+=cross['dy']
        if s=='572A2983':d.update(dx=0.,dy=0.)
        d['half_sector_distance_px']=float(np.hypot(h[0]['dx']-h[1]['dx'],h[0]['dy']-h[1]['dy']))
        d['halves']=h;d['meta']=m;d['applied']=[d['dx'],d['dy']] if d['r']>=.30 and not d['boundary'] else [0.,0.]
        rep['registre'][s]=d; print(s,json.dumps(d),flush=True)
    assert max(x['error_px'] for x in rep['controls'])<.10,'known-shift equivariance failed'
    savejson(REB44/'A2_registre.json',rep)

if __name__=='__main__':main()
