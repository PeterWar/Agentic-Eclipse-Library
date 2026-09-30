"""G2d · Les QUATRE marques verdes de Pere al Nubols.psb (capa RHEF), al LLENÇ SENCER a 1/4, amb tres jutges independents per a cada marca:
 (T) CANVI TEMPORAL: ln(inici/final) de cada tren, sense el perfil radial, banda 64–512 px. Un núvol prim canvia entre la primera i la segona meitat de la totalitat (el vent el mou);
     la corona, el cel llis i els residus de flat no. I si és núvol, els DOS trens veuen el mateix canvi (corr(T_V, T_S) > 0).
 (V×S) ACORD ENTRE TRENS de l'estructura estàtica (banda 64–512): el cel i la corona són compartits; un residu de flat o de vinyetatge és d'un sol tren.
 (B) BRNO: correlació de l'estructura azimutal per anell dins de la marca contra el 200 i el 400 mm de Brno (sostre: Brno×Brno). Brno no comparteix els nostres núvols.
Sortides: JSON a REB39, vistes 1/4 a VIS39 (mateixa escala per a tot el llenç, cap estirament per retall)."""
from comu39 import *
import cv2
from scipy.ndimage import gaussian_filter, binary_opening, label, distance_transform_edt
sys.path.insert(0, str(ROOT / 'research/tools/auditoria_estructura')); import nucli as N
from psd_tools import PSDImage
D = 4; SONY36 = ROOT / 'research/tools/v36_20260908/cau/sony_corrected_total_v36.npy'
SCR = Path('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/bb2a9ec7-d793-44f1-a277-703c16855cd4/scratchpad')


def q(p, c=1):
    arr = np.load(p, mmap_mode='r'); a = np.asarray(arr[::D, ::D, c] if arr.ndim == 3 else arr[::D, ::D], np.float32); return a
def lnm(a):
    m = np.isfinite(a) & (a > 0); return np.where(m, np.log(np.maximum(a, 1e-9)), 0).astype(np.float32), m
def gm(a, m, s):
    """gaussiana normalitzada per la màscara"""
    w = gaussian_filter(m.astype(np.float32), s); return np.where(w > 0.05, gaussian_filter(np.where(m, a, 0), s) / np.maximum(w, 1e-6), 0)
def band(a, m, s1, s2): return gm(a, m, s1) - gm(a, m, s2)
def corr(a, b, m):
    if m.sum() < 50: return float('nan')
    u = a[m] - a[m].mean(); v = b[m] - b[m].mean(); d = np.sqrt((u * u).sum() * (v * v).sum()); return float((u * v).sum() / d) if d > 0 else float('nan')
def sense_radial(a, m, r4, dr=8):
    """treu la mediana per anell de dr px (a 1/4) → només queda l'estructura azimutal (⛔ primera versió: r4 era en R☉ i feia 2 anells)"""
    out = np.zeros_like(a); rb = (r4 * RS / D / dr).astype(int); mx = rb[m].max() + 1   # anells de dr píxels (a 1/4); r4 és en R☉
    for i in range(mx):
        sel = m & (rb == i)
        if sel.sum() > 20: out[sel] = a[sel] - np.median(a[sel])
    return out
def png(nom, a, esc, m, marques, txt):
    img = np.clip((np.where(m, a, 0) / esc + 1) / 2 * 255, 0, 255).astype(np.uint8); img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR); img[~m] = (40, 40, 40)
    for k, mk in enumerate(marques):
        cnt, _ = cv2.findContours(mk.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE); cv2.drawContours(img, cnt, -1, (0, 255, 0), 2)
        ys, xs = np.where(mk); cv2.putText(img, f'M{k + 1}', (int(xs.mean()), int(ys.mean())), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (0, 255, 0), 3)
    cv2.putText(img, f'{txt}  (escala +-{esc:g} ln, tot el llenc igual)', (12, 36), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2); cv2.imwrite(str(VIS39 / f'G2d_{nom}_quart.png'), img); return img


def main():
    r, t = coords(); r4 = r[::D, ::D] / RS; az4 = np.degrees(t[::D, ::D])
    # 1. marques: tint verd de la capa RHEF del Nubols (R i B abaixats)
    mp = SCR / 'marques_quart.npy'
    if mp.exists(): marques_m = np.load(mp)
    else:
        psd = PSDImage.open('/Users/USUARI/Downloads/Nubols.psb'); L = next(l for l in psd if l.name == 'P02 RHEF · V38'); a = L.numpy()[::D, ::D, :3]
        verd = (a[..., 1] - 0.5 * (a[..., 0] + a[..., 2])) > 0.03; verd = binary_opening(verd, iterations=2); np.save(mp, verd); marques_m = verd; del a, psd
    lab, k = label(marques_m); sizes = np.bincount(lab.ravel())[1:]; ids = [i + 1 for i in np.argsort(sizes)[::-1] if sizes[i] > 2000]; marques = [lab == i for i in ids]
    log(f'marques trobades: {len(marques)} → ' + ' · '.join(f'M{j + 1}: {int(mk.sum()) * D * D / 1e6:.1f} Mpx, r {np.percentile(r4[mk], 5):.1f}–{np.percentile(r4[mk], 95):.1f} R☉, az {np.percentile(az4[mk], 5):.0f}…{np.percentile(az4[mk], 95):.0f}°' for j, mk in enumerate(marques)))
    # 2. dades a 1/4 (canal G)
    V, mV = lnm(q(CAU38 / 'vixen_total_v38.npy')); S, mS = lnm(q(SONY36)); F, mF = lnm(q(CAU38 / 'fusion_total_v38.npy'))
    VI, mVI = lnm(q(CAU39 / 'vixen_total_v38_inici.npy')); VF, mVF = lnm(q(CAU39 / 'vixen_total_v38_final.npy')); VE, mVE = lnm(q(CAU39 / 'vixen_total_v38_parell.npy')); VO, mVO = lnm(q(CAU39 / 'vixen_total_v38_senar.npy'))
    SI = np.zeros_like(S); SF = np.zeros_like(S); mSt = np.zeros_like(mS)
    for ap in ('A', 'B'):
        i_, mi = lnm(q(CAU39 / f'sony_{ap}_total_v38_inici.npy')); f_, mf = lnm(q(CAU39 / f'sony_{ap}_total_v38_final.npy')); mm = mi & mf & ~mSt; SI[mm] = i_[mm]; SF[mm] = f_[mm]; mSt |= mm
    dt = distance_transform_edt(mV) * D; mVc = mV & (dt > 64); dts = distance_transform_edt(mS) * D; mSc = mS & (dts > 64)   # lluny de les vores del suport (64 px)
    mTV = mVI & mVF & mVc; mTS = mSt & mSc; mA = mV & mS & mVc & mSc & (r4 > 1.3)
    s1, s2 = 64 / D, 512 / D
    # (T) canvi temporal per tren, sense perfil radial, banda 64–512
    TV = sense_radial(band(VI - VF, mTV, s1, s2), mTV, r4); TS = sense_radial(band(SI - SF, mTS, s1, s2), mTS, r4)
    TVc = sense_radial(band(VE - VO, mVE & mVO & mVc, s1, s2), mVE & mVO & mVc, r4)   # control: meitats aleatòries (només soroll)
    # (V×S) estructura estàtica
    BV = sense_radial(band(V, mV, s1, s2), mV, r4); BS = sense_radial(band(S, mS, s1, s2), mS, r4); BF = sense_radial(band(F, mF, s1, s2), mF, r4)
    rep = dict(marques=[]); log(f"{'marca':>6} {'r R☉':>9} | {'rms T_V':>8} {'rms ctrl':>8} {'rms T_S':>8} {'corr(T_V,T_S)':>14} | {'rms V':>7} {'rms S':>7} {'V×S':>6} {'F×S':>6} | {'T_V×V':>6} {'T_V×S':>6}")
    for j, mk in enumerate(marques):
        mtv = mk & mTV; mts = mk & mTS; mvs = mk & mA; d = dict(marca=j + 1, px=int(mk.sum()) * D * D, r_R=[float(np.percentile(r4[mk], 5)), float(np.percentile(r4[mk], 95))], az=[float(np.percentile(az4[mk], 5)), float(np.percentile(az4[mk], 95))])
        d['rms_TV'] = float(np.std(TV[mtv])) if mtv.sum() > 50 else float('nan'); d['rms_TV_control'] = float(np.std(TVc[mtv])) if mtv.sum() > 50 else float('nan'); d['rms_TS'] = float(np.std(TS[mts])) if mts.sum() > 50 else float('nan')
        d['corr_TV_TS'] = corr(TV, TS, mtv & mts); d['rms_V'] = float(np.std(BV[mvs])) if mvs.sum() > 50 else float('nan'); d['rms_S'] = float(np.std(BS[mvs])) if mvs.sum() > 50 else float('nan'); d['VxS'] = corr(BV, BS, mvs); d['FxS'] = corr(BF, BS, mvs)
        d['TV_x_V'] = corr(TV, BV, mtv & mvs); d['TV_x_S'] = corr(TV, BS, mtv & mvs)   # el canvi temporal s'assembla a l'estructura que es veu? (núvol congelat al total)
        d['cobertura_V'] = float(mtv.mean() / max(mk.mean(), 1e-9)); d['cobertura_S'] = float(mts.mean() / max(mk.mean(), 1e-9))
        rep['marques'].append(d); log(f"M{j + 1:<5} {d['r_R'][0]:>4.1f}–{d['r_R'][1]:<4.1f} | {d['rms_TV']:>8.4f} {d['rms_TV_control']:>8.4f} {d['rms_TS']:>8.4f} {d['corr_TV_TS']:>+14.2f} | {d['rms_V']:>7.4f} {d['rms_S']:>7.4f} {d['VxS']:>+6.2f} {d['FxS']:>+6.2f} | {d['TV_x_V']:>+6.2f} {d['TV_x_S']:>+6.2f}   (cobertura V {d['cobertura_V']:.2f} S {d['cobertura_S']:.2f})")
    # fora de les marques, mateix rang de radis (control de lloc)
    tot = np.zeros_like(marques_m)
    for mk in marques: tot |= mk
    for rr in ((2, 4), (4, 6), (6, 9)):
        sel = ~tot & (r4 >= rr[0]) & (r4 < rr[1]); d = dict(anell=rr, rms_TV=float(np.std(TV[sel & mTV])), rms_TV_control=float(np.std(TVc[sel & mTV])), rms_TS=float(np.std(TS[sel & mTS])), corr_TV_TS=corr(TV, TS, sel & mTV & mTS), VxS=corr(BV, BS, sel & mA), rms_V=float(np.std(BV[sel & mA])), rms_S=float(np.std(BS[sel & mA])))
        rep.setdefault('fora_marques', []).append(d); log(f"fora de les marques {rr[0]}–{rr[1]} R☉: rms T_V {d['rms_TV']:.4f} (ctrl {d['rms_TV_control']:.4f}) T_S {d['rms_TS']:.4f} corr(T_V,T_S) {d['corr_TV_TS']:+.2f} · estàtic: rms V {d['rms_V']:.4f} S {d['rms_S']:.4f} V×S {d['VxS']:+.2f}")
    # (B) Brno per marca: estructura azimutal per anell dins de la marca
    REG = json.loads((ROOT / 'research/tools/auditoria_estructura/registre2.json').read_text()); GEO = ROOT / 'research/tools/v25_lineal/cau_v25/geometria_v27.json'
    M = np.asarray(json.loads(GEO.read_text())['M_llenc_a_v23']); ANG = float(np.arctan2(M[1, 0], M[0, 0])); NTH = 1440; rr_all = np.round(np.arange(1.3, 9.0, 0.1), 2)
    brno = {}
    for name in ('TSE_2026_200mm_DHS.png', 'TSE_2026_400mm_DHS.png'):
        im, *_ = N.carrega_brno(name); g = REG[name]; brno[name] = N.mostreja(im, g['cy'], g['cx'], g['R_sol_px'], rr_all, NTH, ang0=np.deg2rad(g['gir_deg'])); del im
    fus = np.load(CAU38 / 'fusion_total_v38.npy', mmap_mode='r')[..., 1]; pf = N.mostreja(fus, CY, CX, RS, rr_all, NTH, ang0=ANG); lf = np.log(np.maximum(pf, 1e-9))
    vix = np.load(CAU38 / 'vixen_total_v38.npy', mmap_mode='r')[..., 1]; pv = N.mostreja(vix, CY, CX, RS, rr_all, NTH, ang0=ANG); lv = np.log(np.maximum(pv, 1e-9))
    son = np.load(SONY36, mmap_mode='r')[..., 1]; ps = N.mostreja(son, CY, CX, RS, rr_all, NTH, ang0=ANG); ls = np.log(np.maximum(ps, 1e-9))
    full = np.zeros((H, W), np.float32)
    for j, mk in enumerate(marques):
        mfull = cv2.resize(mk.astype(np.float32), (W, H), interpolation=cv2.INTER_NEAREST); pm = N.mostreja(mfull, CY, CX, RS, rr_all, NTH, ang0=ANG) > 0.5
        def estr(pol):
            p = pol.copy(); p[~pm] = np.nan; return N.estructura(p)
        eb = {n: estr(b) for n, b in brno.items()}; ef, ev, es = estr(lf), estr(lv), estr(ls); out = {}
        for n in brno:
            key = n.replace('TSE_2026_', '').replace('_DHS.png', ''); out[key] = dict(fusio=float(np.nanmedian(N.corr_per_anell(ef, eb[n]))), vixen=float(np.nanmedian(N.corr_per_anell(ev, eb[n]))), sony=float(np.nanmedian(N.corr_per_anell(es, eb[n]))))
        out['Brno200xBrno400'] = float(np.nanmedian(N.corr_per_anell(eb['TSE_2026_200mm_DHS.png'], eb['TSE_2026_400mm_DHS.png']))); out['VixenxSony_polar'] = float(np.nanmedian(N.corr_per_anell(ev, es)))
        rep['marques'][j]['brno'] = out; log(f"M{j + 1} Brno (mediana per anell dins de la marca): " + ' · '.join(f"{k}: fusió {v['fusio']:+.2f} V {v['vixen']:+.2f} S {v['sony']:+.2f}" if isinstance(v, dict) else f'{k} {v:+.2f}' for k, v in out.items()))
    savejson(REB39 / 'G2d_nubols_llenc.json', rep)
    # vistes al llenç sencer, mateixa escala
    escT = 0.004; escB = 0.02
    i1 = png('canvi_temporal_Vixen', TV, escT, mTV, marques, 'ln(Vixen inici / final), sense perfil radial, banda 64-512 px')
    i2 = png('canvi_temporal_Sony', TS, escT, mTS, marques, 'ln(Sony inici / final), sense perfil radial, banda 64-512 px')
    i3 = png('control_meitats_aleatories_Vixen', TVc, escT, mVE & mVO & mVc, marques, 'CONTROL: ln(Vixen parell / senar) = nomes soroll')
    i4 = png('estatic_Vixen', BV, escB, mV, marques, 'Vixen: estructura azimutal 64-512 px')
    i5 = png('estatic_Sony', BS, escB, mS, marques, 'Sony: estructura azimutal 64-512 px')
    i6 = png('estatic_fusio', BF, escB, mF, marques, 'fusio V38: estructura azimutal 64-512 px')
    h, w = i1.shape[:2]; sm = lambda im: cv2.resize(im, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    pan = np.vstack([np.hstack([sm(i1), sm(i2), sm(i3)]), np.hstack([sm(i4), sm(i5), sm(i6)])]); cv2.imwrite(str(VIS39 / 'G2d_panell_llenc_vuite.png'), pan); log('G2d fet')


if __name__ == '__main__':
    main()
