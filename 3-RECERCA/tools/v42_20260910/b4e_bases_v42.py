"""B4e (V42) · Bases de pantalla amb la corba declarada (recepta EXACTA de la V39 b4e_bases_corbades: k=1 total, k=0,25 cel/4) sobre la fusió V42 SENSE ESTRELLES,
i la capa `Estrelles (llum mesurada)` = corba(fusió amb estrelles) − corba(fusió sense estrelles) en l'espai de pantalla (Linear Dodge la torna a sumar exactament).
Cel per tren de la V29 combinat amb els pesos i el ρ de la fusió V42."""
from comu42 import *
VA = 70736.46875; PEND, ANC, TERRA = 0.22, 0.74, 0.045


def base_srgb(tot, k, m, wv, rho, skv, sks, ms):
    ws = np.where(ms, 1 - wv, 0).astype(np.float32); wv_ = np.where(ms, wv, 1.0).astype(np.float32); mf = m.astype(np.float32); den = gauss(mf, 24)
    data = np.empty((H, W, 3), np.float32)
    for c in range(3):
        T = np.nan_to_num(np.asarray(tot[..., c], np.float32)); cel = wv_ * np.nan_to_num(np.asarray(skv[..., c], np.float32)) + ws * np.nan_to_num(np.asarray(rho[..., c], np.float32)) * np.nan_to_num(np.asarray(sks[..., c], np.float32))
        data[..., c] = np.maximum(T - (1 - k) * cel, 0); del T, cel
    L = (data[..., 0] + 2 * data[..., 1] + data[..., 2]) / 4; tone = comu.corba_to(L, m, VA, pend=PEND, anc=ANC, terra=TERRA); ls = gauss(L * mf, 24) / np.maximum(den, 1e-8)
    q = np.stack([gauss(data[..., i] * mf, 24) / np.maximum(den, 1e-8) / np.maximum(ls, 1e-8) for i in range(3)], axis=2); del data
    ylin = comu.a_lineal(tone); qmax = q.max(axis=2)
    with np.errstate(divide='ignore', invalid='ignore'): wmax = np.where(qmax > 1, (1 / np.maximum(ylin, 1e-8) - 1) / (qmax - 1), 1)
    wg = np.clip(np.nan_to_num(wmax, nan=0, posinf=1), 0, 1); srgb = comu.a_srgb(ylin[..., None] * (1 + wg[..., None] * (q - 1))) * mf[..., None]
    return np.clip(np.nan_to_num(srgb), 0, 1).astype(np.float32), tone


def main():
    m = np.load(CAU42 / 'support_v42.npy'); wv = np.nan_to_num(np.asarray(np.load(CAU42 / 'weight_vixen_v42.npy', mmap_mode='r'), np.float32)); rho = np.load(CAU42 / 'rho_v42.npy', mmap_mode='r')
    skv = np.load(ROOT / 'research/tools/v29/cau_final/vixen_sky.npy', mmap_mode='r'); sks = np.load(ROOT / 'research/tools/v29/cau_final/sony_sky.npy', mmap_mode='r'); ms = np.load(CAUF / 'sony_support.npy')
    tot0 = np.load(CAU42 / 'fusion_total_v42_sense_estrelles.npy', mmap_mode='r'); tot1 = np.load(CAU42 / 'fusion_total_v42.npy', mmap_mode='r'); r, _ = coords(); rep = {}
    for k, nom in ((1.0, 'base_corba_total_v42'), (0.25, 'base_cel4_v42')):
        s0, tone = base_srgb(tot0, k, m, wv, rho, skv, sks, ms); u = np.round(s0 * 65535).astype(np.uint16); np.save(CAU42 / f'{nom}_u16.npy', u)
        prof = [float(np.median(tone[m & (r > a * RS) & (r < (a + 0.2) * RS)])) for a in (1.05, 1.5, 2, 3, 4, 6)]; rep[nom] = {'k': k, 'va': VA, 'pend': PEND, 'anc': ANC, 'terra': TERRA, 'to_mediana_per_radi': prof, 'sha256_u16': sha(CAU42 / f'{nom}_u16.npy')}
        from PIL import Image; Image.fromarray(np.uint8(u[::4, ::4] // 257)).save(VIS42 / f'B4e_{nom}_llenc_sencer.png'); log(f'{nom}: to mediana per radi {prof}')
        if k == 1.0:
            s1, _ = base_srgb(tot1, k, m, wv, rho, skv, sks, ms); d = np.clip(s1 - s0, 0, 1); u2 = np.round(d * 65535).astype(np.uint16); np.save(CAU42 / 'estrelles_llum_mesurada_v42_u16.npy', u2)
            rep['estrelles'] = {'definicio': 'corba(fusió) − corba(fusió sense estrelles), espai de pantalla, Linear Dodge', 'max': float(d.max()), 'px_no_nuls': int((u2 > 0).any(axis=2).sum()), 'sha256_u16': sha(CAU42 / 'estrelles_llum_mesurada_v42_u16.npy')}; log(f"capa estrelles: màx {d.max():.3f}, {rep['estrelles']['px_no_nuls']} px no nuls"); del s1, d, u2
        del s0, tone, u
    savejson(REB42 / 'B4e_bases.json', rep); log('B4e fet')


if __name__ == '__main__':
    main()
