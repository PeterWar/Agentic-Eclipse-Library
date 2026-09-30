"""Feather real pointing overlap, with a low-frequency relative calibration.

The fit compares the same sky pixels in A and B. It cannot borrow texture
from a neighbouring location. All transformations and residuals are saved.
"""
from common import *
def design(x,y):return np.stack([np.ones_like(x),x,y,x*x,x*y,y*y],axis=-1)

def main():
    A=np.load(CAU/'sony_A_total.npy',mmap_mode='r');B=np.load(CAU/'sony_B_total.npy',mmap_mode='r')
    pa=np.load(CAU/'sony_A_weights.npy',mmap_mode='r');pb=np.load(CAU/'sony_B_weights.npy',mmap_mode='r')
    ma=np.all(np.isfinite(A)&(A>0)&(pa>0),axis=2);mb=np.all(np.isfinite(B)&(B>0)&(pb>0),axis=2)
    r,t=coords(); y,x=np.ogrid[:H,:W];gx=(x-W/2)/4000;gy=(y-H/2)/4000
    da=cv2.distanceTransform((ma|(r<1.2*RS)).astype(np.uint8),cv2.DIST_L2,5)
    db=cv2.distanceTransform((mb|(r<1.2*RS)).astype(np.uint8),cv2.DIST_L2,5)
    wa=pa[...,1]*smooth(da,0,160)*ma;wb=pb[...,1]*smooth(db,0,160)*mb
    # Exclude known contaminated first-pointing ghost from blend, using B at
    # those same coordinates. Vixen is not used in this correction.
    dist=np.hypot(x-GHOST_XY[0],y-GHOST_XY[1]);g=1-smooth(dist,140,200);wa*=1-g
    den=wa+wb;weight=wa/np.maximum(den,1e-20)
    # At an isolated footprint pixel retain the only valid observation.
    weight=np.where(ma&~mb,1,np.where(mb&~ma,0,weight)).astype(np.float32)
    # B is the uncontaminated reference throughout its observed interior.
    # A contributes only at the physical B footprint edge or beyond it.
    # This eliminates a local donor disc and its residual photometric ring.
    weight=np.where(mb,(1-smooth(db,0,384))*ma,ma).astype(np.float32)
    np.save(CAU/'sony_A_blend_weight.npy',weight)
    out=np.lib.format.open_memmap(CAU/'sony_corrected_total.npy',mode='w+',dtype=np.float32,shape=(H,W,3))
    rep={'model':'log(B/A), robust degree-2 Cartesian polynomial, same-sky block medians','feather_px':384,'ghost':'B primary across its entire observed interior; A only in physical B footprint overlap or beyond it; no local ghost-shaped source switch','channels':{}}
    boxes=[];overlap=ma&mb
    for yy in range(0,H-128,128):
        for xx in range(0,W-128,128):
            sl=(slice(yy,yy+128,4),slice(xx,xx+128,4));good=overlap[sl]&(r[sl]>2*RS)&(r[sl]<10*RS)&(dist[sl]>250)&(da[sl]>60)&(db[sl]>60)
            if good.mean()>.8:boxes.append((sl,good,(xx+64-W/2)/4000,(yy+64-H/2)/4000))
    D=design(np.array([b[2] for b in boxes]),np.array([b[3] for b in boxes]))
    for c in range(3):
        q=np.array([np.median(np.log(B[sl+(c,)][good]/A[sl+(c,)][good])) for sl,good,_,_ in boxes])
        use=np.isfinite(q)
        for _ in range(4):
            coef=np.linalg.lstsq(D[use],q[use],rcond=None)[0];res=q-D@coef;mad=max(1.4826*np.median(np.abs(res[use]-np.median(res[use]))),1e-5);use=np.isfinite(q)&(np.abs(res)<4*mad)
        pred=coef[0]+coef[1]*gx+coef[2]*gy+coef[3]*gx*gx+coef[4]*gx*gy+coef[5]*gy*gy
        factor=np.exp(pred).astype(np.float32)
        # Local residual of the same-sky ratio removes the donor boundary
        # left by a global polynomial. Exclude the contaminated disc before
        # estimating the ratio; common injected texture cancels in B/A.
        ratio=np.where(overlap&(dist>220)&(A[...,c]>0),np.log(np.maximum(B[...,c],1e-8)/np.maximum(A[...,c],1e-8))-pred,0).astype(np.float32)
        ratio=np.nan_to_num(ratio,nan=0,posinf=0,neginf=0)
        ok=(overlap&(dist>220)).astype(np.float32)
        small=(W//8,H//8);wr=cv2.resize(ok,small,interpolation=cv2.INTER_AREA)
        nr=cv2.resize(ratio*ok,small,interpolation=cv2.INTER_AREA)
        low=gauss(nr,16)/np.maximum(gauss(wr,16),1e-6)
        local=cv2.resize(low,(W,H),interpolation=cv2.INTER_LINEAR)
        factor*=np.exp(local)
        aa=np.nan_to_num(A[...,c],nan=0)*factor;bb=np.nan_to_num(B[...,c],nan=0)
        out[...,c]=aa*weight+bb*(1-weight)
        np.save(CAU/f'sony_A_relative_factor_{c}.npy',factor)
        rep['channels'][str(c)]={'coefficients':coef,'local_ratio_sigma_px':128,'ghost_exclusion_radius':220,'blocks':len(q),'used':int(use.sum()),'factor_p1_p50_p99':np.percentile(factor[ma],[1,50,99]),'log_ratio_residual_p5_p50_p95':np.percentile(res[use],[5,50,95]),'raw_log_ratio_p5_p50_p95':np.percentile(q[use],[5,50,95])}
        log(str(rep['channels'][str(c)]))
    out.flush(); savejson(CAU/'pointing_merge_receipt.json',rep);log('pointings merged')

if __name__=='__main__':main()
