"""Positive bilinear interpolation on the complete green CFA lattice.
Origin(1,0), basis(1,1),(1,-1):u=(x+y-1)/2,v=(x-y-1)/2.
Unlike averaging two interpolated green planes, native green samples are fixed
points of this interpolator. Confidence never changes radiance coefficients.
"""
import numpy as np
from scipy.ndimage import maximum_filter

def interpolate(values,quality,variance,bad,u,v,u0,v0):
    mx=np.asarray(u,dtype=float)-u0;my=np.asarray(v,dtype=float)-v0;ix=np.floor(mx).astype(int);iy=np.floor(my).astype(int)
    inside=(ix>=0)&(iy>=0)&(ix+1<values.shape[1])&(iy+1<values.shape[0]);sx=np.clip(ix,0,values.shape[1]-2);sy=np.clip(iy,0,values.shape[0]-2)
    fu=mx-ix;fv=my-iy;g=np.zeros_like(mx);q=g.copy();var=g.copy();lo=np.full_like(g,np.inf);hi=-lo
    for dy,dx,b in [(0,0,(1-fu)*(1-fv)),(0,1,fu*(1-fv)),(1,0,(1-fu)*fv),(1,1,fu*fv)]:
        val=values[sy+dy,sx+dx];g+=b*val;q+=b*quality[sy+dy,sx+dx];var+=b*b*variance[sy+dy,sx+dx];lo=np.minimum(lo,val);hi=np.maximum(hi,val)
    invalid=bad[:-1,:-1]|bad[1:,:-1]|bad[:-1,1:]|bad[1:,1:];strict=inside&~invalid[sy,sx]
    # Same2 native-pixel taper radius as the old2px-spaced green-plane grid.
    # Each new lattice axis step has length sqrt(2) native pixels.
    near=maximum_filter(invalid,size=7,mode='constant',cval=1)[sy,sx]&strict;distance=np.ones_like(g);d=np.ones(int(near.sum()));px=mx[near];py=my[near];x0=ix[near];y0=iy[near]
    for di in range(-3,4):
        for dj in range(-3,4):
            xi=x0+dj;yi=y0+di;ok=(xi>=0)&(yi>=0)&(xi<invalid.shape[1])&(yi<invalid.shape[0]);bc=~ok|invalid[np.clip(yi,0,invalid.shape[0]-1),np.clip(xi,0,invalid.shape[1]-1)]
            dx=np.maximum(np.maximum(xi-px,px-xi-1),0);dy=np.maximum(np.maximum(yi-py,py-yi-1),0);d=np.minimum(d,np.where(bc,np.hypot(dx,dy)/np.sqrt(2),1))
    distance[near]=d;distance[~strict]=0;taper=distance*distance*(3-2*distance);q*=strict*taper
    good=q>0;assert not np.any(good&~strict)
    assert np.all(g[good]>=lo[good]-1e-8) and np.all(g[good]<=hi[good]+1e-8)
    return dict(g=np.where(good,g,np.nan),q=q,variance=np.where(good,var,np.nan)),dict(valid=int(good.sum()),near_invalid=int(near.sum()),convex_range_PASS=True,strict_four_sample_validity_PASS=True,taper_radius_native_pixels=2.)

def elementary_checks():
    v,u=np.mgrid[:40,:40];value=(1+u+v)+2*(u-v)+10.;rng=np.random.default_rng(114912);x=rng.uniform(4,34,1000);y=rng.uniform(4,34,1000)
    q=np.ones_like(value);var=q*3.;bad=np.zeros_like(value,dtype=bool)
    a,_=interpolate(value,q,var,bad,x,y,0,0);expected=(1+x+y)+2*(x-y)+10
    linear_error=float(np.max(abs(a['g']-expected)));assert linear_error<1e-12
    xx=np.array([10.,12.,20.]);yy=np.array([11.,20.,15.]);a,_=interpolate(value,q,var,bad,xx,yy,0,0)
    assert np.array_equal(a['g'],value[yy.astype(int),xx.astype(int)]) and np.array_equal(a['variance'],np.full(3,3.))
    bad[10,10]=True;a,_=interpolate(value,q,var,bad,np.array([10.2]),np.array([10.3]),0,0);assert a['q'][0]==0
    return dict(affine_reproduction_max_error=linear_error,native_green_values_exact=True,native_green_variance_exact=True,invalid_contributor_rejected=True)
