import numpy as np, json
Y = np.array([0.2126, 0.7152, 0.0722])
sk = np.load('sketch_q4.npy'); fo = np.load('foto.npy')
g = json.load(open('geom.json')); es = json.load(open('escala_sketch.json'))

# --- Display P3 -> sRGB (mateixa TRC; matriu lineal)
def dec(u):  # sRGB TRC decode
    return np.where(u <= 0.04045, u/12.92, ((u+0.055)/1.055)**2.4)
def enc(v):
    v = np.clip(v, 0, 1)
    return np.where(v <= 0.0031308, 12.92*v, 1.055*v**(1/2.4) - 0.055)
P3_XYZ = np.array([[0.4865709, 0.2656677, 0.1982173],
                   [0.2289746, 0.6917385, 0.0792869],
                   [0.0000000, 0.0451134, 1.0439444]])
XYZ_sRGB = np.array([[ 3.2404542, -1.5371385, -0.4985314],
                     [-0.9692660,  1.8760108,  0.0415560],
                     [ 0.0556434, -0.2040259,  1.0572252]])
M = XYZ_sRGB @ P3_XYZ
print('P3->sRGB lineal\n', np.round(M, 4))
sk_lin = dec(sk) @ M.T
frac_neg = float(np.mean(sk_lin < -1e-4))
sk_s = enc(sk_lin).astype(np.float32)   # sketch en sRGB codificat
print('sketch: fracció de píxels fora de gamut sRGB', frac_neg)
np.save('sketch_q4_srgb.npy', sk_s)

def anells(img, cx, cy):
    h, w = img.shape[:2]
    return np.hypot((np.arange(w)-cx)[None,:], (np.arange(h)-cy)[:,None])

def perfil(img, cx, cy, Rs, vores, nom):
    r = anells(img, cx, cy)/Rs
    Yv = img @ Y
    R_, G_, B_ = img[...,0], img[...,1], img[...,2]
    rg = R_/np.maximum(G_, 1e-6); bg = B_/np.maximum(G_, 1e-6)
    files = []
    for a, b in zip(vores[:-1], vores[1:]):
        m = (r >= a) & (r < b)
        n = int(m.sum())
        # cobertura de l'anell: àrea real / àrea teòrica de l'anell
        cob = n / (np.pi*(b*b - a*a)*Rs*Rs)
        if n < 50: files.append(dict(r0=a, r1=b, n=n, cob=cob)); continue
        d = dict(r0=float(a), r1=float(b), rmid=float(0.5*(a+b)), n=n, cob=float(min(cob,1.0)))
        for k, v in (('R', R_), ('G', G_), ('B', B_), ('Y', Yv), ('RG', rg), ('BG', bg)):
            q = np.percentile(v[m], [16, 50, 84])
            d[k] = float(q[1]); d[k+'_16'] = float(q[0]); d[k+'_84'] = float(q[2])
        files.append(d)
    return files

vores = np.round(np.arange(1.0, 8.6, 0.1), 2)
cxs, cys, Rs_sk = es['sol_cx_q4'], es['sol_cy_q4'], es['R_sol_q4']
prof_sk = perfil(sk_s, cxs, cys, Rs_sk, vores, 'sketch')
prof_sk_p3 = perfil(sk, cxs, cys, Rs_sk, vores, 'sketch_p3')
prof_fo = perfil(fo, 3439.0, 2234.0, 446.15, vores, 'foto')
json.dump(dict(sketch=prof_sk, sketch_p3=prof_sk_p3, foto=prof_fo), open('perfils.json','w'))
print('\n r0-r1   | sketch(sRGB) G   Y   R/G   B/G  cob |  foto G    Y    R/G   B/G  cob')
for a, b in zip(prof_sk, prof_fo):
    if 'G' not in a or 'G' not in b: 
        print(f"{a['r0']:.1f}-{a['r1']:.1f} sense dades (n={a.get('n')}, {b.get('n')})"); continue
    print(f"{a['r0']:.1f}-{a['r1']:.1f} | {a['G']:.4f} {a['Y']:.4f} {a['RG']:.3f} {a['BG']:.3f} {a['cob']:.2f} | "
          f"{b['G']:.4f} {b['Y']:.4f} {b['RG']:.3f} {b['BG']:.3f} {b['cob']:.2f}")

# --- earthshine: disc lunar
def disc(img, cx, cy, Rl, nom):
    r = anells(img, cx, cy)
    m = r < 0.85*Rl
    G_ = img[...,1][m]; Yv = (img @ Y)[m]
    out = dict(nom=nom, n=int(m.sum()))
    for k, v in (('G', G_), ('Y', Yv), ('R', img[...,0][m]), ('B', img[...,2][m])):
        q = np.percentile(v, [5, 50, 95]); out[k] = [float(x) for x in q]
    # perfil radial dins del disc
    prof = []
    for a in np.arange(0, 1.0, 0.1):
        mm = (r >= a*Rl) & (r < (a+0.1)*Rl)
        prof.append((float(a+0.05), float(np.median(img[...,1][mm])), float(np.median((img@Y)[mm]))))
    out['perfil_G_Y'] = prof
    return out
s = g['sketch_q4']; f = g['foto']
d_sk = disc(sk_s, s['cx'], s['cy'], s['R'], 'sketch sRGB')
d_sk_p3 = disc(sk, s['cx'], s['cy'], s['R'], 'sketch P3')
# a la FOTO: centre lunar de l'ajust i R = 460 (disc enganxat); també amb el centre del npz
d_fo = disc(fo, 3442.25, 2231.67, 460.0, 'foto (centre npz)')
d_fo2 = disc(fo, f['cx'], f['cy'], 460.0, 'foto (centre ajust)')
for d in (d_sk, d_sk_p3, d_fo, d_fo2):
    print(d['nom'], 'n', d['n'], 'G p5/50/95', np.round(d['G'],4), 'Y', np.round(d['Y'],4), 'R', np.round(d['R'],4), 'B', np.round(d['B'],4))
    print('   perfil (r/Rl, G, Y):', [(round(a,2), round(b,4), round(c,4)) for a,b,c in d['perfil_G_Y']])
json.dump(dict(sketch=d_sk, sketch_p3=d_sk_p3, foto=d_fo, foto_ajust=d_fo2), open('disc.json','w'), indent=1)

# --- cel per sectors: uniformitat
def sectors(img, cx, cy, Rs, r0, r1, nom):
    h, w = img.shape[:2]
    yy = (np.arange(h)-cy)[:,None]; xx = (np.arange(w)-cx)[None,:]
    r = np.hypot(xx, yy)/Rs; th = np.degrees(np.arctan2(-yy, xx)) % 360  # 0=E(dreta),90=N(dalt)
    m = (r >= r0) & (r < r1)
    print(f'{nom} anell {r0}-{r1} R_sol per sectors de 45°: (Y mediana, R/G, B/G, n)')
    for a in range(0, 360, 45):
        mm = m & (th >= a) & (th < a+45)
        if mm.sum() < 100: print(f'  {a:3d}-{a+45:3d}: -'); continue
        Yv = (img@Y)[mm]; print(f'  {a:3d}-{a+45:3d}: {np.median(Yv):.4f}  {np.median(img[...,0][mm]/img[...,1][mm]):.3f} {np.median(img[...,2][mm]/img[...,1][mm]):.3f}  n={mm.sum()}')
sectors(sk_s, cxs, cys, Rs_sk, 4.0, 4.5, 'SKETCH')
sectors(sk_s, cxs, cys, Rs_sk, 6.2, 7.0, 'SKETCH')
sectors(fo, 3439.0, 2234.0, 446.15, 4.0, 4.5, 'FOTO')
sectors(fo, 3439.0, 2234.0, 446.15, 6.2, 7.0, 'FOTO')
