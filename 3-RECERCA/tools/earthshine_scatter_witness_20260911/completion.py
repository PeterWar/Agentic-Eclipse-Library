"""Auxiliary exposure completion for wide optical predictors only."""
from scatter_common import *
import cv2
from scipy.ndimage import gaussian_filter
source=np.load(OUT/'D0_completion_sources.npz');frames={r['stem']:r for r in json.loads((OUT/'D0_completion_sources.json').read_text())['frames']};yy,xx=np.mgrid[:N,:N].astype(np.float32);r=np.hypot(xx-CX,yy-CY);distance=source['source_lunar_distance'];p=json.loads((OUT/'B1_physical_mixture.json').read_text())['p'];a=p/(1-p);coeff=np.array([a,-a*a,a**3,-a**4])
# Pixel-area approximation used only inside an auxiliary broad-light model.
P=np.clip(.5-distance,0,1);mv=np.isfinite(source['lunar']);cv=np.isfinite(source['solar']);M=np.nan_to_num(source['lunar']);C=np.nan_to_num(source['solar'])
def auxiliary(stem):
    center=frames[stem]['solar_center'];mx=xx-np.float32(center[0]-CX);my=yy-np.float32(center[1]-CY);solar=cv2.remap(C.astype(np.float32),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);valid=cv2.remap(cv.astype(np.float32),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);valid=(valid>=1-1e-6).astype(float)
    cover=P*mv+(1-P)*valid;F=P*M+(1-P)*solar*valid;dc=gaussian_filter(cover,.97,truncate=5);core=gaussian_filter(F,.97,truncate=5)/np.maximum(dc,1e-30);db=gaussian_filter(dc,12,truncate=5);wide=gaussian_filter(core*dc,12,truncate=5)/np.maximum(db,1e-30);Y=(1-p)*core+p*wide;quality=(1-p)*dc+p*db
    return Y,quality>=.995
def broad_correction(g,valid):
    value=np.where(valid,g,0);result=np.zeros_like(g,dtype=float);support=np.ones_like(g,dtype=float)
    for k,c in enumerate(coeff,1):
        sigma=12*np.sqrt(k);den=gaussian_filter(valid.astype(float),sigma,truncate=5);blur=gaussian_filter(value.astype(float),sigma,truncate=5)/np.maximum(den,1e-30);result+=c*blur;support=np.minimum(support,den)
    return result/(1-p),support
