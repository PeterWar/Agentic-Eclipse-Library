import numpy as np, lib, stack2, fitmodel, esf

LONG = ["572A2999.CR3", "572A2987.CR3", "572A3005.CR3", "572A2998.CR3",
        "572A3004.CR3", "572A2992.CR3", "572A2974.CR3", "572A2993.CR3",
        "572A3000.CR3", "572A2988.CR3", "572A2991.CR3", "572A2973.CR3"]
SHORT = ["572A3009.CR3", "572A3010.CR3", "572A3011.CR3", "572A3012.CR3",
         "572A3013.CR3", "572A3014.CR3", "572A3015.CR3", "572A3016.CR3",
         "572A3017.CR3", "572A3018.CR3", "572A2962.CR3", "572A2963.CR3",
         "572A2964.CR3", "572A2965.CR3", "572A2966.CR3"]
TH_MAJ = np.radians(157.0)
SELS = {
    'tots els azimuts': None,
    'eix curt (perp.)': lambda x: abs(np.cos(x['th']-TH_MAJ)) < 0.30,
    'eix llarg (vert.)': lambda x: abs(np.cos(x['th']-TH_MAJ)) > 0.92,
}

def block(names, tag, snr=12):
    cache = {}
    for n in names:
        img = lib.load(n)
        cache[n] = (img, lib.solve_geometry(img)[:3])
    for key in ('R', 'G1', 'G2', 'B'):
        for sl, sel in SELS.items():
            bs = [stack2.accumulate(*cache[n], key, sel=sel, snr_min=snr) for n in names]
            med, cnt = stack2.merge(bs)
            p, rms = fitmodel.fit(stack2.cent, med, 14.0)
            fw, hi, ho = fitmodel.fwhm_of(p)
            print("%-12s %3s  %-18s  FWHM=%.3f px = %5.2f\"   (dins %.2f\" / fora %.2f\")  rms=%.4f" %
                  (tag, key, sl, fw, fw*lib.SCALE, hi*lib.SCALE, ho*lib.SCALE, rms))
        # error per fotograma
        fws = []
        for n in names:
            med, cnt = stack2.merge([stack2.accumulate(*cache[n], key, snr_min=snr)])
            try:
                p, _ = fitmodel.fit(stack2.cent, med, 14.0)
                fws.append(fitmodel.fwhm_of(p)[0]*lib.SCALE)
            except Exception:
                pass
        fws = np.array(fws)
        print("             %3s  fotograma a fotograma: %.2f\" +- %.2f (sd), error de la mitjana %.2f\", n=%d, rang %.2f-%.2f" %
              (key, fws.mean(), fws.std(ddof=1), fws.std(ddof=1)/np.sqrt(len(fws)), len(fws), fws.min(), fws.max()))
    print()

block(LONG, "1/1000-1/30")
block(SHORT, "1/3200", snr=8)
