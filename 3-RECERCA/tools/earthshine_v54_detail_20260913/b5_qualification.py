from b2_judge import *
claim();z=np.load(OUT/'arrays/B1_stacks.npz')
raw={k:z[k] for k in ['all','half0','half1','early','late']}
raw['noise_polar']=np.load(OUT/'arrays/B3_source_denoised.npy')
for j in [0,1]:raw[f'inverse{j}']=np.load(OUT/f'arrays/B4_inverse_model{j}.npy')
raw['Sony']=np.load(ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'];raw['LROC']=lroc()
pol={k:polar(v) for k,v in raw.items()};rows=[];noise=[]
for lo,hi in [(8,16),(16,24),(24,40),(40,64)]:
    b={k:band(v[0],lo,hi) for k,v in pol.items()}
    for rl,rh in [(100,300),(300,370),(370,435),(435,449)]:
        m=np.broadcast_to((rr[:,None]>=rl)&(rr[:,None]<rh),(len(rr),nt))&pol['Sony'][1]&pol['LROC'][1]
        n=.5*(b['half0']-b['half1']);tmp=.5*(b['early']-b['late']);p=b['all']
        noise.append(dict(band=[lo,hi],radius=[rl,rh],rms=float(np.std(p[m])),alternate=float(np.std(n[m])),temporal=float(np.std(tmp[m])),wiener_regional=max(0.,1-float(np.var(n[m])/max(np.var(p[m]),1e-30)))))
        for name in ['all','noise_polar','inverse0','inverse1']:
            for parity in [0,1]:
                mm=m&((np.arange(nt)[None,:]//120)%2==parity)&pol[name][1];s=compare(b[name],b['Sony'],mm);l=compare(b[name],b['LROC'],mm)
                rows.append(dict(source=name,band=[lo,hi],radius=[rl,rh],partition='fit' if parity==0 else 'heldout',Sony=s,LROC=l))
save('B5_qualification_checked.json',dict(rows=rows,noise=noise,supersedes='B5_qualification.json: empty support now explicitly null and counted; no NaN interpreted as evidence',conclusions=dict(route1='Not identified; cross-kernel injections fail even though same-kernel tests pass.',route2='Noise measured across four bands. Strong attenuation fails the 0.90 retention requirement; used only as confidence for a positive small photographic promotion.',route3='Frozen geometric preference did not improve mean Sony correlation in heldout; not promoted.',route4='Native pre-CameraRaw promotion of already corroborated 40-64 detail is the photographic candidate, pending real Camera Raw and full limb gates.')))
print('B5 done',flush=True)
