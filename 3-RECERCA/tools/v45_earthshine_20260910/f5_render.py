"""Photographic log-relief derivative; calibrated native-green arrays retained.
No synthetic lunar terrain. Reuse fixed measured Vixen boundary and09 join.
"""
from comu45 import *
from scipy.special import ndtr

def main():
    claim45();source=sys.argv[1] if len(sys.argv)>1 else 'combined_corrected'
    h=np.load(CAU45/(source+'_logdetail.npy'));g=np.load(CAU45/(source+'.npy'))
    old=json.loads((REB44/'F5_render.json').read_text());col=np.array(old['color']);level=old['level_linear']
    base=np.load(CAU44/'pere09_rgb.npy').astype(float)/65535;lin=comu.a_lineal(base)
    w=np.load(CAU44/'join_coverage.npy')
    # The exact V44 photometric protection is inherited through the stored
    # zero contribution pixels; reconstruct physical protected decision.
    from importlib.util import spec_from_file_location,module_from_spec
    sp=spec_from_file_location('v44render',HERE44/'f5_render.py');m=module_from_spec(sp);sp.loader.exec_module(m)
    edge=np.load(CAU44/'vixen_optical_edge.npy');wcheck,_,protected,jrep=m.join_response(base,edge)
    assert np.max(abs(w-wcheck))<1e-7
    med=np.median(h[R<.8*RL]);rho=h-med
    rep={'source':source,'relief':'single Cartesian log highpass sigma16 after unsmoothed-radial cubic background; contrast-relative derivative, not recovered absolute lunar photometry','no_detail_taper':True,'color':col.tolist(),'level_linear':level,'same_geometry_and_join_V44':True,'variants':{},'join':jrep}
    def disp(k):return to_srgb((level*col)[None,None,:]*np.exp(np.clip(k*rho,-12,12))[...,None],np.ones_like(R,bool))
    for title,contrast in [('natural',.12),('relleu24',.24)]:
        lo,hi=0.,200.
        for _ in range(26):
            k=(lo+hi)/2;im=disp(k);v=im[...,1][R<.8*RL];cc=np.diff(np.percentile(v,[5,95]))[0]/np.median(v)
            if cc<contrast:lo=k
            else:hi=k
        k=(lo+hi)/2;disc=disp(k)
        target=np.clip(comu.a_srgb(lin+w[...,None]*comu.a_lineal(disc)),0,1)
        delta=np.maximum(target-base,0);delta[protected]=0;target=np.clip(base+delta,0,1)
        u=np.round(delta*65535).astype(np.uint16)
        np.save(CAU45/f'earthshine_{title}_delta_u16.npy',u);np.save(CAU45/f'earthshine_{title}_disc.npy',disc.astype(np.float32))
        png45(f'F5_{title}_compost_1a1.png',target);png45(f'F5_{title}_disc_1a1.png',disc*(R<454)[...,None])
        rep['variants'][title]=dict(K=float(k),contrast_target=contrast,protected_changed=int(np.any(u[protected]!=0,axis=1).sum()),outside470_nonzero=int(np.any(u[R>470]!=0,axis=1).sum()))
        if title=='natural':
            np.save(CAU45/'expected_moon_u16.npy',np.clip(np.load(CAU44/'pere09_rgb.npy').astype(np.uint32)+u,0,65535).astype(np.uint16))
            np.save(CAU45/'standalone_disc_u16.npy',np.round(disc*65535).astype(np.uint16))
            # Geometric antialias only for separate inspection. No imported09
            # perles/chromosphere protection in this standalone surface view.
            mask=np.zeros_like(R,dtype=float)
            for oy in [-.375,-.125,.125,.375]:
                for ox in [-.375,-.125,.125,.375]:
                    ph=np.arctan2(YY+oy-CYT,XX+ox-CXT)%(2*np.pi);rl=np.interp(ph*len(edge)/(2*np.pi),np.arange(len(edge)),edge,period=len(edge))
                    mask+=(np.hypot(XX+ox-CXT,YY+oy-CYT)<rl)/16
            np.save(CAU45/'standalone_mask_u16.npy',np.round(mask*65535).astype(np.uint16))
    hdr=to_srgb(np.repeat(np.nan_to_num(g)[...,None],3,axis=2),R<RL+40)
    np.save(CAU45/'earthshine_HDR_u16.npy',np.round(hdr*65535).astype(np.uint16))
    np.save(CAU45/'HDR_mask_u16.npy',np.load(CAU44/'HDR_mask_u16.npy'))
    savejson(REB45/'F5_render.json',rep);print(json.dumps(rep),flush=True)
if __name__=='__main__':main()
