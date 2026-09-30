"""G2b · La caixa verda per ESCALES i el desplaçament del patró entre meitats temporals.
Per a cada banda (passa-banda gaussià s1–s2): correlacions Vixen parell×senar, Vixen inici×final, Sony pA×pB, Sony inici×final, Vixen×Sony (totals), fusió×Sony.
I la prova del desplaçament: correlació de fase (finestra de Hann, pic dins de ±64 px) entre les meitats temporals de cada tren (control: meitats aleatòries → pic a 0).
Ús: g2b_nubols_escales.py x0 y0 x1 y1"""
from comu39 import *
from scipy.ndimage import gaussian_filter
from scipy.signal.windows import hann
SONY36 = ROOT / 'research/tools/v36_20260908/cau/sony_corrected_total_v36.npy'


def band(a, s1, s2): return gaussian_filter(a, s1) - gaussian_filter(a, s2)
def corr(a, b, m):
    u = a[m] - a[m].mean(); v = b[m] - b[m].mean(); d = np.sqrt((u * u).sum() * (v * v).sum()); return float((u * v).sum() / d) if d > 0 else float('nan')
def ln_crop(p, sl, c=1):
    arr = np.load(p, mmap_mode='r'); a = np.asarray(arr[sl][..., c] if arr.ndim == 3 else arr[sl], np.float32); m = np.isfinite(a) & (a > 0); return np.where(m, np.log(np.maximum(a, 1e-9)), 0), m
def desplacament(a, b, m, rmax=64):
    """correlació de fase normalitzada amb finestra de Hann; retorna (dx, dy, pic) dins de ±rmax"""
    h, w = a.shape; win = np.outer(hann(h), hann(w)); mm = m.astype(np.float32) * win
    A = np.fft.fft2((a - a[m].mean()) * mm); B = np.fft.fft2((b - b[m].mean()) * mm); R = A * np.conj(B); cc = np.fft.fftshift(np.fft.ifft2(R / np.maximum(np.abs(R), 1e-12)).real)
    cy, cx = h // 2, w // 2; sub = cc[cy - rmax:cy + rmax + 1, cx - rmax:cx + rmax + 1]; iy, ix = np.unravel_index(np.argmax(sub), sub.shape); return int(ix - rmax), int(iy - rmax), float(sub.max()), float(sub[rmax, rmax])


def main():
    x0, y0, x1, y1 = [int(v) for v in sys.argv[1:5]]; pad = 384; sl = (slice(max(y0 - pad, 0), min(y1 + pad, H)), slice(max(x0 - pad, 0), min(x1 + pad, W)))
    core = np.zeros((sl[0].stop - sl[0].start, sl[1].stop - sl[1].start), bool); core[y0 - sl[0].start:y1 - sl[0].start, x0 - sl[1].start:x1 - sl[1].start] = True
    V, mV = ln_crop(CAU38 / 'vixen_total_v38.npy', sl); S, mS = ln_crop(SONY36, sl); F, mF = ln_crop(CAU38 / 'fusion_total_v38.npy', sl)
    VE, mVE = ln_crop(CAU39 / 'vixen_total_v38_parell.npy', sl); VO, mVO = ln_crop(CAU39 / 'vixen_total_v38_senar.npy', sl); VI, mVI = ln_crop(CAU39 / 'vixen_total_v38_inici.npy', sl); VF, mVF = ln_crop(CAU39 / 'vixen_total_v38_final.npy', sl)
    # Sony: l'apuntament que cobreix la caixa
    sony = {}
    for ap in ('A', 'B'):
        a, ma = ln_crop(CAU39 / f'sony_{ap}_total_v38_pA.npy', sl); cob = float(ma[core].mean()); log(f'Sony {ap}: cobertura de la caixa {cob:.2f}')
        if cob > 0.9:
            b, mb = ln_crop(CAU39 / f'sony_{ap}_total_v38_pB.npy', sl); i, mi = ln_crop(CAU39 / f'sony_{ap}_total_v38_inici.npy', sl); f, mf = ln_crop(CAU39 / f'sony_{ap}_total_v38_final.npy', sl); sony[ap] = (a, b, i, f, ma & mb & mi & mf)
    m = mV & mS & mF & mVE & mVO & mVI & mVF & core
    for ap in sony: m &= sony[ap][4]
    log(f'caixa x {x0}–{x1} y {y0}–{y1} · píxels vàlids {int(m.sum())} · apuntaments Sony amb cobertura: {list(sony)}')
    rows = []
    log(f"{'banda px':>10} {'V par×sen':>10} {'V ini×fin':>10} {'S pA×pB':>9} {'S ini×fin':>10} {'V×S':>7} {'F×S':>7} {'F×V':>7} {'rmsV':>7} {'rmsS':>7} {'N_V/2':>7} {'N_S/2':>7}")
    for s1, s2 in ((2, 4), (4, 8), (8, 16), (16, 32), (32, 64), (64, 128), (128, 256)):
        bV, bS, bF, bVE, bVO, bVI, bVF = (band(x, s1, s2) for x in (V, S, F, VE, VO, VI, VF)); r = dict(banda=[s1, s2])
        r['V_par_sen'] = corr(bVE, bVO, m); r['V_ini_fin'] = corr(bVI, bVF, m); r['VxS'] = corr(bV, bS, m); r['FxS'] = corr(bF, bS, m); r['FxV'] = corr(bF, bV, m)
        r['rmsV'] = float(np.std(bV[m])); r['rmsS'] = float(np.std(bS[m])); r['NV2'] = float(np.std((bVE - bVO)[m]) / 2)
        r['S_pA_pB'] = r['S_ini_fin'] = r['NS2'] = float('nan')
        for ap, (a, b, i, f, _) in sony.items():
            ba, bb, bi, bf = (band(x, s1, s2) for x in (a, b, i, f)); r['S_pA_pB'] = corr(ba, bb, m); r['S_ini_fin'] = corr(bi, bf, m); r['NS2'] = float(np.std((ba - bb)[m]) / 2); r['sony_ap'] = ap
        rows.append(r); log(f"{s1:>4}–{s2:<5} {r['V_par_sen']:>+10.2f} {r['V_ini_fin']:>+10.2f} {r['S_pA_pB']:>+9.2f} {r['S_ini_fin']:>+10.2f} {r['VxS']:>+7.2f} {r['FxS']:>+7.2f} {r['FxV']:>+7.2f} {r['rmsV']:>7.4f} {r['rmsS']:>7.4f} {r['NV2']:>7.4f} {r['NS2']:>7.4f}")
    # desplaçament del patró (banda 8–64) entre meitats: temporals i aleatòries (control)
    des = {}
    for nom, (a, b) in {'Vixen inici→final': (VI, VF), 'Vixen parell→senar (control)': (VE, VO)}.items():
        dx, dy, pic, zero = desplacament(band(a, 8, 64), band(b, 8, 64), m); des[nom] = dict(dx=dx, dy=dy, pic=pic, a_zero=zero); log(f'desplaçament {nom}: ({dx:+d}, {dy:+d}) px, pic {pic:.3f}, valor a (0,0) {zero:.3f}')
    for ap, (a, b, i, f, _) in sony.items():
        for nom, (p, q) in {f'Sony {ap} inici→final': (i, f), f'Sony {ap} pA→pB (control)': (a, b)}.items():
            dx, dy, pic, zero = desplacament(band(p, 8, 64), band(q, 8, 64), m); des[nom] = dict(dx=dx, dy=dy, pic=pic, a_zero=zero); log(f'desplaçament {nom}: ({dx:+d}, {dy:+d}) px, pic {pic:.3f}, valor a (0,0) {zero:.3f}')
    # i Vixen→Sony (mateix instant): si el patró és del cel, pic a 0
    dx, dy, pic, zero = desplacament(band(V, 8, 64), band(S, 8, 64), m); des['Vixen→Sony'] = dict(dx=dx, dy=dy, pic=pic, a_zero=zero); log(f'desplaçament Vixen→Sony: ({dx:+d}, {dy:+d}) px, pic {pic:.3f}, valor a (0,0) {zero:.3f}')
    savejson(REB39 / f'G2b_nubols_escales_{x0}_{y0}.json', dict(caixa=[x0, y0, x1, y1], files=rows, desplacaments=des)); log('G2b fet')


if __name__ == '__main__':
    main()
