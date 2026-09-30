"""a_achf · la capa 51 (ACHF micro 1-16, «04») de la V104 regenerada al LLENÇ SENCER amb el codi de f3_filtres_v98 E3 (ordre 1), només aquesta
capa (σ 1, 2, 4, 8, 16; perfil de contrast del canal G; tanh; sn_smooth amb resolution_sigma; centre_rings global; gaussiana externa 1,5).
Opció --pre snp: l'entrada ln L de la caixa lunar passa per la resolució que segueix el S/N (mitjana_sn, perfil radial intacte, σ × --sn-esc).
Sortida: <OUT>/<nom>/L51_G_moon.npy (u16, caixa lunar)."""
import sys, argparse, time, json, gc; sys.path.insert(0, '/private/tmp/claude_v105/fila')
from comu_fila import *
import numexpr as ne
from v86_operadors import gauss, sn_smooth, centre_rings
ap = argparse.ArgumentParser(); ap.add_argument('nom'); ap.add_argument('--pre', choices=['cap', 'snp'], default='cap'); ap.add_argument('--sn-esc', type=float, default=1.0)
A = ap.parse_args(); OD = OUT / A.nom; OD.mkdir(parents=True, exist_ok=True); t0 = time.time()
def conv_ordre1(a, w, s, ksize, border):   # còpia literal de f3_filtres_v98.conv_ordre1
    k = cv2.getGaussianKernel(ksize, s).astype(np.float64).ravel(); u = (np.arange(ksize) - ksize // 2) / s
    k0 = k.astype(np.float32); k1 = (k * u).astype(np.float32); k2 = (k * u * u).astype(np.float32)
    f = lambda img, kx, ky: cv2.sepFilter2D(img, cv2.CV_32F, kx, ky, borderType=border)
    wf = np.asarray(w, np.float32); aw = (np.asarray(a, np.float32) * wf).astype(np.float32)
    m00 = f(wf, k0, k0); m10 = f(wf, k1, k0); m01 = f(wf, k0, k1); m20 = f(wf, k2, k0); m02 = f(wf, k0, k2); m11 = f(wf, k1, k1)
    b0 = f(aw, k0, k0); b1 = f(aw, k1, k0); b2 = f(aw, k0, k1); del aw
    C00 = ne.evaluate('m20*m02 - m11*m11'); C01 = ne.evaluate('-(m10*m02 - m01*m11)'); C02 = ne.evaluate('m10*m11 - m20*m01')
    det = ne.evaluate('m00*C00 + m10*C01 + m01*C02'); q = ne.evaluate('det / where(m00*m20*m02 > 1e-30, m00*m20*m02, 1e-30)')
    o1 = ne.evaluate('(C00*b0 + C01*b1 + C02*b2) / where(abs(det) > 1e-30, det, 1e-30)'); o0 = ne.evaluate('b0 / where(m00 > 1e-20, m00, 1e-20)')
    out = np.where(q > 0.02, o1, o0).astype(np.float32); return out, q.astype(np.float32)
def normgauss1(a, w, s):
    ks = int(round(s * 4 * 2 + 1)) | 1; return conv_ordre1(np.where(w > 0, a, 0), (w > 0).astype(np.float32) * w, s, ks, cv2.BORDER_REFLECT_101)[0]
I = entrades((0, 0, W, H), lum=True); m, x, good = I['m'], I['x'], I['good']; del I['a']; gc.collect()
rep = dict(nom=A.nom, pre=A.pre, sn_esc=A.sn_esc)
if A.pre == 'snp':
    SN = np.load(OUT / 'SN_MAPA.npz'); sl = (slice(BOXL[1], BOXL[3]), slice(BOXL[0], BOXL[2])); SIGM = SN['sigma'] * A.sn_esc
    x[sl] = np.where(good[sl], mitjana_sn(x[sl], good[sl], SIGM, perfil=True, log=True), x[sl]); rep['pre_sigma_p50_p99'] = np.percentile(SIGM[SIGM > 0], [50, 99]).round(3).tolist()
yy, xx = np.ogrid[:H, :W]; r = np.hypot(yy - CYS, xx - CXS).astype('float32'); del yy, xx
ARX = ARREL / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay'
old = json.loads((ARX / 'v29_profiles_round1/cau/refined_detail_receipt.json').read_text()); p = old['profiles']['1']
var = json.loads((ARX / 'filters_v58_dependencies/fine_variants_receipt.json').read_text())['variants']
scale = np.interp(np.log(np.maximum(r / RS, 1e-5)), p['lnr_centres'], p['robust_contrast']).astype('float32')
w = good.astype(np.float32); acc = np.zeros((H, W), np.float32)
for sig in (1, 2, 4, 8, 16):
    acc += (x - normgauss1(x, w, sig)) / 5; print('σ', sig, f'{time.time() - t0:.0f} s', flush=True)
del x; gc.collect()
sigmamap = np.load(ARREL / '4-RESULTATS/v85_regeneracio_20260922/fixed_inputs/resolution_sigma.npy', mmap_mode='r')
d = np.where(good, acc / scale, 0).astype('float32'); del acc; sc = var['micro1_16']['scale_tanh']
mapped = (.5 * np.tanh(d / max(sc, 1e-6))).astype('float32'); del d; sm = sn_smooth(mapped, m, sigmamap); del mapped; centered, hist = centre_rings(sm, m, r); del sm
aa = np.clip(.5 + centered, 0, 1); aa[~m] = .5; wsup = m.astype('float32'); den = gauss(wsup, 1.5); b = .5 + gauss((aa - .5) * wsup, 1.5) / np.maximum(den, 1e-8); b[~m] = .5
u16 = np.round(np.clip(np.nan_to_num(b, nan=0.5), 0, 1) * 65535).astype(np.uint16)
np.save(OD / 'L51_G_moon.npy', u16[BOXL[1]:BOXL[3], BOXL[0]:BOXL[2]])
v4 = np.load(E / 'estat_v103/L51_G.npy', mmap_mode='r'); dif = np.abs(u16.astype(np.int32) - np.asarray(v4).astype(np.int32))
fora = np.ones((H, W), bool); fora[BOXL[1]:BOXL[3], BOXL[0]:BOXL[2]] = False
rep.update(centre_rings=hist, dif_u16_llenc_max=int(dif.max()), dif_u16_fora_caixa_max=int(dif[fora].max()), dif_u16_fora_caixa_px_gt1=int((dif[fora] > 1).sum()), segons=round(time.time() - t0, 1))
desa(OD / 'A_REBUT.json', rep); print(json.dumps(rep, default=str))
