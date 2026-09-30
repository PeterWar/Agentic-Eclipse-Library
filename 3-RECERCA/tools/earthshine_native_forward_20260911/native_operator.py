"""Positive native-pixel forward quadrature for separate lunar/solar fields.
K is an isotropic Gaussian integrated exactly over a rotated unit sensor pixel.
Radiance is bilinear on a fixed world grid; lunar occultation splits integration
cells at the observed limb. No radiance is interpolated before fitting data.
"""
from native_forward_common import *
from scipy.special import ndtr
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix,coo_matrix
from numpy.polynomial.legendre import leggauss

class Geometry:
    def __init__(self,refine=16):
        self.box=PLAN['scene_box_xyxy'];x0,y0,x1,y1=self.box;self.shape=(y1-y0+1,x1-x0+1);self.size=int(np.prod(self.shape))
        edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');angles=np.arange(-len(edge)*refine//12,len(edge)*refine//12+1)*2*np.pi/(len(edge)*refine)
        rr=np.interp(angles%(2*np.pi),np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi);self.ex=CX+rr*np.cos(angles);self.ey=CY+rr*np.sin(angles)
        assert np.all(np.diff(self.ey)>0) and self.ey[0]<y0-20 and self.ey[-1]>y1+20
    def border(self,y):return np.interp(y,self.ey,self.ex)

    def quadrature(self,shift=(0.,0.),inside=True,order=4):
        """Positive GL quadrature, split at every boundary segment/cell crossing.
        Each source uses its own translated grid: no unsplit bilinear knots.
        """
        sx,sy=shift;x0,y0,x1,y1=self.box;ny,nx=self.shape;nodes,weights=leggauss(order);nodes=(nodes+1)/2;weights=weights/2
        qx=[];qy=[];qw=[];indices=[];coeff=[]
        for iy in range(ny-1):
            yl=y0+iy+sy;yh=yl+1;ys=self.ey[(self.ey>yl)&(self.ey<yh)];knots0=np.r_[yl,ys,yh];bx=self.border(knots0)
            for ix in range(nx-1):
                xl=x0+ix+sx;xh=xl+1
                if inside and bx.max()<=xl:continue
                if not inside and bx.min()>=xh:continue
                # Fully homogeneous cells need one tensor quadrature only.
                full=(inside and bx.min()>=xh) or (not inside and bx.max()<=xl)
                knots=np.array([yl,yh]) if full else knots0
                if not full:
                    extra=[]
                    for bound in [xl,xh]:
                        cross=(bx[:-1]-bound)*(bx[1:]-bound)<0
                        if cross.any():extra.extend((knots0[:-1][cross]+(bound-bx[:-1][cross])/(bx[1:][cross]-bx[:-1][cross])*np.diff(knots0)[cross]).tolist())
                    if extra:knots=np.sort(np.r_[knots,extra])
                yq=(knots[:-1,None]+np.diff(knots)[:,None]*nodes).ravel();wy=(np.diff(knots)[:,None]*weights).ravel()
                border=np.clip(self.border(yq),xl,xh);left=np.full_like(yq,xl) if inside else border;right=border if inside else np.full_like(yq,xh)
                if full:left[:]=xl;right[:]=xh
                xx=(left[:,None]+(right-left)[:,None]*nodes).ravel();yy=np.repeat(yq,order);ww=(wy[:,None]*(right-left)[:,None]*weights).ravel();ok=ww>1e-18
                xx=xx[ok];yy=yy[ok];ww=ww[ok]
                if not len(ww):continue
                fx=xx-xl;fy=yy-yl;cc=np.stack([(1-fx)*(1-fy),fx*(1-fy),(1-fx)*fy,fx*fy],1);ii=np.tile([iy*nx+ix,iy*nx+ix+1,(iy+1)*nx+ix,(iy+1)*nx+ix+1],(len(ww),1))
                qx.append(xx);qy.append(yy);qw.append(ww);indices.append(ii);coeff.append(cc)
        xx=np.concatenate(qx);yy=np.concatenate(qy);ww=np.concatenate(qw);ii=np.concatenate(indices);cc=np.concatenate(coeff)
        assert ww.min()>0 and cc.min()>-1e-12 and np.max(abs(cc.sum(1)-1))<1e-12
        basis=csr_matrix((cc.ravel(),(np.repeat(np.arange(len(xx)),4),ii.ravel())),shape=(len(xx),self.size))
        return np.stack([xx,yy],1),ww,basis

def response_matrix(points,J,quadrature,sigma=.97,radius=6.5,chunk=200):
    """Rows are actual green pixels; columns are source radiance basis nodes."""
    xy,area,basis=quadrature;tree=cKDTree(xy);inv=np.linalg.inv(J);rows=[]
    assert np.max(abs(J.T@J-np.eye(2)))<1e-10 and abs(np.linalg.det(J)-1)<1e-10
    for start in range(0,len(points),chunk):
        p=points[start:start+chunk];neighbors=tree.query_ball_point(p,radius,workers=1);lens=np.array([len(a) for a in neighbors]);ri=np.repeat(np.arange(len(p)),lens);ci=np.concatenate(neighbors).astype(int);delta=(xy[ci]-p[ri])@inv.T
        kx=ndtr((delta[:,0]+.5)/sigma)-ndtr((delta[:,0]-.5)/sigma);ky=ndtr((delta[:,1]+.5)/sigma)-ndtr((delta[:,1]-.5)/sigma);kw=kx*ky*area[ci]
        mat=csr_matrix((kw,(ri,ci)),shape=(len(p),len(xy)))@basis;mat.eliminate_zeros();rows.append(mat)
    from scipy.sparse import vstack
    result=vstack(rows,format='csr');assert result.data.min()>=0
    return result

def source_rows():
    epochs=json.loads((ROOT/'output/earthshine_optics_20260911/B3_epoch_stationarity.json').read_text())['epochs'];rows=[dict(m,epoch=ep['epoch']) for ep in epochs for m in ep['frames']];wanted=PLAN['train_stems']+PLAN['reserved_stems'];rows=[m for m in rows if m['stem'] in wanted];assert len(rows)==12
    reference=np.mean([m['solar_center_in_lunar_grid'] for m in rows if m['stem'] in PLAN['train_stems']],axis=0)
    for m in rows:
        m['solar_shift']=np.array(m['solar_center_in_lunar_grid'])-reference;m['train']=m['stem'] in PLAN['train_stems']
    return rows,reference

def observed(m):
    from scipy.ndimage import gaussian_filter
    z=np.load(SRC/f'A0_native_samples_{m["stem"]}.npz');x0,y0,x1,y1=PLAN['observations_xyxy'];valid=z['valid']&(z['q']>0)&np.isfinite(z['g'])&np.isfinite(z['variance'])&(z['variance']>0);ok=(z['x']>=x0)&(z['x']<=x1)&(z['y']>=y0)&(z['y']<=y1)&valid
    # Weight variance only: the same4-native-pixel spatial averaging used by
    # the source compositor avoids giving an individual downward noise draw
    # an artificially high precision. Observed radiance itself stays native.
    u=(z['native_x']+z['native_y']-1)//2;v=(z['native_x']-z['native_y']-1)//2;u=u-u.min();v=v-v.min();shape=(v.max()+1,u.max()+1);num=np.zeros(shape);den=np.zeros(shape);num[v[valid],u[valid]]=z['variance'][valid];den[v[valid],u[valid]]=1
    vs=gaussian_filter(num,4/np.sqrt(2))/np.maximum(gaussian_filter(den,4/np.sqrt(2)),1e-30)
    return dict(xy=np.stack([z['x'][ok],z['y'][ok]],1),g=z['g'][ok],variance=z['variance'][ok],weight_variance=vs[v[ok],u[ok]],q=z['q'][ok],J=z['native_to_world'],green_plane=z['green_plane'][ok],raw_relative=z['raw_relative'][ok])
