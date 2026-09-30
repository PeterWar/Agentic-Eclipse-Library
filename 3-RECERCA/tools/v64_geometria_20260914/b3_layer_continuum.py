from pathlib import Path
import numpy as np,json,tifffile as tf,cv2
from scipy.ndimage import gaussian_filter,label,binary_dilation,map_coordinates
R=Path.cwd();O=R/'output/v64_geometria_20260914';P=R/'output/v61_interiors_limbe_20260913';A=O/'arrays'
j=json.loads((P/'A0_sources.json').read_text())['V57']['layers'];bgmix=np.zeros((2000,2000),float);S=np.zeros((2000,2000,3),float);raw=[];mask=[];bgs=[]
for i in range(7):
    rgb=np.stack([np.load(P/'arrays'/f'V57_L{i:02d}_C{c}.npy') for c in range(3)],-1).astype(float)/65535;raw.append(rgb)
    m=np.load(P/'arrays'/f'V57_L{i:02d}_C-2.npy').astype(float)/65535
    if not j[i]['visible']:m*=0
    mask.append(m)
    # Same physical-dark-core concept, exposure-independent classification:
    # use the connected low-intensity interior relative to each photo's
    # own near-limb continuum, not one absolute threshold for all exposures.
    yy,xx=np.ogrid[2777:4777,4377:6377];rad=np.hypot(xx-5376.568111973117,yy-3776.647534140857)
    typical=np.median(rgb[...,1][(rad>470)&(rad<480)]);lab,n=label(rgb[...,1]<typical*.15);core=lab==lab[1000,1000]
    valid=~binary_dilation(core,iterations=5);den=gaussian_filter(valid.astype(float),8);bg=gaussian_filter(rgb[...,1]*valid,8)/np.maximum(den,1e-8);bgs.append(bg)
    bgmix+=m*(bg-bgmix);S+=m[...,None]*(rgb-S)
M=np.array(json.loads((P/'C3_rigid_controls.json').read_text())['matrix_global']);M[:,2]+=M[:,:2]@np.array([4377,2777])-np.array([4377,2777])
def warp(a):return cv2.warpAffine(a,M,(2000,2000),flags=cv2.INTER_CUBIC)
native=tf.imread(P/'V61_interiors_only.tif')[...,:3].astype(float)/65535
alpha=np.clip(native[...,1]/np.maximum(bgmix,1e-8),0,1)
np.save(A/'B3_continuum_mix.npy',warp(bgmix));np.save(A/'B3_alpha_probe.npy',warp(alpha));np.save(A/'B3_alpha_source.npy',alpha)
print('DIAGNOSTIC PER-LAYER CONTINUUM; no product promoted',flush=True)
