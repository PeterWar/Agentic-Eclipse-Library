from pathlib import Path
import json,numpy as np,tifffile as tf,cv2
from scipy.ndimage import map_coordinates,gaussian_filter1d
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path.cwd();O=R/'output/v64_geometria_20260914';A=O/'arrays';V=O/'vistes';P=R/'output/v61_interiors_limbe_20260913'
cx,cy=5376.568111973117,3776.647534140857;th=np.arange(1440)*np.pi/720;rr=np.arange(425,485,.25);gx=cx+np.cos(th[:,None])*rr;gy=cy+np.sin(th[:,None])*rr
f4=np.load(R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
def prof(a):return map_coordinates(a,[gy-2777,gx-4377],order=1,mode='nearest')
M=np.array(json.loads((P/'C3_rigid_controls.json').read_text())['matrix_global']);M[:,2]+=M[:,:2]@np.array([4377,2777])-np.array([4377,2777])
def warp(a):return cv2.warpAffine(a,M,(2000,2000),flags=cv2.INTER_CUBIC)
def load(n,c=1):return tf.imread(O/(n+'.tif'))[...,c].astype(float)/65535
fields={'Moon_mask':np.load(A/'L30_C-2.npy')/65535,'base_mask':np.load(A/'L3_C-2.npy')/65535,'base_G':load('A0_base_unmasked'),'photo_G':warp(tf.imread(P/'V61_interiors_only.tif')[...,1].astype(float)/65535),'photo_R':warp(tf.imread(P/'V61_interiors_only.tif')[...,0].astype(float)/65535),'extra12_G':np.load(A/'L83_C1.npy')/65535,'extra12_R':np.load(A/'L83_C0.npy')/65535,'final_G':load('A0_clean'),'final_R':load('A0_clean',0),'SO_alpha':load('A0_interiors_unmasked',3)}
for i in range(7):fields[f'raw{12-i:02d}_G']=warp(np.load(P/'arrays'/f'V57_L{i:02d}_C1.npy').astype(float)/65535)
profiles={n:prof(a) for n,a in fields.items()};edges={};contrast={}
for n,p in profiles.items():
    res=np.full((3,1440),np.nan);amp=np.zeros(1440)
    for i in range(1440):
        inner=np.median(p[i,(rr>=f4[i]-12)&(rr<f4[i]-6)]);outer=np.median(p[i,(rr>=f4[i]+8)&(rr<f4[i]+14)]);amp[i]=abs(outer-inner)
        if amp[i]<.00015:continue
        q=(p[i]-inner)/(outer-inner)
        for k,frac in enumerate([.25,.5,.75]):
            hits=np.flatnonzero((q[:-1]<frac)&(q[1:]>=frac)&(rr[:-1]>f4[i]-15)&(rr[:-1]<f4[i]+15))
            if len(hits):j=hits[0];res[k,i]=rr[j]+.25*(frac-q[j])/(q[j+1]-q[j])
    edges[n]=res;contrast[n]=amp
marks=json.loads((O/'A2_green_marks.json').read_text());report=[]
for m in marks:
    x,y=m['centre'];theta=np.arctan2(y-cy,x-cx)%(2*np.pi);i=round(theta*720/np.pi)%1440;inds=(np.arange(i-4,i+5)%1440).astype(int);row=dict(mark=m['index'],angle_deg=float(theta*180/np.pi),centre=m['centre'],rows={})
    fig,ax=plt.subplots(2,1,figsize=(10,7),sharex=True)
    for n in ['Moon_mask','base_mask','SO_alpha','photo_G','base_G','raw12_G','raw11_G','raw10_G','raw09_G','extra12_G']:
        e=np.nanmedian(edges[n][:,inds],axis=1);row['rows'][n]=dict(r25_50_75=e.tolist(),delta50_from_Moon=float(e[1]-np.nanmedian(edges['Moon_mask'][1,inds])),contrast=float(np.median(contrast[n][inds])))
    for n in ['Moon_mask','base_mask','SO_alpha']:ax[0].plot(rr-f4[i],np.median(profiles[n][inds],axis=0),label=n)
    for n in ['photo_G','base_G','final_G','photo_R','final_R','extra12_R']:ax[1].plot(rr-f4[i],np.median(profiles[n][inds],axis=0),label=n)
    for a in ax:a.legend(fontsize=8);a.grid(alpha=.2);a.axvline(0,color='k',lw=.5);a.set_xlim(-12,15)
    ax[1].set_xlabel('Radial distance from F4 (pixels; outward positive)');ax[0].set_title(f'Mark {m["index"]} theta={theta*180/np.pi:.2f} deg; median +/-1 degree');fig.tight_layout();fig.savefig(V/f'B1_profiles_{m["index"]:02d}.png');plt.close(fig);report.append(row)
np.savez(O/'B1_edges_profiles.npz',theta=th,radius=rr,f4=f4,**{n+'_edge':v for n,v in edges.items()},**{n+'_profile':v for n,v in profiles.items()})
(O/'B1_edges.json').write_text(json.dumps(dict(marks=report,method='Same 25/50/75-percent edge detector; inner F4-12..-6, outer F4+8..14; nonmeasurable if contrast<0.00015. Apparent edge, not intrinsic lunar radius.'),indent=2)+'\n')
for r in report:print(json.dumps(r),flush=True)
