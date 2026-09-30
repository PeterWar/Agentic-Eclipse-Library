"""m_mesura · emula el compost de la V104 (caixa lunar, fins a la 234) amb la 56 i/o la 51 substituïdes i mesura:
 (a) energia fina (1–3 px d'arc) de ln L: pic a l'inici (màx a d 2,5–4 px dalt; DMIN+1…DMIN+3 als altres sectors) contra la mitjana a 5–8 px (i contra 5,75);
 (b) anells/línies: mitjana per arc de ΔL/L contra la V104 a cada fila de 0,25 px (d −1…16), màx |Δ|;
 (c) lupa: energia per escales d'arc 2–16 px a la franja (d 2,5–4) contra fora (6–10), variant i V104;
 (d) detall de fora: rms i màx de ΔL/L a d 8–12, 12–40 i 40–200 px.
Ús: m_mesura.py <variant> [<variant> ...]  (cada variant és una carpeta amb L56_G_moon.npy i/o L51_G_moon.npy)."""
import sys; sys.path.insert(0, '/private/tmp/claude_v105/fila')
from comu_fila import *
CP = Compost(); C4 = CP.c(); L4 = lum(C4)
d_, th_ = dist_theta(BOXL)
def carrega(nom):
    sub = {}
    for lid in (56, 51):
        p = OUT / nom / f'L{lid}_G_moon.npy'
        if p.exists(): sub[lid] = np.load(p).astype(np.float32) / 65535
    return sub
PIC = {'dalt': (2.5, 4.0), 'dalt_esq': (4.75, 6.75), 'baix_esq': (5.5, 7.5), 'dreta': (1.0, 3.0)}      # l'inici: DMIN + 1…3 (DMIN 1,3 · 3,9 · 4,5 · <0)
FORA = {'dalt': (5.0, 8.0), 'dalt_esq': (8.0, 11.0), 'baix_esq': (8.5, 11.5), 'dreta': (4.0, 7.0)}
def mesura(L, Lref):
    res = {}
    for nm in ['dalt', 'dalt_esq', 'baix_esq', 'dreta']:
        s = sec(nm); f = fina(L, s); fr = fina(Lref, s); lo, hi = PIC[nm]; ip = (DG >= lo) & (DG <= hi); io = (DG >= FORA[nm][0]) & (DG <= FORA[nm][1])
        am = arcmean(L, s); ar = arcmean(Lref, s); rel = (am - ar) / np.maximum(ar, 1e-6); rz = (DG >= -1) & (DG <= 16)
        esc = escales(L, s); escr = escales(Lref, s); ib = (DG >= lo) & (DG <= hi); iof = (DG >= FORA[nm][0] + 1) & (DG <= FORA[nm][1] + 2)
        lupa = {k: round(float(esc[k][ib].mean() / esc[k][iof].mean()), 3) for k in esc if k != '0-1'}; lupar = {k: round(float(escr[k][ib].mean() / escr[k][iof].mean()), 3) for k in escr if k != '0-1'}
        res[nm] = dict(pic=round(float(f[ip].max()), 5), d_pic=float(DG[ip][np.argmax(f[ip])]), fora=round(float(f[io].mean()), 5), ratio=round(float(f[ip].max() / f[io].mean()), 3),
                       ratio_v104=round(float(fr[ip].max() / fr[io].mean()), 3), ratio_575=round(float(f[ip].max() / f[id_(5.75)]), 3),
                       anell_max_pct=round(float(100 * np.abs(rel[rz]).max()), 3), anell_d=float(DG[rz][np.argmax(np.abs(rel[rz]))]),
                       lupa_escales_banda_sobre_fora=lupa, lupa_v104=lupar, perfil_fina=[round(float(v), 5) for v in f[(DG >= 0) & (DG <= 12)]])
    dd = d_; rel2 = (L - Lref) / np.maximum(Lref, 1e-6)
    res['fora'] = {f'{a}-{b}': dict(rms_pct=round(float(100 * np.sqrt(np.mean(rel2[(dd >= a) & (dd < b)] ** 2))), 4), max_pct=round(float(100 * np.abs(rel2[(dd >= a) & (dd < b)]).max()), 3)) for a, b in [(8, 12), (12, 40), (40, 200), (200, 700)]}
    return res
if __name__ == '__main__':
    tot = {}
    for nom in sys.argv[1:]:
        sub = carrega(nom); C = CP.c(sub); L = lum(C); np.save(OUT / nom / 'COMP_emul.npy', C.astype(np.float32)); r = mesura(L, L4); tot[nom] = r
        desa(OUT / nom / 'MESURA.json', r)
        print(f'### {nom} (capes {sorted(sub)})')
        for nm in ['dalt', 'dalt_esq', 'baix_esq', 'dreta']:
            q = r[nm]; print(f"  {nm:9s} pic {q['pic']:.4f}@{q['d_pic']:.2f} fora {q['fora']:.4f} ràtio {q['ratio']:.3f} (V104 {q['ratio_v104']:.3f}; /5,75 {q['ratio_575']:.3f}) · anell màx {q['anell_max_pct']:.3f} % @ {q['anell_d']:.2f} · lupa {q['lupa_escales_banda_sobre_fora']} (V104 {q['lupa_v104']})")
        print('  fora:', r['fora'])
