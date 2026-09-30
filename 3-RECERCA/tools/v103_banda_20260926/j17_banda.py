"""j17 (V103 banda) · Portes de la franja a3d contra l'a3c de la V99, sobre la dada linealitzada (E post-matriu, G'), per sector de 30° i calaix de
0,5 px de distància a la silueta REAL de presentació:
  (1) COBERTURA: DMIN per azimut (V99 i V103) i el primer calaix amb dada (domini_E) per sector;
  (2) NIVELL a la transició (règim de banda → règim net): perfil de ln G' per calaix; residu contra la recta ajustada a 6–12 px (com j14/j15);
      «graó» = residu màxim en valor absolut a 2–6 px; el mateix per a la V99 on té dada; i la diferència V103 − V99 on tots dos tenen dada
      (ha de ser ≈ 0 fora de la banda: byte a byte);
  (3) DETALL: rms del detall tangencial (DoG 2→16 px al llarg de l'arc) per calaix, V103 contra V99 (on té dada) i contra el règim net lluny;
  (4) PORTA: on g > 0,5 (règim de banda), nombre de fotogrames i D_real màxima.
Ús: j17_banda.py <A3C_franja_silueta.npz (V103)> <A3C_franja_silueta.npz (V99)> <sortida.json>. Només lectura."""
import sys, json
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; R9 = ARREL / '4-RESULTATS/v99_banda_20260925'
A = np.load(sys.argv[1]); B = np.load(sys.argv[2]); OUT = Path(sys.argv[3])
by0, by1, bx0, bx1 = [int(v) for v in A['box']]; LX, LY, RL = [float(v) for v in A['centre']]
S = np.load(R9 / 'D21_silueta_o2.npz'); pag, eg = S['pa'], S['e']
EA, DA, GA, NFA = A['E'][..., 1], A['domini_E'], A['porta_banda'], A['NF']; EB, DB = B['E'][..., 1], B['domini_E']; DMA, DMB = A['DMIN'], B['DMIN']; DXA = A['DREAL_MAX']
EBAN = A['E_banda'][..., 1] if 'E_banda' in A.files else None; ENET = A['E_net'][..., 1] if 'E_net' in A.files else None; WBAN = A['W_banda'] if 'W_banda' in A.files else None; WNET = A['W_net'] if 'W_net' in A.files else None
def polar(img, a0, a1, r0=0.0, r1=14.0, DS=0.5):
    rr = np.arange(r0, r1, 0.25); tt = np.radians(np.arange(a0, a1, DS / RL * 180 / np.pi)); R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij')
    e_ = np.interp(np.degrees(T_).ravel() % 360, pag, eg, period=360).reshape(R_.shape)
    PX = (LX + (R_ + e_) * np.cos(T_) - bx0).astype(np.float32); PY = (LY - (R_ + e_) * np.sin(T_) - by0).astype(np.float32)
    return rr, cv2.remap(img.astype(np.float32), PX, PY, cv2.INTER_NEAREST)   # veí més proper SEMPRE: el lineal barrejava els zeros de fora del domini (ln 1e-6) dins la vora
rep = dict(sectors={}, DMIN_per_azimut={str(a): dict(V99=round(float(DMB[int(a / 360 * len(DMB))]), 2), V103=round(float(DMA[int(a / 360 * len(DMA))]), 2)) for a in range(0, 360, 15)})
BINS = np.arange(0.5, 12.0, 0.5)
for a0 in range(0, 360, 30):
    a1 = a0 + 30; rr, PA_ = polar(np.log(np.maximum(EA, 1e-6)), a0, a1); _, PB_ = polar(np.log(np.maximum(EB, 1e-6)), a0, a1)
    _, dA = polar(DA.astype(np.int16), a0, a1); _, dB = polar(DB.astype(np.int16), a0, a1); _, gA = polar(GA, a0, a1); _, nfA = polar(NFA, a0, a1); _, dxA = polar(DXA, a0, a1)
    dA = dA > 0.5; dB = dB > 0.5
    # perfils de nivell (mediana al llarg de l'arc, només amb dada) i recta a 6–12
    def perfil(P, D):
        m = np.where(D, P, np.nan); return np.nanmedian(m, axis=1) if np.isfinite(m).any() else np.full(len(rr), np.nan)
    pA, pB = perfil(PA_, dA), perfil(PB_, dB); fit = (rr >= 6) & (rr < 12)
    def residu(pp):
        ok = fit & np.isfinite(pp)
        if ok.sum() < 8: return np.full(len(rr), np.nan)
        c = np.polyfit(rr[ok], pp[ok], 1); return pp - np.polyval(c, rr)
    rA, rB = residu(pA), residu(pB)
    def dog(P, D):
        Pm = np.where(D, P, np.nan); Pf = np.where(np.isfinite(Pm), Pm, np.nanmedian(Pm, axis=1, keepdims=True)); Pf = np.nan_to_num(Pf)
        g2 = gaussian_filter1d(Pf, 2 / 0.5, axis=1, mode='nearest'); g16 = gaussian_filter1d(Pf, 16 / 0.5, axis=1, mode='nearest'); return np.where(D, g2 - g16, np.nan)
    tA, tB = dog(PA_, dA), dog(PB_, dB); s = {}
    # costura entre règims: ln(E_banda / E_net) on tots dos tenen pes (mateixos fotogrames a 4–6,5 px al costat d'avanç: mesura només l'efecte de T)
    if EBAN is not None:
        _, pb = polar(np.log(np.maximum(EBAN, 1e-6)), a0, a1); _, pn = polar(np.log(np.maximum(ENET, 1e-6)), a0, a1); _, wb_ = polar(WBAN, a0, a1); _, wn_ = polar(WNET, a0, a1); _, en_ = polar(ENET, a0, a1); _, eb_ = polar(EBAN, a0, a1)
        amb2 = (wb_ > 0) & (wn_ > 0) & (en_ > 0) & (eb_ > 0) & dA   # només on TOTS DOS règims tenen dada de debò
        frac_b = np.where(wn_ + gA * wb_ > 0, gA * wb_ / np.maximum(wn_ + gA * wb_, 1e-30), 0.0)   # fracció de banda PER PÍXEL (Codex, ronda 3): g·Wb/(Wn + g·Wb), amb el W_net separat
        amb_net = amb2 & (frac_b <= 0.5)   # on el règim net domina de debò, píxel a píxel
    else: amb2 = None
    for lo in BINS:
        m = (rr >= lo) & (rr < lo + 0.5); cobA = float(np.nanmean(dA[m])); cobB = float(np.nanmean(dB[m])); amb = dA[m] & dB[m]
        s[f'{lo:.1f}'] = dict(cob_V103=round(cobA, 2), cob_V99=round(cobB, 2), g_banda=round(float(np.nanmean(gA[m][dA[m]])), 2) if dA[m].any() else None,
                           NF_V103=float(np.nanmedian(nfA[m][dA[m]])) if dA[m].any() else None, Dreal_max_p50=round(float(np.nanmedian(dxA[m][dA[m]])), 2) if dA[m].any() else None,
                           residu_nivell_V103=round(float(np.nanmedian(rA[m])), 4) if np.isfinite(rA[m]).any() else None, residu_nivell_V99=round(float(np.nanmedian(rB[m])), 4) if np.isfinite(rB[m]).any() else None,
                           dif_V103_menys_V99_on_tots_dos=round(float(np.nanmedian((PA_[m] - PB_[m])[amb])), 4) if amb.sum() > 50 else None,
                           detall_rms_V103=round(float(np.nanstd(tA[m][dA[m]])), 4) if cobA >= 0.9 else None, detall_rms_V99=round(float(np.nanstd(tB[m][dB[m]])), 4) if cobB >= 0.9 else None,
                           costura_banda_menys_net=round(float(np.nanmedian((pb[m] - pn[m])[amb2[m]])), 4) if amb2 is not None and amb2[m].sum() > 50 else None,
                           costura_on_net_domina_px=round(float(np.nanmedian((pb[m] - pn[m])[amb_net[m]])), 4) if amb2 is not None and amb_net[m].sum() > 50 else None,
                           fraccio_banda_px_p50=round(float(np.nanmedian(frac_b[m][amb2[m]])), 3) if amb2 is not None and amb2[m].sum() > 50 else None)
    primer = lambda D: next((float(rr[k]) for k in range(len(rr)) if np.nanmean(D[k]) >= 0.5), None)
    # «graó» = residu màxim a la ZONA DE TRANSICIÓ entre règims (4–6,5 px), on hi hauria una costura; a 2–4 px el residu és estructura real
    # (curvatura de la corona, cromosfera, protuberàncies: la V99 la té igual on hi arriba) i s'informa, però no es jutja
    grao = max((abs(v['residu_nivell_V103']) for k, v in s.items() if v['residu_nivell_V103'] is not None and 4.5 <= float(k) < 6.5), default=None)   # 4,5–6,5: on la porta g fa la transició
    grao24 = max((abs(v['residu_nivell_V103']) for k, v in s.items() if v['residu_nivell_V103'] is not None and 2.0 <= float(k) < 4.0), default=None)
    difmax = max((abs(v['dif_V103_menys_V99_on_tots_dos']) for k, v in s.items() if v['dif_V103_menys_V99_on_tots_dos'] is not None and v['cob_V103'] >= 0.9 and v['cob_V99'] >= 0.9 and float(k) < 12), default=None)
    graoB = max((abs(v['residu_nivell_V99']) for k, v in s.items() if v['residu_nivell_V99'] is not None and 4.5 <= float(k) < 6.5 and v['cob_V99'] >= 0.9), default=None)
    rep['sectors'][f'{a0}-{a1}'] = dict(primer_calaix_amb_dada_V99=primer(dB), primer_calaix_amb_dada_V103=primer(dA), grao_transicio_45_65_V103=None if grao is None else round(grao, 4), grao_transicio_45_65_V99=None if graoB is None else round(graoB, 4),
                                        residu_2_4_V103_informatiu=None if grao24 is None else round(grao24, 4), dif_max_V103_V99_on_tots_dos=None if difmax is None else round(difmax, 4), calaixos=s)
    print(f"{a0:3d}-{a1:3d}: dada des de V99 {primer(dB)} → V103 {primer(dA)} · transició 4,5–6,5: V103 {grao} (V99 {graoB}) · |V103−V99| {difmax} · residu 2–4 (inf.) {grao24} · det 2–3: {s['2.0']['detall_rms_V103']} / 3–4: {s['3.0']['detall_rms_V103']} / 7–10: {s['7.0']['detall_rms_V103']} (V99 {s['7.0']['detall_rms_V99']})")
# control nul i veredicte: el «graó» de la V99 als sectors on té dada des de ≤ 2 px (dreta) és el nivell nul de l'operador (curvatura real de la corona
# sobre la recta de 6–12 px); PASSA si, a cada sector del costat d'avanç (60–270°), el graó de la V103 ≤ max(0,02, 2 × nul) i la costura ≤ 2 %
# nul PER SECTOR: el residu de la V99 a la mateixa zona de transició (la curvatura real d'aquell sector); on la V99 no hi arriba, el nul general
nul = [v['grao_transicio_45_65_V99'] for k, v in rep['sectors'].items() if v['grao_transicio_45_65_V99'] is not None]
NUL = float(np.median(nul)) if nul else 0.02; LLINDAR = max(0.02, 2 * NUL); falles = []
for k, v in rep['sectors'].items():
    a0 = int(k.split('-')[0])
    if 60 <= a0 < 270:
        ll = max(0.02, 1.5 * v['grao_transicio_45_65_V99']) if v['grao_transicio_45_65_V99'] is not None else LLINDAR
        if v['grao_transicio_45_65_V103'] is not None and v['grao_transicio_45_65_V103'] > ll: falles.append(f'{k}: graó a la transició {v["grao_transicio_45_65_V103"]} (llindar {ll:.4f})')
        # la costura només es jutja on el règim net domina (g ≤ 0,5: ≥ 2,5 fotogrames nets efectius); amb g > 0,5 el «net» són uns pocs curts
        # amb pes ínfim i el biaix de color dels 1/3200 (doc. 170 §4): no és referència
        cs = [abs(c['costura_on_net_domina_px']) for c in v['calaixos'].values() if c.get('costura_on_net_domina_px') is not None]
        if cs and max(cs) > 0.02: falles.append(f'{k}: costura on el net domina per píxel {max(cs):.4f}')
        # (la costura sobre TOTS els píxels amb dos règims és informativa: on la banda domina, el «net» són uns pocs curts amb pes ínfim i biaix de color)
    if v['dif_max_V103_V99_on_tots_dos'] is not None and v['dif_max_V103_V99_on_tots_dos'] > 0.02: falles.append(f'{k}: |V103 − V99| on tots dos tenen dada {v["dif_max_V103_V99_on_tots_dos"]}')
rep['veredicte'] = dict(nul_V99_dreta=None if not nul else round(NUL, 4), llindar_grao=round(LLINDAR, 4), falles=falles, resultat='PASSA' if not falles else 'FALLA')
print('NUL (V99, transició 4,5–6,5 px, tots els sectors amb cobertura)', rep['veredicte']['nul_V99_dreta'], 'llindar', rep['veredicte']['llindar_grao'], rep['veredicte']['resultat'], falles)
OUT.write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print('fet', OUT)
