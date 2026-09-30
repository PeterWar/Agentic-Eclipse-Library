from filters58 import *
claim();rr=np.arange(1.1*RS,2.0*RS,.25);th=np.arange(1440)*2*np.pi/1440;mx=CX+rr[:,None]*np.cos(th);my=CY+rr[:,None]*np.sin(th);rep={}
def stats(p):
 # Only a measurement: radial mean high-pass and its discrete Fourier power. No image correction.
 v=np.mean(p,axis=1);v=v-gaussian_filter1d(v,64);fr=np.fft.rfftfreq(len(v),.25);ps=np.abs(np.fft.rfft(v*np.hanning(len(v))))**2;near=np.abs(fr-1/8)<.008;bg=((fr>.085)&(fr<.17))&~near;return dict(power8=float(ps[near].sum()),power8_over_adjacent_mean=float(ps[near].mean()/np.mean(ps[bg])),radial_rms=float(np.std(v)))
for idx,tag in [(15,'P02c_RHEF_local60_native'),(16,'P02d_RHEF_local30_native')]:
 old=map_coordinates(roi(idx).astype('float32')/65535,[my-ROI[1],mx-ROI[0]],order=1);a=np.load(O/'filters'/f'{tag}_u16.npy',mmap_mode='r');new=map_coordinates(a.astype('float32')/65535,[my,mx],order=1);rep[tag]=dict(old=stats(old),new=stats(new));print(tag,rep[tag],flush=True)
for tag,path in [('independent_sony',V42/'cau/sony_corrected_total_v42.npy'),('vixen',R/'research/tools/v38_20260908/cau/vixen_total_v38.npy')]:
 a=np.load(path,mmap_mode='r')[...,1];p=map_coordinates(np.log(np.maximum(a,1e-8)),[my,mx],order=1);rep[tag]=stats(p);print(tag,rep[tag],flush=True)
save('C5_real_period8.json',rep)
