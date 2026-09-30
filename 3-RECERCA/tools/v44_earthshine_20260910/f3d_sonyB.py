"""Recover independently corroborated Sony-B interior detail, outside its ghost.
Weights come from exposure/validity, never from similarity to LROC.
"""
from comu44 import *
from f3b_detall_log import local_detail
from scipy.ndimage import gaussian_filter, distance_transform_edt

def main():
    prepare();out={}
    for name in ('surface_clean','surface_sonyB'):
        g=np.load(CAU44/f'{name}_rgb.npy')[...,1];ln=np.log(np.maximum(g,1e-3));bad=~np.isfinite(ln)
        ln=ln[tuple(distance_transform_edt(bad,return_distances=False,return_indices=True))]
        d=local_detail(ln,lam_low=10.)*np.exp(gaussian_filter(ln,8));out[name]=d
        np.save(CAU44/f'{name}_detail_16_24.npy',d)
    dist=np.hypot(XX+X0-5367,YY+Y0-3545)
    t=np.clip((dist-140)/40,0,1);guard=t*t*(3-2*t)
    t=np.clip((R-.86*RL)/(.02*RL),0,1);radial=1-t*t*(3-2*t)
    wb=np.load(CAU44/'surface_sonyB_weight.npy');wc=np.load(CAU44/'surface_clean_weight.npy')
    beta=wb/np.maximum(wb+wc,1e-9)*guard*radial
    correction=beta*(out['surface_sonyB']-out['surface_clean'])
    np.save(CAU44/'sonyB_interior_correction_DN.npy',correction.astype(np.float32));np.save(CAU44/'sonyB_beta.npy',beta.astype(np.float32))
    savejson(REB44/'F3d_sonyB.json',dict(role='additional interior16-24px detail; no broad/background B',spot_center=[5367,3545],zero_inside_radius=140,full_at_radius=180,radial_taper=[.86,.88],beta_mean=float(beta[(R<.86*RL)&(dist>180)].mean()),outside_support_max=float(abs(correction[(R>=.88*RL)|(dist<=140)]).max())))

if __name__=='__main__':main()
