"""Measure detail against a fixed, unsmoothed second telescope at Vixen-dominated radii."""
from pilot_isotropic import *
n=256;yy,xx=np.mgrid[:n,:n];x=xx-(n-1)/2;y=yy-(n-1)/2
window=np.hanning(n)[:,None]*np.hanning(n)[None,:];freq=np.fft.fftfreq(n);fr=np.hypot(freq[:,None],freq[None,:])
bands={f'{lo}-{hi}':(fr>=1/hi)&(fr<1/lo) for lo,hi in [(4,8),(8,16),(16,32),(32,64),(64,128)]}
def fft(a):
    a=np.asarray(a,dtype='float64');a=a-a.mean()-x*np.sum(a*x)/np.sum(x*x)-y*np.sum(a*y)/np.sum(y*y)
    return np.fft.fft2(a*window)
def main():
    sony=np.load(CAU/'sony_B_total.npy',mmap_mode='r');rep={'method':'lnG SonyB FIXED unsmoothed; four256px windows at1.6R; remove plane, Hann2D, FFT2; per-window correlation and crosspower ratios then median','reference':str(CAU/'sony_B_total.npy'),'scope':'Vixen-dominated inner corona, not independent truth for every pixel of a fused image; outer micrograin not corroborated','layers':{}}
    for tag,p in SOURCES.items():
        old=np.load(p,mmap_mode='r');new=np.load(D/f'cau/{tag}_final_u16.npy',mmap_mode='r');rows=[]
        for name,px,py in [('NE',5603,3113),('W',4723,3478),('E',6056,3653),('S',5239,4470)]:
            sl=(slice(py-128,py+128),slice(px-128,px+128));g=sony[sl][...,1];assert np.all(np.isfinite(g)&(g>0))
            J=fft(np.log(g));A=fft(old[sl]/65535-.5);B=fft(new[sl]/65535-.5);q={}
            for band,m in bands.items():
                j,a,b=J[m],A[m],B[m];pj,pa,pb=[np.vdot(z,z).real for z in (j,a,b)];ca=np.vdot(j,a).real;cb=np.vdot(j,b).real
                q[band]={'r_old':float(ca/np.sqrt(pj*pa)),'r_new':float(cb/np.sqrt(pj*pb)),'RMS_new_over_old':float(np.sqrt(pb/pa)),'coherent_gain':float(cb/ca)}
            rows.append({'name':name,'center':[px,py],'bands':q})
        rep['layers'][tag]={'rows':rows,'median':{b:{k:float(np.median([q['bands'][b][k] for q in rows])) for k in rows[0]['bands'][b]} for b in bands}}
    savejson(D/'fixed_judge.json',rep);log('fixed Sony judge saved')
if __name__=='__main__':main()
