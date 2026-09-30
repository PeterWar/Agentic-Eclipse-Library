import rawpy, numpy as np, glob, subprocess, os, sys
D='/Users/USUARI/Desktop/Eclipse 2026/Darks Canon R6III Eclipse/'
out=subprocess.run(['exiftool','-q','-n','-T','-FileName','-ExposureTime','-CameraTemperature']+sorted(glob.glob(D+'*.CR3')),capture_output=True,text=True).stdout
rows=[l.split('\t') for l in out.strip().split('\n')]
for exp in ['10','2','1']:
    fs=[r[0] for r in rows if r[1]==exp]
    print(exp,'n=',len(fs))
    stack=[]
    for f in fs:
        r=rawpy.imread(D+f); stack.append(r.raw_image_visible.astype(np.float32)); r.close()
    st=np.stack(stack); del stack
    med=np.median(st,axis=0)
    np.save(f'dark_med_{exp}.npy',med.astype(np.float32))
    print('  median-of-medians pedestal', np.median(med), 'p1',np.percentile(med,1),'p99',np.percentile(med,99),'max',med.max())
    del st, med
