import numpy as np, lib, esf, stack2

NAMES_LONG = ["572A2999.CR3", "572A2987.CR3", "572A3005.CR3", "572A2998.CR3",
              "572A3004.CR3", "572A2992.CR3", "572A2974.CR3", "572A2993.CR3",
              "572A3000.CR3", "572A2988.CR3", "572A2991.CR3", "572A2973.CR3"]
NAMES_SHORT = ["572A3009.CR3", "572A3010.CR3", "572A3011.CR3", "572A3012.CR3",
               "572A3013.CR3", "572A3014.CR3", "572A3015.CR3", "572A3016.CR3",
               "572A3017.CR3", "572A3018.CR3", "572A2962.CR3", "572A2963.CR3",
               "572A2964.CR3", "572A2965.CR3", "572A2966.CR3"]

PROM = [np.radians(a) if a < 180 else np.radians(a-360) for a in (47.5, 77.5, 261.5)]
WID = np.radians(7.0)


def is_prom(x):
    return any(abs(np.angle(np.exp(1j*(x['th']-p)))) < WID for p in PROM)


def is_quiet(x):
    return not any(abs(np.angle(np.exp(1j*(x['th']-p)))) < np.radians(18) for p in PROM)


def run(names, tag):
    cache = {}
    for n in names:
        img = lib.load(n)
        cache[n] = (img, lib.solve_geometry(img)[:3])
    for key in ('R', 'G1', 'B'):
        for lab, sel in (('protuberancies', is_prom), ('corona tranquilla', is_quiet)):
            bs = [stack2.accumulate(*cache[n], key, sel=sel, snr_min=10) for n in names]
            med, cnt = stack2.merge(bs)
            try:
                x, d, pk, l, r = stack2.lsf(med)
                print("%-9s %3s %-18s FWHM=%.3f px = %.2f\"  (dins %.2f\" / fora %.2f\")  npix=%d" %
                      (tag, key, lab, r-l, (r-l)*lib.SCALE, (pk-l)*lib.SCALE, (r-pk)*lib.SCALE,
                       cnt[len(cnt)//2]))
            except Exception as e:
                print(tag, key, lab, "fallit", e)
    print()


run(NAMES_LONG, "1/1000-1/30")
run(NAMES_SHORT, "1/3200")
