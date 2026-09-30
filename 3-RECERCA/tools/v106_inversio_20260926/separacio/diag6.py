"""Els residus arran de la vora (D < 2) són soroll aleatori entre fotogrames o estructura coherent en el temps?
Correlació dels residus r_j (δ_j − Ĉ − Λ̂_j) entre fotogrames consecutius (mateixos píxels, Lluna gairebé al mateix lloc)."""
import numpy as np
from pipeline import Pipeline
P = Pipeline({}); I = P.inverteix(P.fr); S = I.S; nd, nth = len(S.dg), S.nth
def res(j):
    c = I.cache[j]; return np.where(c['ok'], c['d'] - I.C - I.avalua_lam(c['a'], c['D']), np.nan), c['D']
parelles = [(0, 1), (1, 2), (2, 3), (5, 6), (0, 7), (9, 10), (14, 15), (15, 16), (26, 27), (32, 33), (50, 51), (51, 52), (55, 56), (60, 61), (50, 66), (0, 60), (9, 40)]
for lo, hi in [(0.6, 2.0), (2.0, 4.0), (6, 12)]:
    txt = []
    for a, b in parelles:
        if a not in I.cache or b not in I.cache: continue
        ra, Da = res(a); rb, Db = res(b); m = np.isfinite(ra) & np.isfinite(rb) & (Da >= lo) & (Da < hi) & (Db >= lo) & (Db < hi)
        if m.sum() > 2000: txt.append(f'{a}-{b}:{np.corrcoef(ra[m], rb[m])[0,1]:+.2f}')
    print(f'D {lo}-{hi}:', ' '.join(txt))
