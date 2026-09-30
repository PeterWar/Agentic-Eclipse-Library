"""s16 · LA REIXA DE FILES DEL SENSOR DE LA SONY al llenç: al sensor hi ha un patró de files amb període 6,00 subplans (12 files RAW; el
flat el té ×1.267 per sobre de la mediana de l'espectre, i les llums dels dos apuntaments també). Al llenç és una reixa de línies paral·leles
a les files (A: 136,3°; B: +0,135°) amb període 6 × 2 × 1,49 = 17,9 px. Aquí es mesura, a cada producte, la potència de l'espectre de la
projecció al llarg de les files (finestra de 2.400 × 2.400 px a 4–8 R☉ dalt-esquerra, on hi ha A i B), al període esperat i als veïns.
Ús: s16_reixa_files.py [variant=carpeta_apilats ...]. Sortida: S16_REIXA_FILES.json."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
ANG = np.radians(136.3); d = np.array([np.cos(ANG), np.sin(ANG)]); n = np.array([-d[1], d[0]])
C0 = np.array([SOL[0] - 1500.0, SOL[1] - 1900.0]); res = {'centre_finestra': C0.tolist(), 'angle_files_A': 136.3}
FONTS2 = dict(FONTS)
for arg in sys.argv[1:]:
    nv, _, dv = arg.partition('='); FONTS2[f'A_{nv}'] = (Path(dv) / 'sony_A_total.npy', 1); FONTS2[f'B_{nv}'] = (Path(dv) / 'cau/sony_B_total_v42.npy', 1)
for nom, (p, ch) in FONTS2.items():
    a = np.load(p, mmap_mode='r'); box = (int(C0[0] - 1800), int(C0[1] - 1800), int(C0[0] + 1800), int(C0[1] + 1800)); box = (max(0, box[0]), max(0, box[1]), min(W, box[2]), min(H, box[3]))
    r = rel_map(retall(a, ch, box), 40.0, 0.0, 41)
    s = np.arange(-1100, 1100.1, 2.0); t = np.arange(-1100, 1100.1, 0.5); X, Y = graella(C0, d, s, t); P = mostreja(r, X, Y, box[:2])
    with np.errstate(all='ignore'): pr = np.nanmean(P, 0)
    ok = np.isfinite(pr)
    if ok.mean() < 0.8: print(nom, 'poca cobertura'); continue
    pr = np.interp(t, t[ok], pr[ok]); pr = pr - np.convolve(pr, np.ones(161) / 161, 'same'); pr = pr[200:-200]
    F = np.abs(np.fft.rfft(pr * np.hanning(len(pr)))) ** 2; f = np.fft.rfftfreq(len(pr), 0.5)
    k = (f > 1 / 60) & (f < 1 / 4); med = np.median(F[k]); per = 1 / f[k]; j = np.argmin(np.abs(per - 17.9))
    w = np.abs(per - 17.9) < 0.8; pic = float(F[k][w].max() / med); iper = float(per[w][np.argmax(F[k][w])])
    amp = float(2 * np.sqrt(F[k][w].max()) / np.sum(np.hanning(len(pr))))   # amplitud d'una sinusoide amb finestra de Hann (unitats del residu)
    res[nom] = dict(pic_17_9_sobre_mediana=pic, periode_pic=iper, amplitud_aprox=amp)
    print(f"{nom:13s}: pic a {iper:.2f} px = ×{pic:.0f} la mediana de l'espectre · amplitud ≈ {amp*1e4:.1f}‱", flush=True)
desa(OUT / 'S16_REIXA_FILES.json', res)
