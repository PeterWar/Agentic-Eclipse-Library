"""Photographic multiplicative edge grading, explicitly requested by Pere.
No blur, registration, radial profile fit, texture synthesis or RAW changes.
Only the gray lunar layer is graded; the09 RGB contribution stays identical.
"""
from comu46 import *

def field(width,strength):
    edge=np.load(CAU44/'vixen_optical_edge.npy');phi=PHI%(2*np.pi)
    limit=np.interp(phi*len(edge)/(2*np.pi),np.arange(len(edge)),edge,period=len(edge))
    distance=limit-R
    t=np.clip((width-distance)/width,0,1);s=t**3*(10+t*(-15+6*t))
    return np.exp(-strength*s),distance

def main():
    claim46();base=np.load(CAU44/'pere09_rgb.npy').astype(float)/65535
    old=np.load(CAU45/'combined_reference_display_u16.npy').astype(float)/65535
    w=np.load(CAU45/'combined_reference_mask_u16.npy').astype(float)/65535
    before=base*(1-w[...,None])+old*w[...,None]
    rows=[]
    for key,width,strength in [('a',24.,1.8),('b',36.,1.8),('c',48.,1.8),('d',36.,2.2)]:
        gain,d=field(width,strength);new=old*gain[...,None];after=base*(1-w[...,None])+new*w[...,None]
        png46('A1_'+key+'_lluna_1a1.png',after)
        # Fixed top/right/west locations. Diagnostic magnification only.
        for name,(x,y),half in [('dalt',(596,247),60),('dreta',(1088,912),70),('oest',(247,700),75)]:
            sl=np.s_[y-half:y+half,x-half:x+half];row=np.concatenate([before[sl],after[sl]],1)
            png46('A1_'+key+'_'+name+'_x3.png',cv2.resize(row,None,fx=3,fy=3,interpolation=cv2.INTER_NEAREST))
        rows.append(dict(key=key,width_px=width,strength=strength,edge_gain=float(np.exp(-strength)),inner_exact=bool(np.array_equal(new[d>=width],old[d>=width])),outside_join_exact=bool(np.array_equal(after[w==0],before[w==0])),chromatic_signal_max_error=float(abs((after[...,0]-after[...,1])-(before[...,0]-before[...,1])).max()),median_before_at_edge=float(np.median(before[...,1][(d>-1)&(d<1)&(w>.2)])),median_after_at_edge=float(np.median(after[...,1][(d>-1)&(d<1)&(w>.2)]))))
    savejson(REB46/'A1_variants.json',dict(variants=rows,scope='photographic local tone; fractional lunar contrast preserved mathematically before quantization; no new scientific texture recovery claimed'))
    print(rows,flush=True)
if __name__=='__main__':main()
