#!/usr/bin/env python3
"""porta_estrelles.py · Porta de les estrelles (Claude, 28-09-2026, per encàrrec de Pere: «posa els guardrails necessaris a la skill perquè això
no torni a passar»). Només lectura. Comprova el PSB EFECTIU i els seus renders natius del Photoshop:

  E1 INVENTARI. Cada estrella pintada (pics de les capes visibles en mode additiu, fora de 2 radis lunars) ha de ser una estrella ACCEPTADA:
     o bé del catàleg acceptat de la versió (--cataleg; per defecte S22_final_catalog.json, criteri congelat de la V65), o bé d'un fitxer --acceptacions-noves amb rebut complet: SNR total ≥ 8,
     ≥ 2 conjunts independents (apuntaments o instruments) amb SNR ≥ 4 cadascun, flux MESURAT (mai tret de la magnitud de catàleg),
     ≥ 300 controls mesurats igual i cap control acceptat. I a la inversa: cap estrella acceptada no pot faltar.
  E2 DOBLE LLUM. Al render SENSE les capes d'estrelles, a la posició de cada estrella pintada no hi pot haver cap estrella: la mateixa llum
     no es pot comptar dues vegades (la pintada i la real que queda a la base). Llindar: S/N ≤ max(5, p99,5 dels controls).
  E3 FANTASMES. Si es dona --model-fantasmes (F2_REBUT.json: desplaçament d'un tren respecte del cel), a les posicions previstes de les
     còpies desplaçades el render sense estrelles no pot ser més brillant que al MATEIX desplaçament girat 90/180/270° al voltant de la
     mateixa estrella (Wilcoxon aparellat, p ≥ 0,01), ni tenir cap S/N > 5.
  E4 CAPA NETA. Cap capa additiva visible pot ser opaca i negra fora de les estrelles (> 1 % del llenç amb alfa efectiva i sense llum): fa opac
     el document i canvia el limbe. Amb --anterior, el compost no pot perdre el canal de transparència.
  E5 REFERÈNCIES. Cada capa amb «Brno» al nom ha d'estar encaixada per les ESTRELLES (mai només per la corona): desplaçament medià
     ≤ 5 px de llenç respecte de les estrelles acceptades (amb ≥ 5 estrelles mesurables; si no, «NO AVALUABLE», que s'ha de declarar).

Ús (des de l'arrel del projecte, amb el Python de l'entorn):
  porta_estrelles.py --psb 1-PHOTOSHOP/V114.psb --render-sense-estrelles <visible_complet.tif amb les capes d'estrelles amagades>
                     [--anterior 1-PHOTOSHOP/V113.psb] [--acceptacions-noves noves.json] [--model-fantasmes F2_REBUT.json] [--sortida rebut.json]
El render sense estrelles es fa amb `3-RECERCA/tools/v112_claude_20260928/r5_render.sh <psb> <carpeta> "<ids de les capes d'estrelles>"`.
Surt amb codi 1 si alguna porta falla. Proves negatives reals: la V113 del migdia (E2, E5), la V113 amb la 413 opaca (E4) i la V113 amb
les 4 Tycho sense acceptació (E1). Vegeu el §1i de la SKILL.md."""
import argparse, hashlib, json, struct, sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB  # noqa: E402

LLUNA = (5375.79, 3775.98, 452.98)          # centre i radi de la Lluna de presentació (px del llenç)
ADDITIUS = {'LINEAR_DODGE', 'SCREEN', 'COLOR_DODGE'}   # modes que SUMEN llum (Aclarir/LIGHTEN no suma: la 76 de Pere hi va)
S22 = ROOT / '4-RESULTATS/v65_pere_estrelles_20260914/S22_final_catalog.json'


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
    return h.hexdigest()


def canals_compost(p):
    with open(p, 'rb') as f: return struct.unpack('>H', f.read(26)[12:14])[0]


def lum(rgb): return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def llum_efectiva(p, L):
    """Contribució de la capa additiva (lluminància × alfa efectiva × opacitat) al llenç sencer, i l'alfa efectiva."""
    H, W = 7506, 10551
    rgb = []; org = None
    for c in (0, 1, 2):
        a, org = p.channel(L['id'], c); rgb.append(a.astype(np.float32))
    x0, y0 = org; h, w = rgb[0].shape
    al = np.ones((h, w), np.float32)
    if -1 in L['chans']: al = p.channel(L['id'], -1)[0].astype(np.float32) / 65535
    if L.get('mask') and -2 in L['chans'] and not L['mask'].get('disabled'):
        m, (mx, my) = p.channel(L['id'], -2); M = np.full((H, W), L['mask'].get('background', 0) / 255.0, np.float32)
        ya, xa = max(my, 0), max(mx, 0); yb, xb = min(my + m.shape[0], H), min(mx + m.shape[1], W)   # la màscara pot sortir del llenç
        M[ya:yb, xa:xb] = m[ya - my:yb - my, xa - mx:xb - mx].astype(np.float32) / 65535; al = al * M[y0:y0 + h, x0:x0 + w]
    al = al * L['opacity'] / 255.0
    E = np.zeros((H, W), np.float32); A = np.zeros((H, W), np.float32)
    E[y0:y0 + h, x0:x0 + w] = lum(np.stack(rgb, -1)) * al; A[y0:y0 + h, x0:x0 + w] = al
    return E, A, (np.stack(rgb, -1).max(-1) > 0)


def pics(E, llindar=1000.0):
    H, W = E.shape; yy, xx = np.nonzero((E == ndi.maximum_filter(E, size=11)) & (E > llindar))
    r = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) / LLUNA[2]; k = r > 2.0
    return [(float(x), float(y), float(E[y, x])) for x, y in zip(xx[k], yy[k])]


YY, XX = np.mgrid[-12:13, -12:13]; RR = np.hypot(XX, YY); NUC = RR < 3; ANELL = (RR >= 8) & (RR < 12)


def snr_punt(L, x, y):
    ix, iy = int(round(x)), int(round(y)); H, W = L.shape
    if not (12 <= ix < W - 12 and 12 <= iy < H - 12): return None
    w = L[iy - 12:iy + 13, ix - 12:ix + 13]; bg = float(np.median(w[ANELL])); s = 1.4826 * float(np.median(np.abs(w[ANELL] - bg)))
    return float((w[NUC].max() - bg) / max(s, 1.0))


def controls(L, evita, n=1500, llavor=11):
    """Estadístic S/N a posicions aleatòries fora de 2 radis lunars i a > 30 px de qualsevol estrella coneguda."""
    rng = np.random.default_rng(llavor); H, W = L.shape; ev = np.array(evita) if evita else np.zeros((0, 2)); out = []
    while len(out) < n:
        x, y = rng.uniform(40, W - 40), rng.uniform(40, H - 40)
        if np.hypot(x - LLUNA[0], y - LLUNA[1]) < 2 * LLUNA[2]: continue
        if len(ev) and np.min(np.hypot(ev[:, 0] - x, ev[:, 1] - y)) < 30: continue
        s = snr_punt(L, x, y)
        if s is not None: out.append(s)
    return np.array(out)


def valida_nova(s):
    conj = [c for c in s.get('conjunts', []) if c.get('snr', 0) >= 4]
    ok = (s.get('snr_total', 0) >= 8 and len(conj) >= 2 and s.get('flux_font') == 'mesurat'
          and s.get('n_controls', 0) >= 300 and s.get('controls_acceptats', 1) == 0)
    return ok, dict(snr_total=s.get('snr_total'), conjunts_amb_snr4=len(conj), flux_font=s.get('flux_font'),
                    n_controls=s.get('n_controls'), controls_acceptats=s.get('controls_acceptats'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--psb', required=True); ap.add_argument('--render-sense-estrelles', required=True)
    ap.add_argument('--anterior'); ap.add_argument('--acceptacions-noves'); ap.add_argument('--cataleg', help='catàleg acceptat de la versió (JSON amb «stars» [{id,x,y}]); per defecte, el S22 de la V65'); ap.add_argument('--model-fantasmes'); ap.add_argument('--sortida')
    a = ap.parse_args()
    psb = Path(a.psb).resolve(); p = PSB(str(psb)); out = dict(psb=str(psb), sha256=sha(psb), portes={})
    cat = Path(a.cataleg) if a.cataleg else S22; dc = json.loads(cat.read_text()); out['cataleg'] = dict(fitxer=str(cat), sha256=sha(cat), retirades=dc.get('retirades', []))
    acc = [dict(id=s['id'], x=s['x'], y=s['y'], font=cat.name) for s in dc['stars']]
    if a.acceptacions_noves:
        for s in json.loads(Path(a.acceptacions_noves).read_text()):
            ok, det = valida_nova(s)
            if ok: acc.append(dict(id=s['id'], x=s['x'], y=s['y'], font='acceptació nova'))
            out.setdefault('acceptacions_noves', []).append(dict(id=s['id'], valida=ok, **det))
    AX = np.array([[s['x'], s['y']] for s in acc])

    # E1 + E4: capes additives visibles
    E_tot = np.zeros((7506, 10551), np.float32); capes = []; e4 = []
    for L in p.layers:
        if not L['visible'] or L['blend'] not in ADDITIUS: continue
        E, A, llum = llum_efectiva(p, L); E_tot += E
        fosc_opac = float(((A > 0) & ~llum).mean()) if llum.shape == A.shape else float(((A > 0) & (E == 0)).mean())
        capes.append(dict(id=L['id'], nom=L['name'], mode=L['blend'])); e4.append(dict(id=L['id'], nom=L['name'], fraccio_opaca_sense_llum=round(fosc_opac, 5)))
    pintades = []
    for x, y, v in sorted(pics(E_tot), key=lambda t: -t[2]):          # un pic per estrella (un sostre pla en dona dos)
        if all(np.hypot(x - u, y - w) > 3 for u, w, _ in pintades): pintades.append((x, y, v))
    sense_acc, casades = [], set()
    for x, y, v in pintades:
        d = np.hypot(AX[:, 0] - x, AX[:, 1] - y); k = int(np.argmin(d))
        if d[k] <= 2.5: casades.add(k)
        else: sense_acc.append(dict(x=round(x, 1), y=round(y, 1), pic=round(v)))
    falten = [acc[k]['id'] for k in range(len(acc)) if k not in casades and np.hypot(acc[k]['x'] - LLUNA[0], acc[k]['y'] - LLUNA[1]) > 2 * LLUNA[2]]
    out['portes']['E1_inventari'] = dict(PASSA=not sense_acc and not falten, capes_additives=capes, estrelles_pintades=len(pintades),
                                         pintades_sense_acceptacio=sense_acc, acceptades_que_falten=falten)
    e4_ok = all(c['fraccio_opaca_sense_llum'] <= 0.01 for c in e4); det4 = dict(capes=e4)
    if a.anterior:
        ca, cn = canals_compost(Path(a.anterior)), canals_compost(psb); det4['canals_compost'] = dict(anterior=ca, ara=cn); e4_ok = e4_ok and cn >= ca
    out['portes']['E4_capa_neta'] = dict(PASSA=e4_ok, **det4)

    # E2 (+ E3): render sense les capes d'estrelles
    import tifffile
    R = lum(tifffile.imread(a.render_sense_estrelles).astype(np.float32))
    nul = controls(R, [(s['x'], s['y']) for s in acc] + [(x, y) for x, y, _ in pintades])
    llindar = max(5.0, float(np.percentile(nul, 99.5)))
    dobles = []
    for x, y, v in pintades:
        s = snr_punt(R, x, y)
        if s is not None and s > llindar: dobles.append(dict(x=round(x, 1), y=round(y, 1), snr=round(s, 2)))
    out['portes']['E2_doble_llum'] = dict(PASSA=not dobles, llindar=round(llindar, 2), controls=dict(n=len(nul), p50=round(float(np.median(nul)), 2),
                                          p99_5=round(float(np.percentile(nul, 99.5)), 2)), estrelles_amb_estrella_a_sota=dobles)
    if a.model_fantasmes:
        m = json.loads(Path(a.model_fantasmes).read_text())['model']; c = m['coef']
        # desplaçament del tren = semblança respecte del Sol: dx = c0·u − c1·v + c2, dy = c1·u + c0·v + c3 (u, v relatius al Sol)
        sol = (5361.77, 3775.75); st = []
        for s in acc:
            u, v = s['x'] - sol[0], s['y'] - sol[1]; dx = c[0] * u - c[1] * v + c[2]; dy = c[1] * u + c[0] * v + c[3]
            if np.hypot(dx, dy) < 7: continue                      # a < 7 px, dins del disc de l'estrella pintada
            sn = snr_punt(R, s['x'] + dx, s['y'] + dy)
            # control aparellat: el MATEIX desplaçament girat 90°, 180° i 270° al voltant de la mateixa estrella (la vora de l'estrella i dels
            # filtres hi pesa igual; només un fantasma prefereix la direcció del model)
            ctl = [snr_punt(R, s['x'] + cx, s['y'] + cy) for cx, cy in ((-dy, dx), (-dx, -dy), (dy, -dx))]
            ctl = [c for c in ctl if c is not None]
            if sn is not None and ctl: st.append(dict(id=s['id'], dx=round(dx, 1), dy=round(dy, 1), snr=round(sn, 2), control=round(float(np.mean(ctl)), 2)))
        v = np.array([t['snr'] for t in st]); cv = np.array([t['control'] for t in st])
        pw = float(wilcoxon(v - cv, alternative='greater').pvalue) if len(v) >= 5 else None
        out['portes']['E3_fantasmes'] = dict(PASSA=bool((pw is None or pw >= 0.01) and (len(v) == 0 or v.max() <= 5)), n=len(st),
                                             snr_mediana=round(float(np.median(v)), 2) if len(v) else None,
                                             control_aparellat_mediana=round(float(np.median(cv)), 2) if len(cv) else None, p_wilcoxon=pw,
                                             controls_aleatoris_p50=round(float(np.median(nul)), 2), mes_brillants=sorted(st, key=lambda t: -t['snr'])[:6])
    else:
        out['portes']['E3_fantasmes'] = dict(PASSA=None, nota='sense --model-fantasmes: no avaluada (cal mesurar el registre de cada tren contra el cel)')

    # E5: capes de Brno encaixades per estrelles
    e5 = []
    for L in p.layers:
        if 'Brno' not in L['name']: continue
        G, (x0, y0) = p.channel(L['id'], 1); G = G.astype(np.float32); A = p.channel(L['id'], -1)[0] if -1 in L['chans'] else None
        RAD = 45; d = []
        for s in acc:
            cx, cy = s['x'] - x0, s['y'] - y0; ix, iy = int(round(cx)), int(round(cy))
            if not (RAD + 40 <= ix < G.shape[1] - RAD - 40 and RAD + 40 <= iy < G.shape[0] - RAD - 40): continue
            if A is not None and A[iy, ix] < 65000: continue
            w = G[iy - RAD - 30:iy + RAD + 31, ix - RAD - 30:ix + RAD + 31]; bg = np.median(w); c = w[30:-30, 30:-30] - bg
            mad = 1.4826 * np.median(np.abs(w - bg)) + 1e-6
            if c.max() < 6 * mad: continue
            lab, _ = ndi.label(c > 0.5 * c.max()); mm = lab == lab[np.unravel_index(np.argmax(c), c.shape)]; yy, xx = np.nonzero(mm); wt = c[mm]
            d.append(float(np.hypot((xx * wt).sum() / wt.sum() - RAD + ix - cx, (yy * wt).sum() / wt.sum() - RAD + iy - cy)))
        med = float(np.median(d)) if d else None
        e5.append(dict(id=L['id'], nom=L['name'], estrelles=len(d), desplacament_medià_px=round(med, 2) if med is not None else None,
                       veredicte='NO AVALUABLE' if len(d) < 5 else ('PASSA' if med <= 5 else 'FALLA')))
    out['portes']['E5_referencies'] = dict(PASSA=all(c['veredicte'] != 'FALLA' for c in e5), capes=e5)

    ok = all(v['PASSA'] is not False for v in out['portes'].values()); out['veredicte'] = 'PASSA' if ok else 'FALLA'
    txt = json.dumps(out, indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    if a.sortida: Path(a.sortida).write_text(txt)
    print(txt); sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
