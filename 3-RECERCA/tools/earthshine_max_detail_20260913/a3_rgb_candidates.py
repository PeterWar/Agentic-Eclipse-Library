"""Freeze photon-weighted RGB source candidates without Sony fitting.
Photometric latent-G scale from A2b training. DC offsets from training only;
no signal from an external reference in the reconstruction.
"""
from common import *
claim();z=np.load(OUT/'arrays/A2_color_stacks.npz');s=json.loads((OUT/'A2b_rgb_training_screen.json').read_text())['color_texture_slopes_relative_G'];slopes={'R':s['R'],'G1':1.,'G2':1.,'B':s['B']};r,t=geometry();fit=(r<350)&(r>60)&((t//(np.pi/6)).astype(int)%2==0)
offsets={c:float(np.median(z['fit_G'][fit]-z['fit_'+c][fit]/slopes[c])) for c in slopes}
save('A3_model_frozen.json',dict(slopes=slopes,offsets=offsets,primary='RGB',ablations={'G':['G1','G2'],'R':['R'],'B':['B'],'GR':['G1','G2','R'],'GB':['G1','G2','B'],'RGB':['R','G1','G2','B']},weights='Inverse propagated photon/read variance per calibrated plane, smooth4px, inherited G exposure-class alpha; scaled by slope squared. No Sony selection.',scope='SOURCE candidates only. Scalar texture scale does not guarantee identical lunar albedo at different wavelengths. No photographic product yet.',training='A0/A2b only; reserved frames and Sony excluded from slope/offset'))
arr={};fractions={}
groups={'G':['G1','G2'],'R':['R'],'B':['B'],'GR':['G1','G2','R'],'GB':['G1','G2','B'],'RGB':['R','G1','G2','B']}
for part in ['all','fit','test','early','late']:
    for name,cc in groups.items():
        num=np.zeros((N,N));den=num.copy()
        for c in cc:
            w=z['weight_'+part+'_'+c]*slopes[c]**2;a=z[part+'_'+c]/slopes[c]+offsets[c];good=np.isfinite(a);num+=np.where(good,a,0)*w;den+=w*good
        arr[part+'_'+name]=np.where(den>0,num/np.maximum(den,1e-30),np.nan).astype(np.float32)
        if part=='all' and name=='RGB':
            for c in cc:fractions[c]=float(np.median((z['weight_all_'+c]*slopes[c]**2/np.maximum(den,1e-30))[fit]))
np.savez_compressed(OUT/'arrays/A3_rgb_candidates.npz',**arr)
save('A3_candidates.json',dict(sha256=sha(OUT/'arrays/A3_rgb_candidates.npz'),RGB_median_weights=fractions,producer='Vixen only'))
print('FROZEN RGB FRACTIONS',fractions,flush=True)
