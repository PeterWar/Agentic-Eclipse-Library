"""Strict full-support H1, actual azimuthal alignment, and B donor identity."""
from common import *
from audit_geometry import polar,correlate
import f3

def h1_setup(r,m,nb=200):
    rv=r[m];rmax=float(rv.max());lo=np.log10(20/rmax)
    idx=np.clip(((np.log10(np.maximum(rv,1)/rmax)-lo)/(-lo)*nb).astype(int),0,nb-1)
    order=np.argsort(idx,kind='stable');cuts=np.searchsorted(idx[order],np.arange(nb+1))
    radii=10**(lo+(np.arange(nb)+.5)/nb*(-lo))*rmax/RS
    return order,cuts,radii

def h1(a,m,ctx):
    order,cuts,radii=ctx;v=a[m][order];rows=[]
    for k in range(len(radii)):
        q=v[cuts[k]:cuts[k+1]]
        if len(q)<400:continue
        med=float(np.median(q));rows.append({'R':radii[k],'n':len(q),'median':med,'error':abs(med-.5)})
    worst=max(rows,key=lambda x:x['error'])
    return {'worst':worst,'PASS':worst['error']<=.05,'rings':rows}

def main():
    assert FINAL_GRID
    r,_=coords();m=np.load(CAU/'fusion_support.npy');ctx=h1_setup(r,m)
    ref=np.load(CAU/'fusion_total.npy',mmap_mode='r');radii=np.linspace(1.12,2.5,60).astype(np.float32)
    R=polar(np.log(np.maximum(ref[...,1],1)),CX,CY,RS,radii)
    ctrl={str(d):correlate(np.roll(R,round(d*4),axis=1),R) for d in (0,1,-1,180)}
    rep={'H1':{},'geometry':{},'controls':ctrl,'support':{'pixels':int(m.sum()),'inner_1_05R':int((m&(r<1.05*RS)).sum())}}
    for n in ('achf','passalt24','gran'):
        a=np.load(CAU/f'{n}_u16.npy').astype(np.float32)/65535
        rep['H1'][n]=h1(a,m,ctx)
        rep['geometry'][n]=correlate(polar(a,CX,CY,RS,radii),R)
        rep['H1'][n]['bin_frequency_diagnostic']=f3.anells_de_calaix(a,r,m)
        log(n+' '+str(rep['H1'][n]['worst'])+' geometry '+str(rep['geometry'][n]))
    x,y=map(lambda q:int(round(q)),GHOST_XY);sl=(slice(y-600,y+600),slice(x-600,x+600))
    B=np.load(CAU/'sony_B_total.npy',mmap_mode='r')[sl];S=np.load(CAU/'sony_corrected_total.npy',mmap_mode='r')[sl]
    rep['ghost_donor']={'region':[x-600,y-600,x+600,y+600],'B_exact_all_channels':bool(np.array_equal(B,S)),'max_abs_difference':float(np.max(np.abs(B-S)))}
    rep['PASS']=all(z['PASS'] for z in rep['H1'].values()) and all(z['PASS'] for z in rep['geometry'].values()) and rep['ghost_donor']['B_exact_all_channels'] and ctrl['0']['PASS'] and all(not ctrl[k]['PASS'] for k in ('1','-1','180'))
    savejson(CAU/'raster_qa.json',rep);log('raster QA '+str(rep['PASS']))

if __name__=='__main__':main()
