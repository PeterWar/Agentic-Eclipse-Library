"""E1e (V41) · La rotació entre els dos apuntaments de la Sony, mesurada a les estrelles, amb DEDUPLICACIÓ i CONTROL NUL.
Entrada: E1d_estrelles_dobles.json (pic real per apuntament A i B, prop de cada component de la capa `Estrelles`).
(1) Vectors A→B per estrella DIFERENT (components de la capa a < 8 px del mateix pic real es fusionen). Model: d = t + θ·(−(y−CY), (x−CX)) [+ s·(x−CX, y−CY)].
(2) Control nul: els mateixos vectors permutats entre posicions (2000 permutacions): quin rms i quin |θ| dona l'atzar.
(3) La capa `Estrelles` respecte del pic real de la fusió: translació sola vs rotació+translació (per saber com s'hauria de re-registrar)."""
from comu41 import *
rng = np.random.default_rng(0)


def ajust(P, D, escala=False):
    n = len(P); A = np.zeros((2 * n, 4 if escala else 3)); A[0::2, 0] = 1; A[1::2, 1] = 1; A[0::2, 2] = -P[:, 1]; A[1::2, 2] = P[:, 0]
    if escala: A[0::2, 3] = P[:, 0]; A[1::2, 3] = P[:, 1]
    sol, *_ = np.linalg.lstsq(A, D.ravel(), rcond=None); pred = (A @ sol).reshape(-1, 2); rms = float(np.sqrt(np.mean((D - pred) ** 2)))
    return dict(t=sol[:2].tolist(), theta_arcmin=float(np.degrees(sol[2]) * 60), escala_pct=float(sol[3] * 100) if escala else None, rms_px_per_component=rms), pred


def dedup(rows, key):
    out = []
    for r in rows:
        p = np.array(key(r))
        if any(np.hypot(*(p - np.array(key(o)))) < 8 for o in out): continue
        out.append(r)
    return out


def main():
    rows = json.loads((REB41 / 'E1d_estrelles_dobles.json').read_text())['files']
    # A→B
    ab = [r for r in rows if 'sep_AB' in r and r['sonyA'][0]['snr'] > 4 and r['sonyB'][0]['snr'] > 4]; posA = lambda r: (r['cat_x'] + r['sonyA'][0]['dx'], r['cat_y'] + r['sonyA'][0]['dy'])
    abu = dedup(sorted(ab, key=lambda r: -min(r['sonyA'][0]['snr'], r['sonyB'][0]['snr'])), posA)
    P = np.array([[posA(r)[0] - CX, posA(r)[1] - CY] for r in abu], float); D = np.array([r['sep_AB_px'] for r in abu], float)
    tr, pred = ajust(P, D); trs, _ = ajust(P, D, escala=True); t_sol, _ = ajust(P, D * 0 + D, escala=False)
    rms_brut = float(np.sqrt(np.mean(D ** 2))); rms_trans = float(np.sqrt(np.mean((D - D.mean(0)) ** 2)))
    # component tangencial contra r
    rr = np.hypot(P[:, 0], P[:, 1]); tang = (D[:, 1] * P[:, 0] - D[:, 0] * P[:, 1]) / rr; rad = (D[:, 0] * P[:, 0] + D[:, 1] * P[:, 1]) / rr
    Dc = D - np.array(tr['t']); tangc = (Dc[:, 1] * P[:, 0] - Dc[:, 0] * P[:, 1]) / rr; radc = (Dc[:, 0] * P[:, 0] + Dc[:, 1] * P[:, 1]) / rr; corr_tr = float(np.corrcoef(tangc, rr)[0, 1])
    # nul: permutar els vectors entre posicions
    nul = []
    for _ in range(2000):
        Dp = D[rng.permutation(len(D))]; f, _ = ajust(P, Dp); nul.append((abs(f['theta_arcmin']), f['rms_px_per_component']))
    nul = np.array(nul); p_rms = float(np.mean(nul[:, 1] <= tr['rms_px_per_component'])); p_theta = float(np.mean(nul[:, 0] >= abs(tr['theta_arcmin'])))
    log(f"A→B: {len(ab)} components → {len(abu)} estrelles diferents · rms brut {rms_brut:.2f} px · només translació {rms_trans:.2f} · rotació+translació: θ {tr['theta_arcmin']:+.2f}′, t ({tr['t'][0]:+.1f}, {tr['t'][1]:+.1f}) px, rms {tr['rms_px_per_component']:.2f} px/component · +escala {trs['escala_pct']:+.3f} % rms {trs['rms_px_per_component']:.2f}")
    log(f"  tangencial (sense t) creix amb r: corr {corr_tr:+.2f}; radial mitjana {radc.mean():+.1f} ± {radc.std():.1f} px · NUL (2000 permutacions): rms ≤ observat en {100 * p_rms:.1f} % dels casos, |θ| ≥ observat en {100 * p_theta:.1f} %; rms nul mediana {np.median(nul[:, 1]):.2f} px, |θ| nul mediana {np.median(nul[:, 0]):.2f}′")
    for r, p, q in zip(abu, D, pred): log(f"    {r['r_R']:4.1f} R☉  mesurat ({p[0]:+.0f},{p[1]:+.0f})  model ({q[0]:+.1f},{q[1]:+.1f})")
    # capa Estrelles → pic real (fusió)
    ok = [r for r in rows if r['fusio'] and r['fusio'][0]['snr'] > 4]; posF = lambda r: (r['cat_x'] + r['fusio'][0]['dx'], r['cat_y'] + r['fusio'][0]['dy']); oku = dedup(sorted(ok, key=lambda r: -r['fusio'][0]['snr']), posF)
    Pc = np.array([[r['cat_x'] - CX, r['cat_y'] - CY] for r in oku], float); Dc2 = np.array([[r['fusio'][0]['dx'], r['fusio'][0]['dy']] for r in oku], float)
    cat_tr, _ = ajust(Pc, Dc2); rms_cat_trans = float(np.sqrt(np.mean((Dc2 - Dc2.mean(0)) ** 2)))
    dob = dedup([r for r in oku if len(r['fusio']) >= 2 and r['fusio'][1]['snr'] > 4 and np.hypot(r['fusio'][1]['dx'] - r['fusio'][0]['dx'], r['fusio'][1]['dy'] - r['fusio'][0]['dy']) < 30], posF)
    log(f"capa Estrelles → pic real: {len(ok)} components → {len(oku)} estrelles; desplaçament mitjà ({Dc2.mean(0)[0]:+.0f}, {Dc2.mean(0)[1]:+.0f}) px, rms després de translació sola {rms_cat_trans:.1f} px; rotació+translació θ {cat_tr['theta_arcmin']:+.1f}′ rms {cat_tr['rms_px_per_component']:.1f} px · dobles a la fusió: {len(dob)} de {len(oku)}")
    savejson(REB41 / 'E1e_rotacio_AB.json', dict(n_components=len(ab), n=len(abu), rms_brut_px=rms_brut, rms_nomes_translacio_px=rms_trans, translacio_px=tr['t'], rotacio_arcmin=tr['theta_arcmin'], rms_residu_px=tr['rms_px_per_component'], amb_escala=trs,
        tangencial_vs_r_corr=corr_tr, radial_mitjana_px=float(radc.mean()), radial_std_px=float(radc.std()), nul=dict(permutacions=2000, p_rms=p_rms, p_theta=p_theta, rms_mediana=float(np.median(nul[:, 1])), theta_abs_mediana=float(np.median(nul[:, 0]))),
        vectors=[dict(r_R=r['r_R'], posA=posA(r), AB=r['sep_AB_px']) for r in abu], capa_estrelles=dict(n_components=len(ok), n=len(oku), desplacament_mitja_px=Dc2.mean(0).tolist(), rms_translacio_sola_px=rms_cat_trans, rotacio_arcmin=cat_tr['theta_arcmin'], rms_rotacio_px=cat_tr['rms_px_per_component'], translacio_px=cat_tr['t']),
        estrelles_diferents_amb_pic=len(oku), dobles=len(dob), referencia_research_125='rotació de camp del salt d\'apuntament +7,9′ (28-08)')); log('E1e fet')


if __name__ == '__main__':
    main()
