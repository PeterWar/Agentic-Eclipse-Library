import numpy as np, rawpy, pandas as pd, pickle
D='/Users/USUARI/Desktop/Eclipse 2026/300mm/'
tab=pd.read_csv('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/xmatch/final_match_sony.csv')
off=pickle.load(open('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony_stars/offsets6.pkl','rb'))['off']
for name,e in (('DSC06993',8.0),('DSC06987',8.0)):
    with rawpy.imread(D+name+'.ARW') as r:
        raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
        wl=r.white_level
    green=(col==1)|(col==3)
    dx,dy=off[name]
    print(f'=== {name} exp={e}s white_level={wl} raw max global={raw.max():.0f} ===')
    print(f'   pixels >= 15000 al fotograma: {(raw>=15000).sum()}  (>=16000: {(raw>=16000).sum()})')
    rows=[]
    for i in range(len(tab)):
        x=tab.x.values[i]+dx; y=tab.y.values[i]+dy
        xi,yi=int(round(x)),int(round(y))
        if not(30<xi<raw.shape[1]-30 and 30<yi<raw.shape[0]-30): continue
        st=raw[yi-6:yi+7,xi-6:xi+7]; gm=green[yi-6:yi+7,xi-6:xi+7]
        rows.append((tab.det.values[i],tab.V.values[i],st[gm].max(),st.max(),np.median(raw[yi-40:yi+41,xi-40:xi+41])))
    rows.sort(key=lambda r:-r[2])
    print(f'   {"det":6s} {"V":>5s} {"pic_verd":>9s} {"pic_qualsevol":>13s} {"fons_local":>10s} {"marge_a_sat":>11s}')
    for d,V,pg,pa,bg in rows[:8]:
        print(f'   {d:6s} {V:5.2f} {pg:9.0f} {pa:13.0f} {bg:10.0f} {wl-pg:11.0f}')
