"""G2 · Què és el que Pere marca en verd a nubols.psb: núvols molt fins, cel, corona o artefacte del filtre? Quatre proves en la BANDA de l'estructura
(passa-banda gaussià s1–s2 px) dins de la caixa marcada:
 (a) Vixen parell × senar (fotogrames alternats en el temps): alt = persistent (corona, cel estàtic o sistemàtic); baix = soroll.
 (b) Vixen inici × final (primera i segona meitat de la totalitat): alt = estàtic; BAIX (amb (a) alt) = varia en el temps → transparència / núvols.
 (c) Vixen × Sony (mateix instant, mateix lloc, dos telescopis): alt = compartit (corona O cel, els núvols també són compartits); baix = sistemàtic d'un tren.
 (d) capa nostra × Brno (altre lloc): els núvols no són compartits; la corona sí. Es fa en polar sobre els anells i azimuts de la caixa.
Ús: g2_nubols.py x0 y0 x1 y1 [s1=8 s2=64]"""
from comu39 import *
import cv2
from scipy.ndimage import gaussian_filter
sys.path.insert(0, str(ROOT / 'research/tools/auditoria_estructura')); import nucli as N


def band(a, s1, s2):
    return gaussian_filter(a, s1) - gaussian_filter(a, s2)


def corr(a, b, m):
    u = a[m] - a[m].mean(); v = b[m] - b[m].mean(); d = np.sqrt((u * u).sum() * (v * v).sum()); return float((u * v).sum() / d) if d > 0 else float('nan')


def main():
    x0, y0, x1, y1 = [int(v) for v in sys.argv[1:5]]; s1 = float(sys.argv[5]) if len(sys.argv) > 5 else 8.0; s2 = float(sys.argv[6]) if len(sys.argv) > 6 else 64.0
    pad = int(3 * s2); sl = (slice(max(y0 - pad, 0), min(y1 + pad, H)), slice(max(x0 - pad, 0), min(x1 + pad, W))); core = (slice(y0 - sl[0].start, y1 - sl[0].start), slice(x0 - sl[1].start, x1 - sl[1].start))
    r, t = coords(); rq = r[sl] / RS; az = np.degrees(t[sl]); wv = np.nan_to_num(np.asarray(np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r')[sl], np.float32))
    log(f'caixa x {x0}–{x1} y {y0}–{y1}: r {rq[core].min():.2f}–{rq[core].max():.2f} R☉ · az {az[core].min():.0f}…{az[core].max():.0f}° · pes Vixen mitjà {wv[core].mean():.2f} · banda {s1:g}–{s2:g} px')
    def ln_crop(p, c=1):
        a = np.asarray(np.load(p, mmap_mode='r')[sl][..., c] if np.load(p, mmap_mode='r').ndim == 3 else np.load(p, mmap_mode='r')[sl], np.float32); m = np.isfinite(a) & (a > 0); return np.where(m, np.log(np.maximum(a, 1e-9)), 0), m
    E, mE = ln_crop(CAU39 / 'vixen_total_v38_parell.npy'); O, mO = ln_crop(CAU39 / 'vixen_total_v38_senar.npy'); V, mV = ln_crop(CAU38 / 'vixen_total_v38.npy')
    S, mS = ln_crop(ROOT / 'research/tools/v36_20260908/cau/sony_corrected_total_v36.npy'); F, mF = ln_crop(CAU38 / 'fusion_total_v38.npy')
    m = mE & mO & mV & mS & mF; mc = np.zeros_like(m); mc[core] = True; m &= mc
    bE, bO, bV, bS, bF = (band(x, s1, s2) for x in (E, O, V, S, F))
    rep = {'caixa': [x0, y0, x1, y1], 'banda_px': [s1, s2], 'r_R': [float(rq[core].min()), float(rq[core].max())], 'az_deg': [float(az[core].min()), float(az[core].max())], 'pes_vixen': float(wv[core].mean())}
    rep['a_vixen_parell_x_senar'] = corr(bE, bO, m); rep['c_vixen_x_sony'] = corr(bV, bS, m); rep['fusio_x_sony'] = corr(bF, bS, m); rep['fusio_x_vixen'] = corr(bF, bV, m)
    rep['rms_banda'] = {'vixen': float(np.std(bV[m])), 'sony': float(np.std(bS[m])), 'fusio': float(np.std(bF[m])), 'meitat_diferencia_sobre_2': float(np.std((bE - bO)[m]) / 2)}
    log(f"(a) Vixen parell×senar {rep['a_vixen_parell_x_senar']:+.3f} · (c) Vixen×Sony {rep['c_vixen_x_sony']:+.3f} · fusió×Sony {rep['fusio_x_sony']:+.3f} · fusió×Vixen {rep['fusio_x_vixen']:+.3f} · rms banda V {rep['rms_banda']['vixen']:.4f} S {rep['rms_banda']['sony']:.4f} F {rep['rms_banda']['fusio']:.4f} soroll(meitats)/2 {rep['rms_banda']['meitat_diferencia_sobre_2']:.4f}")
    pi, pf = CAU39 / 'vixen_total_v38_inici.npy', CAU39 / 'vixen_total_v38_final.npy'
    if pi.exists() and pf.exists():
        I, mI = ln_crop(pi); Fi, mFi = ln_crop(pf); mm = m & mI & mFi; bI, bFi = band(I, s1, s2), band(Fi, s1, s2)
        rep['b_vixen_inici_x_final'] = corr(bI, bFi, mm); rep['b_inici_x_parell'] = corr(bI, bE, mm)
        # desplaçament entre inici i final (correlació de fase): si l'estructura es mou, hi ha un pic desplaçat
        a_, b_ = np.where(mm, bI, 0), np.where(mm, bFi, 0); Fa, Fb = np.fft.fft2(a_), np.fft.fft2(b_); cc = np.fft.ifft2(Fa * np.conj(Fb) / np.maximum(np.abs(Fa * np.conj(Fb)), 1e-12)).real
        iy, ix = np.unravel_index(np.argmax(cc), cc.shape); dy = iy if iy < cc.shape[0] // 2 else iy - cc.shape[0]; dx = ix if ix < cc.shape[1] // 2 else ix - cc.shape[1]; rep['desplacament_inici_final_px'] = [int(dx), int(dy)]
        log(f"(b) Vixen inici×final {rep['b_vixen_inici_x_final']:+.3f} (inici×parell {rep['b_inici_x_parell']:+.3f}) · desplaçament de fase inici→final ({dx}, {dy}) px")
    else:
        log('(b) inici/final encara no recompostos')
    # (d) Brno: estructura azimutal als anells i azimuts de la caixa
    REG = json.loads((ROOT / 'research/tools/auditoria_estructura/registre2.json').read_text()); GEO = ROOT / 'research/tools/v25_lineal/cau_v25/geometria_v27.json'
    M = np.asarray(json.loads(GEO.read_text())['M_llenc_a_v23']); ANG = float(np.arctan2(M[1, 0], M[0, 0])); NTH = 1440
    rr = np.round(np.arange(max(1.2, np.floor(rq[core].min() * 10) / 10), min(9.0, np.ceil(rq[core].max() * 10) / 10) + 0.05, 0.1), 2)
    a0, a1 = az[core].min(), az[core].max(); th = (np.degrees(np.linspace(0, 2 * np.pi, NTH, endpoint=False) + ANG) + 180) % 360 - 180; selaz = (th >= a0) & (th <= a1)
    def estr_box(pol):
        p = pol.copy(); p[:, ~selaz] = np.nan; return N.estructura(p)
    outs = {}
    for name in ('TSE_2026_200mm_DHS.png', 'TSE_2026_400mm_DHS.png', 'TSE_2026_530mm_DHS.png'):
        im, *_ = N.carrega_brno(name); g = REG[name]; pb = N.mostreja(im, g['cy'], g['cx'], g['R_sol_px'], rr, NTH, ang0=np.deg2rad(g['gir_deg'])); outs[name] = estr_box(pb); del im
    fus = np.load(CAU38 / 'fusion_total_v38.npy', mmap_mode='r')[..., 1]; pf_ = N.mostreja(fus, CY, CX, RS, rr, NTH, ang0=ANG); ef = estr_box(np.log(np.maximum(pf_, 1e-9)))
    vix = np.load(CAU38 / 'vixen_total_v38.npy', mmap_mode='r')[..., 1]; pv = N.mostreja(vix, CY, CX, RS, rr, NTH, ang0=ANG); ev = estr_box(np.log(np.maximum(pv, 1e-9)))
    son = np.load(ROOT / 'research/tools/v36_20260908/cau/sony_corrected_total_v36.npy', mmap_mode='r')[..., 1]; ps = N.mostreja(son, CY, CX, RS, rr, NTH, ang0=ANG); es = estr_box(np.log(np.maximum(ps, 1e-9)))
    d = {}
    for name, eb in outs.items():
        cf = N.corr_per_anell(ef, eb); cv = N.corr_per_anell(ev, eb); cs = N.corr_per_anell(es, eb); d[name] = {'fusio': float(np.nanmedian(cf)), 'vixen': float(np.nanmedian(cv)), 'sony': float(np.nanmedian(cs))}
    cb = N.corr_per_anell(outs['TSE_2026_200mm_DHS.png'], outs['TSE_2026_400mm_DHS.png']); d['Brno200xBrno400'] = float(np.nanmedian(cb)); rep['d_brno_estructura_azimutal_per_anell_mediana'] = d
    log('(d) Brno (estructura azimutal per anell dins de la caixa, mediana): ' + '; '.join(f"{k.replace('TSE_2026_', '').replace('_DHS.png', '')}: fusió {v['fusio']:+.2f} Vixen {v['vixen']:+.2f} Sony {v['sony']:+.2f}" if isinstance(v, dict) else f'{k} {v:+.2f}' for k, v in d.items()))
    savejson(REB39 / f'G2_nubols_{x0}_{y0}.json', rep); log('G2 fet')


if __name__ == '__main__':
    main()
