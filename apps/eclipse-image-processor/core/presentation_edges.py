"""Display-only black fill and edge antialiasing; never used as filter input."""
import numpy as np
from scipy.ndimage import distance_transform_edt, label
from .cancellation import check_cancelled

EDGE_WIDTH_NATIVE_PX = 2.


def black_edge_alpha(source, valid=None, scale=1., geometry=None):
    """Black-overlay alpha16; attenuate only the observed side of missing boundaries.

    A smoothstep over two native pixels starts half a target pixel outside the
    missing support. Fast previews use at least one target pixel. No missing
    radiance is inferred and no observed pixel is blurred with its neighbours.
    An observed, connected exactly-black lunar disk is protected as well; this
    is display support only and does not change the original validity mask.
    """
    a=np.asarray(source)
    if a.ndim!=2 or not a.size or not np.isfinite(scale) or scale<=0:
        raise ValueError('Edge antialiasing requires a 2D source and positive finite scale')
    support=np.isfinite(a)
    if valid is not None:
        if np.shape(valid)!=a.shape:
            raise ValueError('Edge validity must match source')
        support &= np.asarray(valid,bool)
    if geometry is not None and all(key in geometry for key in ('sx','sy','sr')):
        cx,cy,radius=(float(geometry[key]) for key in ('sx','sy','sr'))
        if np.isfinite([cx,cy,radius]).all() and radius>0:
            y0,y1=max(0,int(np.floor(cy-1.5*radius))),min(a.shape[0],int(np.ceil(cy+1.5*radius))+1)
            x0,x1=max(0,int(np.floor(cx-1.5*radius))),min(a.shape[1],int(np.ceil(cx+1.5*radius))+1)
            if y1>y0 and x1>x0:
                y,x=np.ogrid[y0:y1,x0:x1]
                black=((a[y0:y1,x0:x1]==0) | ~support[y0:y1,x0:x1]) & (np.hypot(x-cx,y-cy)<=1.5*radius)
                iy,ix=int(np.clip(round(cy)-y0,0,y1-y0-1)),int(np.clip(round(cx)-x0,0,x1-x0-1))
                if black[iy,ix]:
                    components,_=label(black)
                    disk=components==components[iy,ix]
                    # A uniformly black field is not an isolated lunar disk.
                    if 4<=disk.sum()<=1.8*np.pi*radius**2:
                        support[y0:y1,x0:x1] &= ~disk
    if support.all():
        return None
    check_cancelled()
    distance=distance_transform_edt(support)
    width=max(1.,EDGE_WIDTH_NATIVE_PX*float(scale))
    t=np.clip((distance-.5)/width,0,1)
    coverage=t*t*(3-2*t)
    check_cancelled()
    alpha=np.rint((1-coverage)*65535).astype(np.uint16)
    alpha.setflags(write=False)
    return alpha


def finish_presentation(image, alpha):
    """Opaque black for nonfinite display samples, plus the same PSB Normal overlay."""
    result=np.nan_to_num(image,nan=0.,posinf=0.,neginf=0.)
    if alpha is not None:
        coverage=1-alpha.astype(float)/65535
        result=result*(coverage[...,None] if result.ndim==3 else coverage)
    return result
