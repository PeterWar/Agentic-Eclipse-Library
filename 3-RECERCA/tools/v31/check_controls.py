"""Negative rotation controls on the exact rasters selected for V31."""
from pilot_isotropic import *
from audit_geometry import polar,correlate
def main():
    radii=np.linspace(1.12,2.5,60).astype('float32');ref=np.load(CAU/'fusion_total.npy',mmap_mode='r');R=polar(np.log(np.maximum(ref[...,1],1)),CX,CY,RS,radii)
    rep={}
    for tag in SOURCES:
        u=np.load(D/f'cau/{tag}_final_u16.npy',mmap_mode='r');P=polar(u.astype('float32')/65535,CX,CY,RS,radii)
        q={str(deg):correlate(np.roll(P,round(deg*4),axis=1),R) for deg in (0,1,-1,180)}
        assert q['0']['PASS'] and all(not q[str(deg)]['PASS'] for deg in (1,-1,180));rep[tag]=q
    savejson(D/'rotation_controls.json',{'layers':rep,'PASS':True});log('rotation controls PASS')
if __name__=='__main__':main()
