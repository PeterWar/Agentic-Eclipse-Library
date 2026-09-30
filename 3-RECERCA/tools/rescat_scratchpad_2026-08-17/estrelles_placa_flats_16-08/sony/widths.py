import numpy as np, sys
sys.path.insert(0,"/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony")
from common import SCALE

def cross_from_peak(ctr,prof,level,side):
    """find where prof crosses `level`, searching from d=0 outward/inward"""
    i0=int(np.argmin(np.abs(ctr)))
    step=-1 if side=='in' else 1
    i=i0
    while 0<i<len(ctr)-1:
        a,b=prof[i],prof[i+step]
        if not np.isfinite(b): return np.nan
        if (a-level)*(b-level)<=0:
            if b==a: return ctr[i]
            return ctr[i]+(level-a)*(ctr[i+step]-ctr[i])/(b-a)
        i+=step
    return np.nan

def widths(ctr,prof):
    o={}
    d50i=cross_from_peak(ctr,prof,0.5,'in')
    o['d50']=d50i
    for L in [0.1,0.25,0.05]:
        o['in_%g'%L]=cross_from_peak(ctr,prof,L,'in')
    for L in [0.75,0.9,0.95]:
        o['out_%g'%L]=cross_from_peak(ctr,prof,L,'out')
    # equivalent FWHM assuming symmetry: 2*(d50 - d10_in) * 0.919 for gaussian 10-90 relation
    return o
