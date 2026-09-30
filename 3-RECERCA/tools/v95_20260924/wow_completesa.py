"""WOW sobre el domini amb PES DE COMPLETESA per escala (V95, 24-09-2026). Norma canònica: res inventat ni reflectit.
Per què: a la V94 (wow_domini + neutralitza) la WOW calculada només amb dada tenia, arran del limbe, un biaix de nivell a les escales gruixudes
(16–128 px): a la vora de la dada el nucli només veu un costat, i la corona hi té un perfil corbat. Es va treure DESPRÉS, restant de la sortida un
perfil coherent al llarg de l'arc fins a 120 px, i això va deixar un anell amb arcs: marques lila i verdes de Pere a 1-PHOTOSHOP/WOW.psb.
Ara el biaix no es produeix. A cada escala s, la contribució d'un píxel es pesa per la COMPLETESA del seu nucli (fracció de pes B3 amb dada):
w_s = smoothstep(completesa_s, C0, C1). Arran del limbe hi queden les escales fines (la textura, que sí que té dada als dos costats) i les
gruixudes s'apaguen gradualment. Sense cap correcció posterior. El suavitzat de cada escala continua sent d'ordre 1 on el suport és incomplet."""
import numpy as np, time, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'v94_20260924'))
from wow_domini import conv_pla, nconv, b3conv, smoothstep
def wow_completesa(a, m, n_esc=8, bilateral=False, C0=0.80, C1=0.97, log=print):
    c = np.where(m, a, 0).astype(np.float32); out = np.zeros_like(c); mf = m.astype(np.float32); pesos = []
    for s in range(n_esc):
        t0 = time.time(); nxt, _ = conv_pla(c, m, s, bilateral); nxt = np.where(m, nxt, 0).astype(np.float32)
        wave = np.where(m, c - nxt, 0).astype(np.float32); wave[np.abs(wave) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(c), np.abs(nxt))] = 0
        amp = np.sqrt(np.maximum(nconv(wave * wave, m, s), 1e-20)); compl = b3conv(mf, s); w = smoothstep(compl, C0, C1).astype(np.float32)
        out += np.where(m, w * wave / amp, 0); c = nxt; pesos.append(w)
        log(f"  WOW{' bilateral' if bilateral else ''} (completesa) escala {s} · {time.time() - t0:.0f} s")
    return np.where(m, out, np.nan).astype(np.float32), pesos

def ng_pes(x, w, s):
    """Mitjana local normalitzada amb pesos w (σ gaussiana s)."""
    import cv2
    num = cv2.GaussianBlur((x * w).astype(np.float32), (0, 0), s); den = cv2.GaussianBlur(w.astype(np.float32), (0, 0), s)
    return num / np.maximum(den, 1e-6)
def wow_completesa_neutra(a, m, n_esc=8, bilateral=False, log=print):
    """Com wow_completesa, però (1) llindar de completesa per escala (suau a les fines, estricte a les gruixudes: el biaix del perfil corbat creix
    amb la mida del nucli) i (2) cada escala blanquejada es fa de mitjana local nul·la (σ = 4·2^s, mínim 8 px, només amb dada i pes de completesa)
    abans de sumar-la: la capa és detall de nivell neutre per construcció, sense cap correcció posterior d'anell ni de vora."""
    c = np.where(m, a, 0).astype(np.float32); out = np.zeros_like(c); mf = m.astype(np.float32); pesos = []
    for s in range(n_esc):
        t0 = time.time(); nxt, _ = conv_pla(c, m, s, bilateral); nxt = np.where(m, nxt, 0).astype(np.float32)
        wave = np.where(m, c - nxt, 0).astype(np.float32); wave[np.abs(wave) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(c), np.abs(nxt))] = 0
        amp = np.sqrt(np.maximum(nconv(wave * wave, m, s), 1e-20)); g = np.where(m, wave / amp, 0).astype(np.float32)
        C0, C1 = 0.45 + 0.05 * s, 0.75 + 0.03 * s; w = (smoothstep(b3conv(mf, s), C0, C1) * mf).astype(np.float32)
        g = g - ng_pes(g, w, max(8.0, 4.0 * 2 ** s)); out += np.where(m, w * g, 0); c = nxt; pesos.append(w)
        log(f"  WOW{' bilateral' if bilateral else ''} (completesa, neutra per escala) escala {s} · {time.time() - t0:.0f} s")
    return np.where(m, out, np.nan).astype(np.float32), pesos
