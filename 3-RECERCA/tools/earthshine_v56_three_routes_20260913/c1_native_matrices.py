"""Native calibrated samples and positive pixel integration on unchanged grid.
Latent is an optically blurred scene; no optical PSF or deconvolution assumed.
Averages the bilinear scene basis over each actual rotated native pixel using
positive GL8 quadrature. Pixel radiance is never interpolated before fitting.
"""
from common import *
from scipy.sparse import coo_matrix,save_npz
from scipy.ndimage import map_coordinates
from numpy.polynomial.legendre import leggauss
import cv2,time
cv2.setNumThreads(2);claim();n=384;x0=y0=508;fs=[m for m in frames() if m['tren']=='vixen' and m['exp']>=.5];r,t=geometry();source=np.load(OLD/'arrays/B11_repeatable_all.npz')['source'];D=np.load(OLD/'arrays/B11_repeatable_all.npz')['detector'];design=json.loads((OLD/'B3_G67_robust_hetero_full_safe_design.json').read_text());shifts=dict(zip(design['names'],design['shifts']));meta=json.loads((ROOT/'research/tools/v36_20260908/cau/vixen_meta.json').read_text())['frames'];phis=np.load(ROOT/'research/tools/v36_20260908/cau/vixen_G_phi.npy',mmap_mode='r')
protocol=dict(method=__doc__,patch=dict(x0=x0,y0=y0,size=n),sources=[m['stem'] for m in fs],quadrature_order=8,refinement_order=12,validity='Actual native q>0, finite positive variance, whole native pixel footprint inside patch. No product clipping/mask.',FPN='Frozen B11 continuous detector evaluated at actual native centres in common detector coordinates; this transports an empirical band-limited field, not a new physical dark calibration.',calibration='Cached un-interpolated per-CFA radiance; exact old k/offset; old smooth phi evaluated at each native coordinate. No interpolation of observed sample radiance.',limits=['Only a central operator pilot until full-field extension qualifies','Shared calibration and optical differences between frames remain','No absolute PSF inferred; native pixel integration is known geometry'])
if (OUT/'C1_protocol.json').exists():assert json.loads((OUT/'C1_protocol.json').read_text())==protocol
else:save('C1_protocol.json',protocol)
def matrix(points,J,order):
 node,ww=leggauss(order);node=node*.5;ww=ww*.5;entries=[];cols=[];rows=[];index=np.arange(len(points))
 for a,wa in zip(node,ww):
  for b,wb in zip(node,ww):
   q=points+np.array([a,b])@J.T;xx=q[:,0]-x0;yy=q[:,1]-y0;ix=np.floor(xx).astype(int);iy=np.floor(yy).astype(int);fx=xx-ix;fy=yy-iy
   for dx,dy,w in [(0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)]:
    rows.append(index);cols.append((iy+dy)*n+ix+dx);entries.append(w*wa*wb)
 A=coo_matrix((np.concatenate(entries),(np.concatenate(rows),np.concatenate(cols))),shape=(len(points),n*n)).tocsr();A.eliminate_zeros();return A

def field_at(phi,xg,yg):
 ax=max(0,int(np.floor(xg.min()/4))-3);bx=min(phi.shape[1],int(np.ceil(xg.max()/4))+4);ay=max(0,int(np.floor(yg.min()/4))-3);by=min(phi.shape[0],int(np.ceil(yg.max()/4))+4);cut=np.asarray(phi[ay:by,ax:bx],np.float32);up=cv2.resize(cut,(cut.shape[1]*4,cut.shape[0]*4),interpolation=cv2.INTER_LINEAR)
 # OpenCV remap has a signed-short destination dimension limit; batch points.
 v=np.concatenate([cv2.remap(up,(xg[k:k+16384]-ax*4).astype(np.float32)[:,None],(yg[k:k+16384]-ay*4).astype(np.float32)[:,None],cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE).ravel() for k in range(0,len(xg),16384)])
 return np.exp(-v)
rows=[];rng=np.random.default_rng(560913);tic=time.time()
for m in fs:
 stem=m['stem'];z=np.load(m['detector_file']);T=np.array(m['roi_to_native']);J=np.linalg.inv(T[:,:2]);sx,sy=m['shift'];j=next(i for i,v in enumerate(meta) if v['name']==stem+'.CR3');xy=[];obs=[];var=[];quality=[];channels=[]
 for c in ['G1','G2']:
  h,w=z[c].shape;yy,xx=np.mgrid[:h,:w];nx=2*xx+z[c+'_origin'][0];ny=2*yy+z[c+'_origin'][1];points=(np.stack([nx.ravel(),ny.ravel()],1)-T[:,2])@J.T;good=(points[:,0]>x0+2)&(points[:,0]<x0+n-3)&(points[:,1]>y0+2)&(points[:,1]<y0+n-3)&(z[c+'_q'].ravel()>0)&np.isfinite(z[c].ravel())&np.isfinite(z[c+'_var'].ravel())&(z[c+'_var'].ravel()>0);p=points[good];f=field_at(phis[j],p[:,0]+X0-sx,p[:,1]+Y0-sy);y=(z[c].ravel()[good]*m['k']+m['offset_RGB'][1])*f;v=z[c+'_var'].ravel()[good]*m['k']**2*f**2;shift=shifts[stem];dc=map_coordinates(D,[p[:,1]+shift[1],p[:,0]+shift[0]],order=1,mode='nearest');xy.append(p);obs.append(y-dc);var.append(v);quality.append(z[c+'_q'].ravel()[good]);channels.append(np.full(len(p),1 if c=='G1' else 2))
 xy=np.concatenate(xy);obs=np.concatenate(obs);var=np.concatenate(var);quality=np.concatenate(quality);channels=np.concatenate(channels);A=matrix(xy,J,8);test=np.linspace(0,len(xy)-1,250,dtype=int);B=matrix(xy[test],J,12);constant=float(np.max(abs(A@np.ones(n*n)-1)));xx,yy=np.meshgrid(np.arange(n)+x0,np.arange(n)+y0);plane=float(max(np.max(abs(A@xx.ravel()-xy[:,0])),np.max(abs(A@yy.ravel()-xy[:,1]))));wave=np.sin(2*np.pi*(xx*.6+yy*.8)/16);refine=float(np.max(abs(A[test]@wave.ravel()-B@wave.ravel())));u=rng.normal(size=n*n);v=rng.normal(size=len(xy));adj=float(abs((A@u)@v-u@(A.T@v))/max(abs((A@u)@v),1));assert constant<1e-12 and plane<1e-9 and adj<1e-10 and refine<.001,(constant,plane,adj,refine)
 ap=OUT/'arrays'/f'C1_{stem}_A.npz';yp=OUT/'arrays'/f'C1_{stem}_samples.npz';assert not ap.exists() and not yp.exists();save_npz(ap,A);np.savez_compressed(yp,xy=xy,observed=obs,variance=var,quality=quality,green_plane=channels,reference_prediction=A@source[y0:y0+n,x0:x0+n].ravel());rows.append(dict(stem=stem,exp=m['exp'],samples=len(xy),nnz=A.nnz,constant_error=constant,plane_error=plane,adjoint_error=adj,GL8_vs_GL12_wave16_max=refine,matrix=str(ap),samples_file=str(yp)))
 print('NATIVE MATRIX',stem,len(xy),'quadrature',refine,'s',round(time.time()-tic),flush=True)
save('C1_native_matrices.json',dict(rows=rows,method=__doc__,qualified='Positive sampling/integration numerics only. Native image reconstruction, injection and independent source judge pending.'));print('NATIVE MATRICES COMPLETE',flush=True)
