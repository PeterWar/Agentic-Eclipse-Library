"""c12 · Hipòtesi: els filtres llegeixen el VERD després de la matriu de color (càmera → Adobe RGB). Per a la llum Hα (cromosfera i protuberàncies),
fora de gamma, aquest verd surt baix o negatiu: els filtres hi veuen fosc. Prova: a la caixa de la franja (dada d'un instant E, amb la mateixa
matriu i els mateixos guanys), comparació del verd matricial G_m amb la lluminància Y d'Adobe RGB (0,2974 R + 0,6273 G + 0,0753 B, sempre ≥ 0
per a llum real), a la cromosfera de l'esquerra, a la protuberància i a la corona de control. I una normalització radial (NRGF simple, per anells
d'1 px sobre tots els azimuts) de G_m i de Y, per veure si l'anell fosc i la protuberància fosca desapareixen.
Sortida: VERD_O_LLUMINANCIA.json i LAMINA_M12_verd_o_lluminancia.png."""
from vm_comu import *
from PIL import Image, ImageDraw, ImageFont
claim()
Q = np.load(V88D / 'A3A_franja_un_instant.npz'); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; E = Q['E']; dom = Q['domini']
cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']; yy, xx = np.mgrid[by0:by1, bx0:bx1]; r = np.hypot(xx - cx, yy - cy); d = r - R
th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
Gm = E[..., 1]; Y = 0.2974 * E[..., 0] + 0.6273 * E[..., 1] + 0.0753 * E[..., 2]
ok = dom & (d > 0) & (d < 45)
k = np.median(Y[ok & (d > 20)] / Gm[ok & (d > 20)]); Yn = Y / k        # mateix nivell que G_m a la corona (20–45 px)
zones = {'cromosfera esquerra 140–165° 1,5–6 px': (140, 165, 1.5, 6), 'cromosfera esquerra 195–220° 1,5–6 px': (195, 220, 1.5, 6),
         'protuberància 172–184° 3–30 px': (172, 184, 3, 30), 'corona control dalt 80–100° 1,5–6 px': (80, 100, 1.5, 6), 'corona 140–165° 15–30 px': (140, 165, 15, 30)}
res = dict(Y_sobre_Gm_a_la_corona=float(k), zones={})
for nom, (a0, a1, d0, d1) in zones.items():
    s = ok & (th >= a0) & (th <= a1) & (d >= d0) & (d <= d1)
    res['zones'][nom] = dict(px=int(s.sum()), R_m=float(np.median(E[..., 0][s])), G_m=float(np.median(Gm[s])), B_m=float(np.median(E[..., 2][s])), Y_nivellada=float(np.median(Yn[s])),
                             G_m_negatiu_frac=float((Gm[s] < 0).mean()), Yn_sobre_Gm=float(np.median(Yn[s] / np.maximum(Gm[s], 1e-6))))
desa_json('VERD_O_LLUMINANCIA.json', res); log(json.dumps(res, ensure_ascii=False))
# NRGF simple per anells d'1 px (tots els azimuts, domini) de G_m i de Y
def nrgf(A):
    ri = np.clip(r.astype(int), 0, int(r.max())); out = np.full(A.shape, np.nan, np.float32)
    for rr in range(int(R) - 2, int(R) + 60):
        s = ok & (ri == rr)
        if s.sum() > 50: m, sd = np.median(A[s]), np.std(A[s]); out[s] = (A[s] - m) / max(sd, 1e-9)
    return out
Ng, Ny = nrgf(Gm), nrgf(Yn)
try: F_ = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 19)
except Exception: F_ = FB = ImageFont.load_default()
BP = (4840 - bx0, 3500 - by0, 5040 - bx0, 4100 - by0)     # meitat esquerra del limbe amb la protuberància
def v(A, lo, hi): return Image.fromarray(np.uint8(np.nan_to_num(np.clip((A - lo) / (hi - lo), 0, 1)) * 255))
cr = (slice(BP[1], BP[3]), slice(BP[0], BP[2])); zf = 2; w_, h_ = (BP[2] - BP[0]) * zf, (BP[3] - BP[1]) * zf
S = Image.new('RGB', (4 * (w_ + 8), h_ + 60), 'white'); dr = ImageDraw.Draw(S)
dr.text((6, 6), 'Entrada dels filtres a la vora esquerra (2:1): verd matricial G_m (el que fan servir) · lluminància Y · NRGF simple de G_m · NRGF simple de Y', fill='black', font=FB)
lo, hi = np.nanpercentile(Gm[cr][ok[cr]], [1, 99.5])
for i, (A, lo_, hi_, et) in enumerate([(Gm, lo, hi, 'G_m'), (Yn, lo, hi, 'Y (mateix nivell a la corona)'), (Ng, -3, 3, 'NRGF de G_m'), (Ny, -3, 3, 'NRGF de Y')]):
    S.paste(v(np.where(ok, A, np.nan)[cr], lo_, hi_).resize((w_, h_), Image.LANCZOS).convert('RGB'), (i * (w_ + 8), 56)); dr.text((i * (w_ + 8) + 3, 34), et, fill='black', font=F_)
S.save(SORT / 'LAMINA_M12_verd_o_lluminancia.png'); log('fet')
