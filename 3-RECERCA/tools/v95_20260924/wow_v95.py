"""WOW de la V95 (24-09-2026). Norma canònica: res inventat ni reflectit; només es trien veïns, mai es copien valors.
On el suport és complet, l'operador és EXACTAMENT el de sempre (v86_operadors.wow / bilateral_conv: nucli B3 à trous 5×5, pes de rang per toc,
potència local amb nconv): lluny de les vores de la dada la V95 és la V94 i la V93. Només canvia a la vora de la dada:
  1. PARELLS: un toc (dy, dx) compta només si el seu simètric (−dy, −dx) també té dada. El suport queda simètric i la mitjana local no s'inclina
     cap a un costat (el biaix d'un sol costat era el que la V94 restava després i li feia els anells).
  2. VORA DIFUMINADA DE LA LLUNA (d < 12 px del limbe): la Lluna difuminada aplana i doblega el perfil radial dels primers píxels (a molts azimuts
     la brillantor puja fins a d 4–8 i després baixa). Un parell que hi toca només compta si els seus dos tocs són a la mateixa distància del limbe que
     el centre (al llarg de l'arc): allà la Lluna els afecta igual. Pes suau: max(1 − smoothstep(|Δd|, 0,5, 1,5), smoothstep(d_min, 4, 12)).
     La zona es mesura des de la CRESTA de la dada a cada azimut (on la brillantor de la vora difuminada fa el màxim: d 3–4 a la dreta, 5–7 a
     l'esquerra): d es desplaça max(0, cresta − 2) px (dmap_vora). Amb la zona fixa, a l'esquerra la cresta quedava fora i en sortien línies
     paral·leles al limbe a 5–11 px (les de la V88, més fluixes).
  3. Pes de completesa (fracció del nucli B3 en parells vàlids) NOMÉS a les escales ≥ 3, i estricte (entra de 0,95 a 0,995): amb el suport
     incomplet, els tocs que queden van al llarg de l'arc i, per la curvatura de la Lluna, cauen més lluny del Sol (a l'escala 6, fins a 15 px
     més enfora), on la corona és més fosca: l'escala surt clara allà on s'engega (era l'arc clar de les marques liles, +0,02 a 80–120 px).
     Les escales fines 0–2 hi són senceres mentre quedi algun parell (textura fins a la vora).
  3b. La potència local per blanquejar cada escala és la de l'original (nconv, tots els tocs amb dada): és una variància i no li cal simetria;
     amb només els parells, a la primera filera de dada quedaven 2–4 tocs i la textura sortia pigada.
  4. NIVELL: la bilateral dona a cada escala una mitjana positiva que creix amb el pendent de la corona (el pes de rang afavoreix el costat de
     fora, més pla). A les escales fines 0–2 és petita i es treu amb UNA constant per a tot el llenç (mitjana on el suport és complet). A les
     escales gruixudes (≥ 3) fa un altiplà clar prop del Sol que s'apagaria arran de la Lluna, on aquestes escales encara no hi entren: cada
     escala gruixuda es fa de mitjana local nul·la a 4 vegades la seva mida (σ = 4·2^s px, ponderada amb el seu pes). És part de l'operador,
     escala per escala, no una correcció del resultat.
Cap correcció posterior local (ni mitjana local, ni anell restat)."""
import numpy as np, numexpr as ne, time, cv2
K = np.array([1, 4, 6, 4, 1], np.float32) / 16
TAPS = [(dy, dx) for dy in range(-2, 3) for dx in range(-2, 3)]
def _refl(n, idx):
    idx = np.mod(idx, 2 * n); return np.where(idx < n, idx, 2 * n - 1 - idx)
def smoothstep(x, lo, hi):
    q = np.clip((x - lo) / (hi - lo), 0, 1); return q * q * (3 - 2 * q)
def conv_v95(a, m, dmap, s, bilateral, wave=None, d_a=4.0, d_b=12.0, iso=(0.5, 1.5), ret_rad=False):
    """Sense wave: retorna (suavitzat, completesa). Amb wave: retorna la potència local de wave amb els mateixos pesos geomètrics."""
    h, w = a.shape; d = 2 ** s; out = np.zeros_like(a); compl = np.zeros_like(a); radf = np.ones_like(a)
    for y0 in range(0, h, 128):
        y1 = min(h, y0 + 128); ctr = a[y0:y1]; mc = m[y0:y1]; dc = dmap[y0:y1]
        V, VAL, D = {}, {}, {}
        for dy, dx in TAPS:
            iy = _refl(h, np.arange(y0, y1) + dy * d)[:, None]; ix = _refl(w, np.arange(w) + dx * d); VAL[(dy, dx)] = m[iy, ix]; D[(dy, dx)] = dmap[iy, ix]
            V[(dy, dx)] = (wave if wave is not None else a)[iy, ix]
        G = {}; GR = {}
        for t in TAPS:
            u = (-t[0], -t[1])
            if t == (0, 0): G[t] = mc.astype(np.float32); GR[t] = np.zeros_like(G[t]); continue
            if u in G: G[t] = G[u]; GR[t] = GR[u]; continue
            pv = VAL[t] & VAL[u] & mc; Dt, Du = D[t], D[u]
            f = ne.evaluate('where(dmn >= db, 1.0, 0.0)', local_dict=dict(dmn=np.minimum(dc, np.minimum(Dt, Du)), db=d_b)).astype(np.float32)
            parcial = f < 1; fr = f.copy()
            if parcial.any():
                iso_w = 1 - smoothstep(np.maximum(np.abs(Dt - dc), np.abs(Du - dc)), iso[0], iso[1]); rad = smoothstep(np.minimum(dc, np.minimum(Dt, Du)), d_a, d_b)
                f = np.where(parcial, np.maximum(iso_w, rad), 1).astype(np.float32); fr = np.where(parcial, rad, 1).astype(np.float32)
            G[t] = (f * pv).astype(np.float32); GR[t] = (np.minimum(fr, f) * pv).astype(np.float32)
        if wave is not None:
            num = np.zeros_like(ctr); ks = np.zeros_like(ctr)
            for (dy, dx) in TAPS:
                k = float(K[dy + 2] * K[dx + 2]); g = G[(dy, dx)]; x = V[(dy, dx)]; num += ne.evaluate('k*g*x*x'); ks += k * g
            out[y0:y1] = num / np.maximum(ks, 1e-20); continue
        if bilateral:   # variància local del pes de rang, com v86_operadors.bilateral_conv, sobre els tocs vàlids (pes geomètric)
            mo = np.zeros_like(ctr); mo2 = np.zeros_like(ctr); ma = np.zeros_like(ctr)
            for (dy, dx) in TAPS:
                k = float(K[dy + 2] * K[dx + 2]); g = G[(dy, dx)]; dl = np.where(g > 0, V[(dy, dx)] - ctr, 0); mo += k * g * dl; mo2 += k * g * dl * dl; ma += k * g
            mean = mo / np.maximum(ma, 1e-20); vv = np.maximum(mo2 / np.maximum(ma, 1e-20) - mean * mean, 1e-20)
        num = np.zeros_like(ctr); den = np.zeros_like(ctr); ks = np.zeros_like(ctr); kr = np.zeros_like(ctr); kn = np.zeros_like(ctr)
        for (dy, dx) in TAPS:
            k = float(K[dy + 2] * K[dx + 2]); g = G[(dy, dx)]; v = np.where(g > 0, V[(dy, dx)], 0); kr += k * GR[(dy, dx)]; kn += (k * g) if (dy, dx) != (0, 0) else 0
            wt = ne.evaluate('k*g*exp(-0.5*(ctr-v)**2/vv)') if bilateral else (k * g)
            num += wt * (v - ctr); den += wt; ks += k * g
        out[y0:y1] = ctr + num / np.maximum(den, 1e-20); compl[y0:y1] = ks; radf[y0:y1] = np.where(kn > 0, kr / np.maximum(kn, 1e-20), 0)   # sense el toc central
    return (out, compl, radf) if ret_rad else (out, compl)
def desplacament_cresta(G, dom, box, cx, cy, R, NT=1440, sig_graus=3.0, dmax=10.0):
    """Cresta de ln G (franja d'un instant) a cada azimut: argmax a d ∈ [0, dmax] del perfil mitjà al llarg de l'arc (σ 3°, només dada).
    Retorna (desplaçament per calaix d'azimut = clip(cresta − 2, 0, 8), suavitzat σ 2°; la cresta)."""
    from scipy.ndimage import gaussian_filter1d
    y0, x0 = box; DR = 0.25; DS = np.arange(0.0, dmax + 1e-6, DR); TS = np.radians((np.arange(NT) + 0.5) * 360 / NT); TT, DD = np.meshgrid(TS, DS)
    PX = (cx + (R + DD) * np.cos(TT) - x0).astype(np.float32); PY = (cy - (R + DD) * np.sin(TT) - y0).astype(np.float32)
    L = np.where(dom, np.log(np.maximum(G, 1e-9)), 0).astype(np.float32); P = cv2.remap(L, PX, PY, cv2.INTER_LINEAR); V = cv2.remap(dom.astype(np.float32), PX, PY, cv2.INTER_LINEAR)
    V = (V > 0.999).astype(np.float32); sg = sig_graus / (360 / NT)
    num = gaussian_filter1d(P * V, sg, axis=1, mode='wrap'); den = gaussian_filter1d(V, sg, axis=1, mode='wrap'); prof = np.where(den > 0.2, num / np.maximum(den, 1e-6), -np.inf)
    cresta = DS[np.argmax(prof, axis=0)]; off = gaussian_filter1d(np.clip(cresta - 2.0, 0, 8), 2.0 / (360 / NT), mode='wrap')
    return off.astype(np.float32), cresta.astype(np.float32)
def dmap_vora(dmap, xx, yy, cx, cy, off):
    """Distància al limbe menys el desplaçament de la cresta del seu azimut (només a d < 60 px; més enllà, la distància real)."""
    NT = len(off); t = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; o = off[(t / 360 * NT).astype(int) % NT]
    return np.where(dmap < 60, dmap - o, dmap).astype(np.float32)
def b3conv(a, s):
    d = 2 ** s; a = np.ascontiguousarray(a, np.float32); h, w = a.shape; tmp = np.zeros_like(a)
    for kk, kv in zip(range(-2, 3), K): tmp += kv * a[_refl(h, np.arange(h) + kk * d)]
    out = np.zeros_like(a)
    for kk, kv in zip(range(-2, 3), K): out += kv * tmp[:, _refl(w, np.arange(w) + kk * d)]
    return out
def nconv(a, m, s):
    """La potència local de l'original (v86_operadors.nconv): tots els tocs amb dada. Una variància no necessita simetria."""
    return b3conv(np.where(m, a, 0), s) / np.maximum(b3conv(m.astype(np.float32), s), 1e-20)
def ng_pes(x, w, s):
    num = cv2.GaussianBlur((x * w).astype(np.float32), (0, 0), s); den = cv2.GaussianBlur(w.astype(np.float32), (0, 0), s); return num / np.maximum(den, 1e-6)
def wow_v95(a, m, dmap, n_esc=8, bilateral=False, log=print, llindar=lambda s: (0.95, 0.995), mus=None, local_des=3, pot_tots=True, sig_local=lambda s: 4.0 * 2 ** s, iso=(0.5, 1.5), centra_rad=False, sig_rad=lambda s: max(32.0, 4.0 * 2 ** s)):
    """mus: constants de centratge per escala (si None, es mesuren aquí on la completesa és ≥ 0,999). Retorna (wow, pesos, mus)."""
    c = np.where(m, a, 0).astype(np.float32); out = np.zeros_like(c); pesos = []; mus_out = []
    for s in range(n_esc):
        t0 = time.time(); nxt, compl, radf = conv_v95(c, m, dmap, s, bilateral, iso=iso, ret_rad=True); nxt = np.where(m, nxt, 0).astype(np.float32)
        wave = np.where(m, c - nxt, 0).astype(np.float32); wave[np.abs(wave) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(c), np.abs(nxt))] = 0
        pot = nconv(wave * wave, m, s) if pot_tots else conv_v95(c, m, dmap, s, False, wave=wave, iso=iso)[0]
        g = np.where(m & (compl > 0), wave / np.sqrt(np.maximum(pot, 1e-20)), 0).astype(np.float32)
        if s >= 3: C0, C1 = llindar(min(s, 7)); w = (smoothstep(compl, C0, C1) * m).astype(np.float32)
        else: w = (m & (compl > 0)).astype(np.float32)
        mu = float(np.mean(g[m & (compl >= 0.999)], dtype=np.float64)) if mus is None else float(mus[s]); mus_out.append(mu); g = g - mu
        if centra_rad: g = g - radf * ng_pes(g, w * radf, sig_rad(s))
        elif s >= local_des: g = g - ng_pes(g, w, sig_local(s))
        out += w * g; c = nxt; pesos.append(w)
        log(f"  WOW{' bilateral' if bilateral else ''} V95 escala {s} · mitjana {mu:+.4f} · {time.time() - t0:.0f} s")
    return np.where(m, out, np.nan).astype(np.float32), pesos, mus_out
