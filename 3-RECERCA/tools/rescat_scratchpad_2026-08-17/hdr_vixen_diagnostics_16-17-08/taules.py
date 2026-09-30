import numpy as np, json
Y = np.array([0.2126, 0.7152, 0.0722])
sk = np.load('sketch_q4_srgb.npy'); fo = np.load('foto.npy')
es = json.load(open('escala_sketch.json')); g = json.load(open('geom.json'))
def anells(img, cx, cy):
    h, w = img.shape[:2]; return np.hypot((np.arange(w)-cx)[None,:], (np.arange(h)-cy)[:,None])
r_sk = anells(sk, es['sol_cx_q4'], es['sol_cy_q4'])/es['R_sol_q4']
r_fo = anells(fo, 3439.0, 2234.0)/446.15
def stats(img, r, r0, dr=0.05):
    m = (r >= r0-dr) & (r < r0+dr)
    G_ = img[...,1][m]; Yv = (img@Y)[m]; RG = img[...,0][m]/np.maximum(G_,1e-6); BG = img[...,2][m]/np.maximum(G_,1e-6)
    cob = m.sum()/(np.pi*((r0+dr)**2-(r0-dr)**2)*(es['R_sol_q4']**2 if img is sk else 446.15**2))
    return dict(G=np.percentile(G_,[16,50,84]), Y=np.percentile(Yv,[16,50,84]), RG=np.percentile(RG,[16,50,84]), BG=np.percentile(BG,[16,50,84]), n=int(m.sum()), cob=float(min(cob,1)))
radis = [1.1,1.3,1.5,2.0,2.5,3.0,4.0,5.0,6.0,6.8,8.0]
print('| R☉ | sketch G (16–84) | FOTO G (16–84) | raó FOTO/sketch | sketch Y | FOTO Y | cobertura sk/foto |')
print('|---|---|---|---|---|---|---|')
out = {}
for r0 in radis:
    a = stats(sk, r_sk, r0); b = stats(fo, r_fo, r0)
    out[r0] = dict(sk=a, fo=b)
    print(f"| {r0} | {a['G'][1]:.3f} ({a['G'][0]:.3f}–{a['G'][2]:.3f}) | {b['G'][1]:.3f} ({b['G'][0]:.3f}–{b['G'][2]:.3f}) | {b['G'][1]/a['G'][1]:.2f} | {a['Y'][1]:.3f} | {b['Y'][1]:.3f} | {a['cob']:.2f}/{b['cob']:.2f} |")
print()
print('| R☉ | sketch R/G | sketch B/G | FOTO R/G | FOTO B/G |')
print('|---|---|---|---|---|')
for r0 in radis:
    a, b = out[r0]['sk'], out[r0]['fo']
    print(f"| {r0} | {a['RG'][1]:.3f} ({a['RG'][0]:.3f}–{a['RG'][2]:.3f}) | {a['BG'][1]:.3f} ({a['BG'][0]:.3f}–{a['BG'][2]:.3f}) | {b['RG'][1]:.3f} ({b['RG'][0]:.3f}–{b['RG'][2]:.3f}) | {b['BG'][1]:.3f} ({b['BG'][0]:.3f}–{b['BG'][2]:.3f}) |")
# zones d'ancoratge exactes del tool
for nom, img, r in (('sketch', sk, r_sk), ('foto', fo, r_fo)):
    for (a,b,tag) in ((1.5,2.2,'corona'), (6.2,7.0,'cel'), (1.02,1.08,'nucli 1.05'), (1.94,2.06,'2.0'), (6.6,7.0,'6.8'), (5.8,6.2,'6.0'), (1.45,1.55,'1.5')):
        m = (r>=a)&(r<b); G_=img[...,1][m]; Yv=(img@Y)[m]
        print(f"{nom:7s} {tag:10s} {a}-{b}: G={np.median(G_):.4f} Y={np.median(Yv):.4f} R/G={np.median(img[...,0][m]/G_):.3f} B/G={np.median(img[...,2][m]/G_):.3f} n={m.sum()}")
