import rawpy, numpy as np
D="/Users/USUARI/Desktop/Eclipse 2026/Darks Canon R6III Eclipse/"
for n in ["572A3444","572A4030"]:
    with rawpy.imread(D+n+".CR3") as r:
        full=r.raw_image.astype(np.float64)
        sizes=(r.sizes.raw_height,r.sizes.raw_width,r.sizes.top_margin,r.sizes.left_margin,r.sizes.height,r.sizes.width)
    print("===",n,"sizes(raw_h,raw_w,top,left,h,w)=",sizes)
    rp=full.mean(axis=1)
    print(" row profile 0..20:", np.round(rp[:21],1))
    bad=np.where(rp>514)[0]
    print(" rows mean>514 :",bad[:60], "n=",len(bad))
    print(" their values  :", np.round(rp[bad][:60],1))
    # column profile restricted to top margin and to image area
    cp=full[:,:].mean(axis=0)
    print(" col profile: min %.2f max %.2f ; first 10 %s ; last 5 %s"%(cp.min(),cp.max(),np.round(cp[:10],1),np.round(cp[-5:],1)))
    badc=np.where(cp>514)[0]
    print(" cols mean>514: n=",len(badc), badc[:30])
    # how much of the full std comes from rows 0-107 (top margin)?
    tm=full[:108]; rest=full[108:]
    print(" topmargin(0:108) mean %.2f std %.2f | rest mean %.4f std %.4f"%(tm.mean(),tm.std(),rest.mean(),rest.std()))
    # variance decomposition on the strided sample
    s=full[::4,::4]
    print(" strided total std %.4f ; strided rows>=108 std %.4f ; strided rows<108 std %.4f"%(s.std(), full[108::4,::4].std() if False else s[27:].std(), s[:27].std()))
