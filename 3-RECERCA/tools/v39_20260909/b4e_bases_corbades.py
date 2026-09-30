"""B4e (V39) · Bases de PANTALLA amb la corba declarada (recepta EXACTA de v29/build_canvas.new_tone): data = k·TOTAL + (1−k)·CORONA,
L = (R+2G+B)/4, corba B (comu.corba_to: pend 0,22, àncora 0,74 a va = 70736,47 (V29), terra 0,045) sobre L, color local conservat (q = ratios
suavitzats 24 px, dessaturació wg on cal per no retallar) → sRGB u16. k = 1: '00 Base corba (total) · V39' (principal, com recomana Codex);
k = 0,25: '00 Base (cel/4) · V39' (alternativa estètica que Pere feia servir de la V32). CORONA = TOTAL − cel, amb el cel per tren de la V29
(cau_final vixen_sky/sony_sky, la descomposició per color) combinat amb els pesos i el ρ de la fusió V38: cel = wv·cel_V + ws·ρ·cel_S.
Sobre la fusió V38 (idèntica a la V39: la V39 només canvia filtres)."""
from comu39 import *
VA = 70736.46875; PEND, ANC, TERRA = 0.22, 0.74, 0.045


def main():
    m = np.load(CAU38 / 'support_v38.npy'); tot = np.load(CAU38 / 'fusion_total_v38.npy', mmap_mode='r'); wv = np.nan_to_num(np.asarray(np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r'), np.float32))
    rho = np.load(CAU38 / 'rho_v38.npy', mmap_mode='r'); skv = np.load(ROOT / 'research/tools/v29/cau_final/vixen_sky.npy', mmap_mode='r'); sks = np.load(ROOT / 'research/tools/v29/cau_final/sony_sky.npy', mmap_mode='r')
    ms = np.load(CAUF / 'sony_support.npy'); ws = np.where(ms, 1 - wv, 0).astype(np.float32); wv_ = np.where(ms, wv, 1.0).astype(np.float32)
    mf = m.astype(np.float32); den = gauss(mf, 24); rep = {}
    for k, nom in ((1.0, 'base_corba_total_v39'), (0.25, 'base_cel4_v39')):
        data = np.empty((H, W, 3), np.float32)
        for c in range(3):
            T = np.nan_to_num(np.asarray(tot[..., c], np.float32)); cel = wv_ * np.nan_to_num(np.asarray(skv[..., c], np.float32)) + ws * np.nan_to_num(np.asarray(rho[..., c], np.float32)) * np.nan_to_num(np.asarray(sks[..., c], np.float32))
            data[..., c] = np.maximum(T - (1 - k) * cel, 0); del T, cel
        L = (data[..., 0] + 2 * data[..., 1] + data[..., 2]) / 4
        tone = comu.corba_to(L, m, VA, pend=PEND, anc=ANC, terra=TERRA)
        ls = gauss(L * mf, 24) / np.maximum(den, 1e-8)
        q = np.stack([gauss(data[..., i] * mf, 24) / np.maximum(den, 1e-8) / np.maximum(ls, 1e-8) for i in range(3)], axis=2); del data
        ylin = comu.a_lineal(tone); qmax = q.max(axis=2)
        with np.errstate(divide='ignore', invalid='ignore'):
            wmax = np.where(qmax > 1, (1 / np.maximum(ylin, 1e-8) - 1) / (qmax - 1), 1)
        wg = np.clip(np.nan_to_num(wmax, nan=0, posinf=1), 0, 1)
        srgb = comu.a_srgb(ylin[..., None] * (1 + wg[..., None] * (q - 1))) * mf[..., None]
        u = np.round(np.clip(np.nan_to_num(srgb), 0, 1) * 65535).astype(np.uint16); np.save(CAU39 / f'{nom}_u16.npy', u)
        r, t = coords(); rq = r / RS; prof = {f'{a}': float(np.median(tone[m & (rq > a) & (rq < a + 0.1)])) for a in (1.05, 1.5, 2.0, 3.0, 4.0, 6.0)}
        rep[nom] = {'k': k, 'va': VA, 'pend': PEND, 'anc': ANC, 'terra': TERRA, 'to_mediana_per_radi': prof, 'sha256_u16': sha(CAU39 / f'{nom}_u16.npy')}
        from PIL import Image; Image.fromarray(np.uint8(u[::4, ::4] // 257)).save(VIS39 / f'B4e_{nom}_llenc_sencer.png'); log(f'{nom}: to mediana per radi {prof}'); del L, tone, q, ylin, srgb, u
    savejson(REB39 / 'B4e_bases_corbades.json', rep); log('B4e fet')


if __name__ == '__main__':
    main()
