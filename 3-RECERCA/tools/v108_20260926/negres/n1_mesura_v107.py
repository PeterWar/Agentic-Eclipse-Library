"""n1 (V108 · negres) · (1) Zones negres a la V107 (màscares noves de Pere a la 41 i la 56, la 54 MGN en Multiplicar 13) i atribució per capa:
amagant-les d'una en una i en grups. Llenç sencer a pas 2 (5276×3753), sense les capes d'ajust 239–244.
Definicions (les de la consulta del 26-09, per continuïtat):
  global : fracció de 1,3–4,5 R☉ més fosca que la mediana del cel a > 7 R☉ dins del marc final;
  local  : fracció més fosca que el cel del MATEIX sector de 10° a 6,5–8,5 R☉ (en la mateixa variant);
  local_suau : el mateix amb L i el cel suavitzats σ 3 px (6 px del llenç): «zones» visibles, no gra d'un píxel.
També: el mateix mesurat sobre el compost FUSIONAT del PSB (el que Pere veu, amb les capes d'ajust), per saber quant hi afegeixen.
Sortida: 4-RESULTATS/v108_20260926/negres/N1_V107.json i pas2/L_<variant>.npy"""
import sys, time, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_negres import *
d2 = OUT / 'pas2'; d2.mkdir(exist_ok=True)
BOX = (0, 0, W, H); PAS = 2
G = mascares(BOX, PAS); r, th, ok, marc = G['r'], G['th'], G['ok'], G['marc']; okm = ok & marc
np.savez_compressed(d2 / 'geom_pas2.npz', r=r, th=th, ok=ok, marc=marc)


def zones(L):
    cel = float(np.median(L[okm & (r > 7)])); cv, sky = cel_local(L, r, th, ok)
    Ls = cv2.GaussianBlur(L, (0, 0), 3.0); _, skys = cel_local(Ls, r, th, ok)
    out = dict(cel_global=cel, cel_sectors_10=[float(v) for v in cv])
    for nom, (a, b) in {'1.3-4.5': (1.3, 4.5), '1.3-2': (1.3, 2), '2-3': (2, 3), '3-4.5': (3, 4.5)}.items():
        m = okm & (r >= a) & (r < b)
        out[nom] = dict(global_=float((L[m] < cel).mean()), local=float((L[m] < sky[m]).mean()), local_marge_5pc=float((L[m] < 0.95 * sky[m]).mean()),
                        local_suau=float((Ls[m] < skys[m]).mean()), mediana_L=float(np.median(L[m])))
    m = okm & (r >= 1.3) & (r < 4.5)
    out['1.3-4.5']['local_per_sector_45'] = {f'{s}-{s + 45}': float((L[m & (th >= s) & (th < s + 45)] < sky[m & (th >= s) & (th < s + 45)]).mean()) for s in range(0, 360, 45)}
    out['1.3-4.5']['local_suau_per_sector_45'] = {f'{s}-{s + 45}': float((Ls[m & (th >= s) & (th < s + 45)] < skys[m & (th >= s) & (th < s + 45)]).mean()) for s in range(0, 360, 45)}
    # quant de fosc: dèficit mitjà relatiu dels píxels negres
    neg = m & (L < sky); out['1.3-4.5']['deficit_mitja_rel'] = float(np.mean(1 - L[neg] / sky[neg])) if neg.any() else 0.0
    # cel: gradient entre sectors (màx/mín del cel local)
    out['cel_max_sobre_min'] = float(np.max(cv) / np.min(cv))
    return out, sky, skys, Ls


if __name__ == '__main__':
    t = time.time(); P = Pila(BOX, PAS); print('carrega', round(time.time() - t, 1), flush=True)
    V = {'V107': {}, 'sense_filtres': {k: 'oculta' for k in FILTRES}}
    for k in FILTRES: V[f'menys{k}'] = {k: 'oculta'}
    for k in (41, 42, 54, 56, 45, 46, 51, 55): V[f'nomes{k}'] = {j: 'oculta' for j in FILTRES if j != k}
    V['menys_NRGF'] = {41: 'oculta', 42: 'oculta'}
    V['menys_NRGF_56'] = {41: 'oculta', 42: 'oculta', 56: 'oculta'}
    V['menys_NRGF_54'] = {41: 'oculta', 42: 'oculta', 54: 'oculta'}
    V['menys_NRGF_54_56'] = {41: 'oculta', 42: 'oculta', 54: 'oculta', 56: 'oculta'}
    V['menys_MULT'] = {j: 'oculta' for j in (54, 41, 42, 45, 46)}
    V['menys_OVER'] = {j: 'oculta' for j in (47, 49, 51, 55, 56)}
    V['menys_RHEF_locals'] = {45: 'oculta', 46: 'oculta'}
    V['nomes_NRGF'] = {j: 'oculta' for j in FILTRES if j not in (41, 42)}
    V['nomes_NRGF_56'] = {j: 'oculta' for j in FILTRES if j not in (41, 42, 56)}
    res = {}; negres = {}
    for nom, esp in V.items():
        t = time.time(); L = P.compon(esp); np.save(d2 / f'L_{nom}.npy', L)
        z, sky, skys, Ls = zones(L); res[nom] = z
        if nom in ('V107', 'menys_NRGF', 'menys56', 'menys_NRGF_56', 'menys54', 'menys_NRGF_54_56', 'sense_filtres'):
            negres[nom] = okm & (r >= 1.3) & (r < 4.5) & (L < sky)
        print(nom, round(time.time() - t, 1), 'local', round(z['1.3-4.5']['local'], 4), 'suau', round(z['1.3-4.5']['local_suau'], 4), 'global', round(z['1.3-4.5']['global_'], 4), flush=True)
    # atribució píxel a píxel dels negres (local) de la V107
    n0 = negres['V107']; tot = int(n0.sum())
    att = dict(total_px=tot,
               desapareixen_sense_NRGF=float((n0 & ~negres['menys_NRGF']).sum() / tot),
               desapareixen_sense_56=float((n0 & ~negres['menys56']).sum() / tot),
               desapareixen_sense_54=float((n0 & ~negres['menys54']).sum() / tot),
               nomes_sense_56_no_sense_NRGF=float((n0 & negres['menys_NRGF'] & ~negres['menys56']).sum() / tot),
               nomes_sense_NRGF_i_56_alhora=float((n0 & negres['menys_NRGF'] & negres['menys56'] & ~negres['menys_NRGF_56']).sum() / tot),
               persisteixen_sense_NRGF_54_56=float((n0 & negres['menys_NRGF_54_56']).sum() / tot),
               persisteixen_sense_filtres=float((n0 & negres['sense_filtres']).sum() / tot))
    res['atribucio_pixel_V107'] = att; print(att, flush=True)
    np.save(d2 / 'negres_V107_local.npy', n0)
    # el compost fusionat del PSB (el que veu Pere, amb les capes d'ajust)
    import struct
    psb = R0 / '1-PHOTOSHOP/V107.psb'
    with open(psb, 'rb') as f:
        hdr = f.read(26); nch = struct.unpack('>H', hdr[12:14])[0]
        n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); n = struct.unpack('>Q', f.read(8))[0]; f.seek(n, 1)
        pos = f.tell(); cmp_ = struct.unpack('>H', f.read(2))[0]
    if cmp_ == 0:
        mm = np.memmap(psb, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, H, W))
        C = np.stack([np.asarray(mm[c, ::PAS, ::PAS], np.float32) / 65535 for c in range(3)], -1); Lf = lum(C); np.save(d2 / 'L_V107_fusionat_psb.npy', Lf)
        z, sky, _, _ = zones(Lf); res['V107_fusionat_psb_amb_ajustos'] = z
        print('fusionat', z['1.3-4.5']['local'], z['1.3-4.5']['local_suau'], z['1.3-4.5']['global_'], flush=True)
        L7 = np.load(d2 / 'L_V107.npy'); m = okm & (r >= 1.3) & (r < 4.5)
        res['fusionat_vs_emulat'] = dict(corr_ln=float(np.corrcoef(np.log(np.maximum(Lf[m], 1e-3)), np.log(np.maximum(L7[m], 1e-3)))[0, 1]),
                                         coincidencia_negres_local=float(((Lf < sky) & n0)[m].sum() / max(1, (n0[m]).sum())))
    else: res['V107_fusionat_psb_amb_ajustos'] = f'compressio {cmp_}: no llegit'
    desa(OUT / 'N1_V107.json', res); print('FET')
