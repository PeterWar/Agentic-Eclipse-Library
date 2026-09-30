"""Lunar stacks in a common clock. Separate surface from epoch-limited limb.
Sony B is kept as an independent diagnostic; never enters the clean HDR.
"""
from comu44 import *

def main():
    prepare();inp=json.loads((REB44/'B2_inputs.json').read_text());fr=inp['frames']
    old=json.loads((ROOT/'output/v43_earthshine_20260910/4-rebuts/F2_apilat_lunar.json').read_text())
    gain=np.array(old['guany_vixen_sobre_sony']);gs={'vixen':1.,'sony':old['g_sensor_relatiu_sony_sobre_vixen']}
    a=np.clip((R-.85*RL)/(.08*RL),0,1);a=a*a*(3-2*a)
    groups={
        'surface_clean':lambda m:m['grup']!='sony_B',
        'surface_vixen':lambda m:m['tren']=='vixen',
        'surface_sonyA':lambda m:m['grup']=='sony_A',
        'surface_sonyB':lambda m:m['grup']=='sony_B',
        'epoch_clean':lambda m:m['grup']!='sony_B',
        'epoch_vixen':lambda m:m['tren']=='vixen',
    }
    rep={'clock':'t_mid_vixen=t_start_sensor+exp/2-C2_sensor+C2_vixen','T0_vixen':15.,'tau':10.,'groups':{}}
    for name,pred in groups.items():
        num=np.zeros((N,N,3),np.float64);den=np.zeros((N,N),np.float64);den2=np.zeros_like(den);nv=np.zeros_like(den)
        count=0;wt_rows=[]
        for m in fr:
            if not pred(m):continue
            z=np.load(m['path']);p=np.load(m['weight']);ok=np.all(np.isfinite(z),axis=2)&(p>0)
            p=np.where(ok,p/max(float(p.max()),1e-20),0.)
            w=p*m['exp']*gs[m['tren']]
            if name.startswith('epoch'):
                wt=np.exp(-((m['t_mid_vixen']-15)/10)**2);w*=((1-a)+a*wt)
            if m['tren']=='sony':z=z*gain
            num+=np.nan_to_num(z)*w[...,None];den+=w;den2+=w*w;nv+=(w>1e-9)
            wt_rows.append(dict(stem=m['stem'],w_inner=float(w[R<.7*RL].sum()),w_outer=float(w[(R>.85*RL)&(R<.95*RL)].sum()),w_limb=float(w[abs(R-454)<2].sum())))
            count+=1
        z=(num/np.maximum(den,1e-30)[...,None]).astype(np.float32);z[den==0]=np.nan
        neff=(den*den/np.maximum(den2,1e-30)).astype(np.float32)
        np.save(CAU44/f'{name}_rgb.npy',z);np.save(CAU44/f'{name}_weight.npy',den.astype(np.float32));np.save(CAU44/f'{name}_neff.npy',neff)
        rep['groups'][name]=dict(n_frames=count,missing_disc=int(((R<RL)&(den==0)).sum()),neff_inner=float(np.median(neff[R<.7*RL])),neff_outer=float(np.median(neff[(R>.85*RL)&(R<.9*RL)])),weights=wt_rows)
        png(f'F2_{name}_tone.png',to_srgb(np.nan_to_num(z),np.isfinite(z[...,1])&(R<RL+40)))
        print(name,{k:v for k,v in rep['groups'][name].items() if k!='weights'},flush=True)
    savejson(REB44/'F2_stacks.json',rep)

if __name__=='__main__':main()
