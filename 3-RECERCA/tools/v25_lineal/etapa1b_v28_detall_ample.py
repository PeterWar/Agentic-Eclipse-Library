#!/usr/bin/env python3
"""V26 · etapa 1b (04-09-2026), sobre els mateixos runs i la mateixa fusió que l'etapa 1:

  (a) la fusió NOMÉS-CORONA desada (`cf_corona_lin.npy`): el cel restat per la descomposició
      de color de la cadena (research/100 §D). Mesurat als runs: el cel iguala la corona a
      2,5 R☉ i la supera ×5,9 a 4, ×13 a 5 i ×24-30 a 6 R☉ — per això la base amb cel surt
      PLANA de 2,7 R☉ enfora i els streamers no s'hi veuen;
  (b) el detall ACHF a ESCALES GRANS (32-256 px, calculat a 1/4 de resolució) sobre
      ln(corona) amb NRGF davant: és on són els streamers (research/82: a 4 R☉ l'estructura
      real comença a 0,5-0,7° = 30-45 px; el 2-32 px de l'etapa 1 hi és soroll). La
      modulació azimutal REAL de la corona és 0,13-0,27 fins a 5 R☉ i soroll (>0,6) des de 6;
  (c) la base alternativa amb el cel reduït: corona + k·cel amb k = 0,25 DECLARAT, la mateixa
      corba B i la MATEIXA àncora que la base de l'etapa 1 (la corona interior no canvia).
"""
import os, sys, json, time, importlib.util
import numpy as np, cv2
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/.claude/skills/corregeix-artefactes/scripts")
import artefactes as art
GHOSTS_V23 = [dict(x=4911, y=5014, radi=50, dx=52, dy=-130, font="ghost Sony 3,0 R☉ (research/116)")]   # V23 de la V26 (M1 vella): només serveix per situar-lo al llenç; els de ~8 R☉ cauen a la zona esvaïda
spec = importlib.util.spec_from_file_location("e1", os.path.join(AQUI, "etapa1_fusio_base_detall.py")); e1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(e1)
comu, f3, fpil = e1.comu, e1.f3, e1.fpil
CAU = e1.CAU; K_CEL = 0.25; SIGMES_GRAN_4 = (8, 16, 32, 64); T0 = time.time()
FADE_GRAN_FI, FADE_GRAN_GROS = (3.0, 4.5), (5.0, 7.0)      # V28: la mitjana (64-256 px) fins a 7 R☉ (total × Brno 200 mm = 0,8 a 4,5° fins a 6,4 R☉)
FADE_AMPLE = (9.0, 9.8); BLEND_FONT = (3.0, 4.0); TERRA_AMPLE = 8.0              # V28: banda ampla 256-1024 px d'arc fins a la vora de cobertura; font corona sola ≤3 R☉ → TOTAL ≥4 R☉
R_TERRA_MAD = 3.5                                          # el MAD per anell no baixa del valor a 3,5 R☉: no s'amplifica cap anell de sistemàtics
REB = {"k_cel": K_CEL, "detall_gran": "passa-alt AZIMUTAL en polar: bandes <64 px i 64-256 px d'arc", "corba": e1.CORBA_B, "esvaiment_gran_fi_32-64px": FADE_GRAN_FI, "esvaiment_gran_gros_128-256px": FADE_GRAN_GROS, "font_hibrida_Rsol": BLEND_FONT, "esvaiment_ample": FADE_AMPLE, "suavitzat_sn": "f3.suavitza_sn a 1/4 per banda", "terra_mad_Rsol": R_TERRA_MAD}
def marca(t): print(f"[{time.time()-T0:7.1f} s] {t}", flush=True)


def passa_alt_azimutal(x, m, rad, R, s_px, nr=700, nt=2880, r0=1.03, r1=9.6):
    """Bandes azimutals en polar (ln r, θ): a = x − G_θ(x; s0) i b = G_θ(x; s0) − G_θ(x; s1), amb σ en px
    d'arc a cada radi (σ_cols = s / r_px · nt / 2π), convolució normalitzada per la màscara i θ cíclic.
    Torna (a, b) al llenç cartesià (mateixa mida que x)."""
    from scipy.ndimage import gaussian_filter1d
    H, W = x.shape; cy, cx = H / 2.0 - 0.5, W / 2.0 - 0.5
    lo, hi = np.log(r0), np.log(r1); rr = np.exp(np.linspace(lo, hi, nr)) * R; th = np.linspace(0, 2 * np.pi, nt, endpoint=False)
    xs = (cx + rr[:, None] * np.cos(th)[None, :]).astype(np.float32); ys = (cy + rr[:, None] * np.sin(th)[None, :]).astype(np.float32)
    P = cv2.remap(np.where(m, x, 0.0).astype(np.float32), xs, ys, cv2.INTER_LINEAR); Pm = cv2.remap(m.astype(np.float32), xs, ys, cv2.INTER_LINEAR)
    def suau_theta(A, Am, s):
        out = np.empty_like(A)
        for i in range(nr):
            sig = max(s / rr[i] * nt / (2 * np.pi), 0.5)
            num = gaussian_filter1d(A[i] * Am[i], sig, mode="wrap"); den = gaussian_filter1d(Am[i], sig, mode="wrap")
            out[i] = num / np.maximum(den, 1e-6)
        return out
    S0 = suau_theta(P, Pm, s_px[0]); S1 = suau_theta(P, Pm, s_px[1])
    A_pol = np.where(Pm > 0.5, P - S0, 0.0).astype(np.float32); B_pol = np.where(Pm > 0.5, S0 - S1, 0.0).astype(np.float32)
    # tornada al cartesià: (r, θ) de cada píxel → (fila, columna) del polar (θ cíclic: 4 columnes de marge)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); rp = np.hypot(yy - cy, xx - cx); tp = np.arctan2(yy - cy, xx - cx) % (2 * np.pi)
    fil = ((np.log(np.maximum(rp / R, 1e-6)) - lo) / (hi - lo) * (nr - 1)).astype(np.float32); col = (tp / (2 * np.pi) * nt).astype(np.float32)
    def tornar(Ppol):
        Pw = np.hstack([Ppol, Ppol[:, :4]])
        return cv2.remap(Pw, col, fil, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return tornar(A_pol), tornar(B_pol)


def main():
    rv, Sv, Cv, CELv, Pv = e1.carrega(e1.VIX); rs, Ss, Cs, CELs, Ps = e1.carrega(e1.SON)
    W, H, RS = Sv["W"], Sv["H"], Sv["R_sol_px"]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy - H / 2.0, xx - W / 2.0).astype(np.float32); theta = np.arctan2(yy - H / 2.0, xx - W / 2.0).astype(np.float32); del yy, xx
    mv = comu.mascara_dada(Pv, rad); ms = comu.mascara_dada(Ps, rad)
    for c in comu.CANALS:
        mv &= np.isfinite(Cv[c]) & np.isfinite(CELv[c]); ms &= np.isfinite(Cs[c]) & np.isfinite(CELs[c])
    _, uv = comu.lluminancia(np.dstack([Cv[c] + CELv[c] for c in comu.CANALS]), rv.matriu, rv.color["guany"])
    _, cv = comu.lluminancia(np.dstack([Cv[c] for c in comu.CANALS]), rv.matriu, rv.color["guany"])
    _, us = comu.lluminancia(np.dstack([Cs[c] + CELs[c] for c in comu.CANALS]), rs.matriu, rs.color["guany"])
    _, cs = comu.lluminancia(np.dstack([Cs[c] for c in comu.CANALS]), rs.matriu, rs.color["guany"])
    del Cv, CELv, Cs, CELs, Pv, Ps
    uv, cv, us, cs = (np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0) for x in (uv, cv, us, cs))
    mb = mv & ms
    for i, c in enumerate(comu.CANALS):
        rho = e1.rho_baixa_freq(uv[..., i], us[..., i], mb, rad, theta, RS, c); us[..., i] *= rho; cs[..., i] *= rho
    del rho; REB["rho"] = e1.REBUT["rho"]
    wv = (1.0 - e1.smoothstep(rad / RS, *e1.MASCARA_FUSIO)) * mv; ws = (1.0 - wv) * ms
    wv = np.where(ms, wv, mv.astype(np.float32)); ws = np.where(mv, ws, ms.astype(np.float32))
    den = np.maximum(wv + ws, 1e-6); mf = (wv + ws) > 0
    assert np.array_equal(mf, np.load(os.path.join(CAU, "mascara_fusio.npy"))), "la màscara de fusió no és la de l'etapa 1"
    uf = np.empty_like(uv); cf = np.empty_like(uv)
    for i in range(3):
        uf[..., i] = (wv * uv[..., i] + ws * us[..., i]) / den; cf[..., i] = (wv * cv[..., i] + ws * cs[..., i]) / den
    del uv, us, cv, cs, wv, ws, den
    cf = np.where(mf[..., None], np.maximum(cf, 0.0), 0.0).astype(np.float32)
    np.save(os.path.join(CAU, "cf_corona_lin.npy"), cf); marca("fusió refeta · corona sola desada")
    # --- cel/corona per anell (rebut) ---
    Lc = ((cf[..., 0] + 2 * cf[..., 1] + cf[..., 2]) / 4.0).astype(np.float32); Lu = ((uf[..., 0] + 2 * uf[..., 1] + uf[..., 2]) / 4.0).astype(np.float32)
    REB["cel_sobre_corona"] = {}
    for r in (2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0):
        s = mf & (np.abs(rad - r * RS) < 0.05 * RS); c_ = float(np.median(Lc[s])); REB["cel_sobre_corona"][str(r)] = round((float(np.median(Lu[s])) - c_) / max(c_, 1e-9), 2)
    marca(f"cel/corona {REB['cel_sobre_corona']}")
    # --- G a l'ORIGEN: el ghost de 3 R☉ es tapa a la corona sola ABANS del detall gran (si no, el
    #     passa-alt de 128-256 px hi deixa un anell fosc de ~150 px que cap pedaç posterior cobreix) ---
    Gm = json.load(open(os.path.join(CAU, "geometria_v23.json"))); Minv = cv2.invertAffineTransform(np.array(Gm["M_llenc_a_v23"], np.float64))
    REB["ghosts_tapats_a_la_corona"] = []
    for g in json.load(open(os.path.join(CAU, "ghosts_llenc.json"))):           # V28: tots els ghosts al llenç (etapa 0)
        gx, gy = g["x"], g["y"]
        bol = art.corregeix_bol(cf, gx, gy, r_in=g["radi"] - 10, r_out=130) if g.get("bol") else None
        art.tapa_inpaint(cf, gx, gy, g["radi"]); art.clona_textura(cf, gx, gy, g["radi"], g["dx"], g["dy"])
        REB["ghosts_tapats_a_la_corona"].append(dict(g, metode="(bol) + inpaint + textura clonada", bol=bol))
    # --- estrelles fora de la corona sola ABANS del detall gran: el passa-alt azimutal de 16-64 px converteix
    #     cada estrella en un disc brillant saturat de 50-100 px (punt A de la V27 ronda 4). Detecció compacta
    #     (DoG 1,5-6 px > 6 MAD, 5-400 px) i inpaint de radi 12 amb ploma 6. Les capes fines les conserven.
    Lc = ((cf[..., 0] + 2 * cf[..., 1] + cf[..., 2]) / 4.0).astype(np.float32)
    from scipy.ndimage import gaussian_filter as _gf, label as _label, find_objects as _fo
    hp = _gf(Lc, 1.5) - _gf(Lc, 6.0); v = hp[mf & (rad > 1.1 * RS)]; med = float(np.median(v)); mad = 1.4826 * float(np.median(np.abs(v - med)))
    # ⛔ amb 6 MAD sortien 13.808 «estrelles» (gra): llindar 20 MAD, pic ≥ 25 MAD, i com a molt 300 (les que saturen el detall gran són poques)
    lab, n = _label((hp - med > 20 * mad) & mf & (rad > 1.1 * RS)); cand = []
    for i, sl in enumerate(_fo(lab), 1):
        c = lab[sl] == i; area = int(c.sum()); h_, w_ = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if area < 4 or area > 400 or max(h_, w_) > 30: continue
        pic = float((hp[sl][c].max() - med) / mad)
        if pic < 25: continue
        ys, xs = np.nonzero(c); yc = int(sl[0].start + ys.mean()); xc = int(sl[1].start + xs.mean())
        if 60 < yc < H - 60 and 60 < xc < W - 60: cand.append((pic, xc, yc, area))
    cand.sort(reverse=True); estr = []
    for pic, xc, yc, area in cand[:300]:
        art.tapa_inpaint(cf, xc, yc, 12, ploma=6); estr.append((xc, yc, area, round(pic, 1)))
    Lc = ((cf[..., 0] + 2 * cf[..., 1] + cf[..., 2]) / 4.0).astype(np.float32)
    REB["estrelles_fora_del_detall_gran"] = {"n": len(estr), "candidates": len(cand), "criteri": "DoG 1,5-6 px > 20 MAD, pic ≥ 25 MAD, 4-400 px, ≤30 px, màx 300; inpaint r 12", "pics_MAD_top5": [e[3] for e in estr[:5]]}
    marca(f"ghosts tapats a la corona sola: {REB['ghosts_tapats_a_la_corona']} · estrelles inpaintades per al detall gran: {len(estr)}")
    # --- (b) ACHF gran a 1/4 ---
    md = mf & (rad > 1.05 * RS) & (Lc > 0)
    W4, H4 = W // 4, H // 4; assert W4 * 4 == W and H4 * 4 == H
    w4 = cv2.resize(md.astype(np.float32), (W4, H4), interpolation=cv2.INTER_AREA)
    L4 = cv2.resize(np.where(md, Lc, 0.0).astype(np.float32), (W4, H4), interpolation=cv2.INTER_AREA) / np.maximum(w4, 1e-6)
    m4 = (w4 > 0.5) & (L4 > 0)
    yy4, xx4 = np.mgrid[0:H4, 0:W4].astype(np.float32); rad4 = np.hypot(yy4 - H4 / 2.0, xx4 - W4 / 2.0).astype(np.float32); del yy4, xx4
    x4c = np.where(m4, np.log(np.maximum(L4, 1e-9)), 0.0).astype(np.float32); x4c = e1.nrgf_lnr(x4c, m4, rad4, RS / 4.0)
    # ⛔ V28 (research/133): de 4 R☉ enfora la CORONA SOLA de la descomposició s'ANTICORRELACIONA amb Brno
    #    (−0,5 a −0,8 amb el 200 mm) mentre que el TOTAL (corona + cel) hi correlaciona a 0,75-0,80 fins a
    #    8,6 R☉: el model de cel s'empassa l'estructura azimutal. Font híbrida en ln: corona sola ≤3 R☉,
    #    total ≥4 R☉ (tots dos amb la mediana per anell restada).
    Lt = ((uf[..., 0] + 2 * uf[..., 1] + uf[..., 2]) / 4.0).astype(np.float32)
    mt = mf & (rad > 1.05 * RS) & (Lt > 0); wt4 = cv2.resize(mt.astype(np.float32), (W4, H4), interpolation=cv2.INTER_AREA)
    Lt4 = cv2.resize(np.where(mt, Lt, 0.0).astype(np.float32), (W4, H4), interpolation=cv2.INTER_AREA) / np.maximum(wt4, 1e-6); mt4 = (wt4 > 0.5) & (Lt4 > 0)
    x4t = np.where(mt4, np.log(np.maximum(Lt4, 1e-9)), 0.0).astype(np.float32); x4t = e1.nrgf_lnr(x4t, mt4, rad4, RS / 4.0)
    wfont = (1 - e1.smoothstep(rad4 / (RS / 4.0), *BLEND_FONT)).astype(np.float32)
    x4 = np.where(m4 & mt4, wfont * x4c + (1 - wfont) * x4t, np.where(m4, x4c, np.where(mt4, x4t, 0.0))).astype(np.float32); m4 = m4 | mt4; del Lt, Lt4, wt4, x4c, x4t
    # V27 (05-09): el detall gran és un passa-alt NOMÉS EN AZIMUT (polar ln r × θ): els arcs
    # concèntrics que Pere va marcar a la V26 (graons HDR i costura de fusió a radis fixos,
    # amplificats a 128-256 px) són variació AL LLARG del raig i un filtre azimutal no els pot
    # veure per construcció; els streamers són variació EN AZIMUT i hi són sencers (research/123
    # mirat del revés). Dues bandes: < 64 px i 64-256 px (en px d'arc a cada radi).
    da, db = passa_alt_azimutal(x4, m4, rad4, RS / 4.0, (16.0, 64.0))     # 64 i 256 px al llenç sencer
    _, dc = passa_alt_azimutal(x4, m4, rad4, RS / 4.0, (64.0, 256.0))     # banda ampla: 256-1024 px d'arc
    da = np.where(m4, da, 0.0).astype(np.float32); db = np.where(m4, db, 0.0).astype(np.float32); dc = np.where(m4, dc, 0.0).astype(np.float32)
    for nm, dd in (("a", da), ("b", db)):
        r_ = f3.suavitza_sn(dd, m4, rad4); dd[...] = (r_[0] if isinstance(r_, tuple) else r_)
    r4 = rad4 / (RS / 4.0)
    fa = (1 - e1.smoothstep(r4, *FADE_GRAN_FI)).astype(np.float32); fb = (1 - e1.smoothstep(r4, *FADE_GRAN_GROS)).astype(np.float32)
    d4 = (da + db).astype(np.float32)                       # per al MAD per anell (sense esvair)
    d4f = (da * fa + db * fb).astype(np.float32); del da, db, fa, fb
    # NRGF complet al detall: cada anell (en ln r, INTERPOLAT — mai per calaix) normalitzat pel seu
    # MAD, perquè els streamers de 3-5 R☉ tinguin la mateixa vara que els d'1,5 R☉ (Druckmüller);
    # amb una sola escala global el p99 el manava el soroll de 6-8 R☉ (esc 0,645) i a 3,5-4,5 R☉
    # l'amplitud quedava a 0,04-0,06. El soroll de >5 R☉ s'esvaeix a l'etapa 4.
    lnr4 = np.log(np.maximum(rad4, 1.0) / (RS / 4.0)); nb = 120
    lo, hi = float(lnr4[m4].min()), float(lnr4[m4].max()); edges = np.linspace(lo, hi, nb + 1); cen = 0.5 * (edges[1:] + edges[:-1])
    idx = np.clip(((lnr4 - lo) / (hi - lo) * nb).astype(np.int32), 0, nb - 1); mad = np.full(nb, np.nan)
    for k in range(nb):
        sel = m4 & (idx == k)
        if sel.sum() > 200: mad[k] = 1.4826 * np.median(np.abs(d4[sel] - np.median(d4[sel])))
    ok = np.isfinite(mad); mad = np.interp(cen, cen[ok], mad[ok]); mad = np.maximum(mad, 0.02)
    mad_terra = float(np.interp(np.log(R_TERRA_MAD), cen, mad)); mad = np.where(cen > np.log(R_TERRA_MAD), np.maximum(mad, mad_terra), mad)
    esc = 3.5 * np.interp(lnr4, cen, mad).astype(np.float32)          # 3,5 MAD → tanh(1) = ±0,38; amb 2 MAD el 6 % de 2,5 R☉ saturava
    y4 = (0.5 + 0.5 * np.tanh(d4f / esc)).astype(np.float32); del d4f
    # --- capa AMPLA (V28): 256-1024 px d'arc, 1,05 → 9,6 R☉, el seu propi MAD per anell amb terra a 6 R☉, guany 1,0 ---
    madc = np.full(nb, np.nan)
    for k in range(nb):
        sel = m4 & (idx == k)
        if sel.sum() > 200: madc[k] = 1.4826 * np.median(np.abs(dc[sel] - np.median(dc[sel])))
    okc = np.isfinite(madc); madc = np.interp(cen, cen[okc], madc[okc]); madc = np.maximum(madc, 0.01)
    madc_terra = float(np.interp(np.log(TERRA_AMPLE), cen, madc)); madc = np.where(cen > np.log(TERRA_AMPLE), np.maximum(madc, madc_terra), madc)
    escc = 3.5 * np.interp(lnr4, cen, madc).astype(np.float32); fc = (1 - e1.smoothstep(r4, *FADE_AMPLE)).astype(np.float32)
    yc4 = (0.5 + 0.5 * np.tanh(dc * fc / escc)).astype(np.float32); del dc, fc
    ycf = cv2.resize(yc4, (W, H), interpolation=cv2.INTER_CUBIC); ycf = np.where(mf & (rad > 1.05 * RS), ycf, 0.5).astype(np.float32)
    r_ = f3.anivella(ycf, rad, mf & (rad > 1.05 * RS)); ycf = (r_[0] if isinstance(r_, tuple) else r_).astype(np.float32)
    pitc, rpc = f3.nivell_per_radi(ycf, rad, mf & (rad > 1.05 * RS), RS); ycf = np.where(mf & (rad > 1.05 * RS), ycf, 0.5).astype(np.float32)
    np.save(os.path.join(CAU, "capa_achf_ample_u16.npy"), (np.clip(ycf, 0, 1) * 65535 + 0.5).astype(np.uint16))
    REB["capa_ample"] = {"banda": "256-1024 px d'arc (azimutal, font híbrida)", "H1_max_abs": float(pitc), "PASSA_H1": bool(float(pitc) <= 0.05), "esvaiment": FADE_AMPLE,
                        "amplitud_p99_per_anell": {str(r): float(np.percentile(np.abs(ycf[mf & (np.abs(rad - r * RS) < 0.05 * RS)] - 0.5), 99)) for r in (1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5)}}
    marca(f"capa AMPLA: {REB['capa_ample']}"); del ycf, yc4
    REB["mad_per_anell_gran"] = {str(round(float(np.exp(c)), 2)): float(v) for c, v in zip(cen[::10], mad[::10])}
    esc = "3,5·MAD per anell (ln r interpolat), terra 0,02"
    y = cv2.resize(y4, (W, H), interpolation=cv2.INTER_CUBIC); y = np.where(md, y, 0.5).astype(np.float32)
    r_ = f3.anivella(y, rad, md); y = (r_[0] if isinstance(r_, tuple) else r_).astype(np.float32)
    pit, r_pitjor = f3.nivell_per_radi(y, rad, md, RS); y = np.where(md, y, 0.5).astype(np.float32)
    np.save(os.path.join(CAU, "capa_achf_gran_u16.npy"), (np.clip(y, 0, 1) * 65535 + 0.5).astype(np.uint16))
    ysat = {str(r): float((((y <= 0.02) | (y >= 0.98)) & md & (np.abs(rad - r * RS) < 0.05 * RS)).sum() / max((md & (np.abs(rad - r * RS) < 0.05 * RS)).sum(), 1)) for r in (1.5, 2.5, 3.5, 4.5)}
    REB["capa_gran"] = {"escala_tanh": esc, "fraccio_saturada_per_anell": ysat, "H1_max_abs": float(pit), "H1_radi_pitjor_Rsol": float(r_pitjor), "PASSA_H1": bool(float(pit) <= 0.05),
                        "amplitud_p99_per_anell": {str(r): float(np.percentile(np.abs(y[md & (np.abs(rad - r * RS) < 0.05 * RS)] - 0.5), 99)) for r in (1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 8.0)}}
    marca(f"capa ACHF gran: {REB['capa_gran']}"); del y, y4, d4, x4, L4, w4, m4, rad4, Lc, Lu
    # --- (c) base amb el cel reduït ---
    ufk = (cf + K_CEL * (uf - cf)).astype(np.float32); del uf, cf
    for i, c in enumerate(comu.CANALS):
        ufk[..., i] = e1.fons_per_raig(ufk[..., i], mf, rad, theta, RS, "k_" + c)
    marca("fons per raig (base k)")
    va = json.load(open(os.path.join(CAU, "rebut_etapa1.json")))["base"]["ancora_va"]
    L = ((ufk[..., 0] + 2.0 * ufk[..., 1] + ufk[..., 2]) / 4.0).astype(np.float32)
    yb = comu.corba_to(L, mf, va, **e1.CORBA_B)
    sigma = 24.0; dn = np.maximum(comu._suau(mf.astype(np.float32), sigma), 1e-6); LS = comu._suau(np.where(mf, L, 0.0), sigma) / dn
    q = np.empty_like(ufk)
    for i in range(3):
        q[..., i] = (comu._suau(np.where(mf, ufk[..., i], 0.0), sigma) / dn) / np.maximum(LS, 1e-9)
    ylin = comu.a_lineal(yb); qmax = q.max(axis=2)
    with np.errstate(divide="ignore", invalid="ignore"):
        wmax = np.where(qmax > 1.0, (1.0 / np.maximum(ylin, 1e-9) - 1.0) / (qmax - 1.0), np.inf)
    wg = np.clip(np.nan_to_num(wmax, nan=0.0, posinf=1.0), 0.0, 1.0).astype(np.float32)
    base = comu.a_srgb(ylin[..., None] * (1.0 + wg[..., None] * (q - 1.0))); base = np.where(mf[..., None], base, 0.0).astype(np.float32)
    np.save(os.path.join(CAU, "base_B_k025_rgb16.npy"), (np.clip(base, 0, 1) * 65535 + 0.5).astype(np.uint16))
    b0 = np.load(os.path.join(CAU, "base_B_rgb16.npy"), mmap_mode="r")
    REB["base_k"] = {"ancora_va": float(va), "nivell_G_mediana": {str(r): [float(np.median(base[..., 1][mf & (np.abs(rad - r * RS) < 0.02 * RS)])), float(np.median(b0[..., 1][mf & (np.abs(rad - r * RS) < 0.02 * RS)]) / 65535.0)] for r in (1.1, 1.5, 2.5, 4.0, 6.0, 8.0)},
                     "nota": "[base k, base etapa 1] · mediana G per anell"}
    REB["fons_per_raig_k"] = e1.REBUT.get("fons_per_raig"); REB["segons"] = time.time() - T0
    json.dump(REB, open(os.path.join(CAU, "rebut_etapa1b.json"), "w"), indent=1, ensure_ascii=False, default=float)
    marca(f"base k feta: {REB['base_k']['nivell_G_mediana']} · FET etapa 1b")


if __name__ == "__main__":
    main()
