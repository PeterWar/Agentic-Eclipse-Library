import numpy as np, lib, esf, stack2, fitmodel, subprocess, json, os

D = lib.D
# t=0 a C2 (20:28:45,1 rellotge de la camera)
T0 = 45.1


def secs(name):
    o = subprocess.run(["exiftool", "-T", "-DateTimeOriginal", "-SubSecTimeOriginal", D+name],
                       capture_output=True, text=True).stdout.strip().split("\t")
    hh, mm, ss = o[0].split()[1].split(":")
    return (int(hh)*3600+int(mm)*60+int(ss)) + int(o[1])/100.0


NAMES = (["572A%04d.CR3" % i for i in range(2958, 2967)] +
         ["572A2967.CR3", "572A2973.CR3", "572A2968.CR3", "572A2974.CR3", "572A2969.CR3",
          "572A2975.CR3", "572A2985.CR3", "572A2991.CR3", "572A2986.CR3", "572A2992.CR3",
          "572A2987.CR3", "572A2993.CR3", "572A2988.CR3", "572A2997.CR3", "572A2998.CR3",
          "572A2999.CR3", "572A3000.CR3", "572A3003.CR3", "572A3004.CR3", "572A3005.CR3",
          "572A3006.CR3"] +
         ["572A%04d.CR3" % i for i in range(3009, 3025)])
base = secs("572A2958.CR3")
out = []
for n in sorted(set(NAMES)):
    try:
        img = lib.load(n)
        g = lib.solve_geometry(img)[:3]
        med, _ = stack2.merge([stack2.accumulate(img, g, 'G1', snr_min=9)])
        p, rms = fitmodel.fit(stack2.cent, med, 14.0)
        fw = fitmodel.fwhm_of(p)[0]*lib.SCALE
        t = secs(n) - (20*3600+28*60+T0)
        out.append((n, t, fw, rms, g[0], g[1]))
        print("%s  t(C2)=%+7.2f s  FWHM_G=%5.2f\"  rms=%.4f  centre=(%.1f,%.1f)" %
              (n, t, fw, rms, g[0], g[1]), flush=True)
    except Exception as e:
        print(n, "fallit", e, flush=True)
json.dump(out, open("serie.json", "w"))
a = np.array([[r[1], r[2]] for r in out if r[3] < 0.02])
print("\nresum (rms<0,02): n=%d  mediana=%.2f\"  mitjana=%.2f\"  sd=%.2f\"  min=%.2f  max=%.2f" %
      (len(a), np.median(a[:, 1]), a[:, 1].mean(), a[:, 1].std(ddof=1), a[:, 1].min(), a[:, 1].max()))
