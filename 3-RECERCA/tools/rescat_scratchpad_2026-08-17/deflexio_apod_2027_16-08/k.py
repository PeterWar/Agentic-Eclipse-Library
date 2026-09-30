import numpy as np
src=open('ecl2027.py').read().split("sites = [")[0]
for k,lbl in [(1737.4,'k=0.2725076 (mean radius, my default)'),(1736.0,'k=0.272281 (Espenak umbral convention)')]:
    ns={}
    exec(src.replace('R_MOON_KM = 1737.4','R_MOON_KM = %.1f'%k), ns)
    c=ns['circumstances']
    # greatest eclipse search near 25.5N 33.2E
    best=(0,None)
    for la in np.arange(25.0,26.8,0.2):
        for lo in np.arange(31.5,34.5,0.5):
            r=c(la,lo,0.0)
            if r['dur_s']>best[0]: best=(r['dur_s'],(la,lo))
    print(f"{lbl}: max duration found {best[0]:.1f} s = {int(best[0]//60)}m{best[0]%60:04.1f}s at {best[1]}")
