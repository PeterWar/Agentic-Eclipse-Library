"""P2b (V42) · Rotació del POWAAAH3 respecte del llenç, mesurada bé (la corona interior hi és saturada i la correlació de P2 no era una detecció: pic = nul).
 (a) CORONA EXTERIOR: anell on el POWAAAH3 no satura ni és cel pla (percentils de G entre 5 i 90 % del rang), perfils polars de ln G passa-alt en azimut, correlació
     circular contra la fusió V38 al mateix anell normalitzat (R☉ del POWAAAH3 = RS·escala); CONTROL NUL: el mateix contra el perfil de la fusió MIRALLAT en azimut.
 (b) MARS DE LA LLUNA: el disc del POWAAAH3 (remostrejat a l'escala del llenç, passa-alt σ 6 px) contra la capa `Compara LROC` de la V39 (mateixa Lluna, mateixa
     libració), escombrada de rotació −180…180° a 0,25°, amb nul mirallat. Les dues han de coincidir. Sortida: REB42/P2b_rotacio.json (angle final per a P2)."""
from comu42 import *
import tifffile
from scipy.ndimage import map_coordinates, gaussian_filter, rotate
from psd_tools import PSDImage
SRC = Path('/Users/USUARI/Desktop/POWAAAH3.tif'); RL = 455.5; MOON = (CX + 14.8, CY + 0.9)


def polar_prof(img, cx, cy, r0, r1, nr=48, nth=1440):
    th = np.linspace(0, 2 * np.pi, nth, endpoint=False); rs = np.linspace(r0, r1, nr); R, T = np.meshgrid(rs, th, indexing='ij')
    v = map_coordinates(img, [cy + R * np.sin(T), cx + R * np.cos(T)], order=1, mode='nearest'); v = v - gaussian_filter(v, (0, 40), mode='wrap'); return v


def corr_az(a, b):
    Fa = np.fft.rfft(a, axis=1); Fb = np.fft.rfft(b, axis=1); cc = np.fft.irfft(Fa * np.conj(Fb), n=a.shape[1], axis=1).sum(axis=0) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12)
    k = int(np.argmax(cc)); return (k * 360.0 / a.shape[1] + 180) % 360 - 180, float(cc[k]), float(np.sort(cc)[-2]), cc


def main():
    P = json.loads((REB42 / 'P2_powaaah.json').read_text()); cxm, cym, Rm, esc = P['disc']['cx'], P['disc']['cy'], P['disc']['R'], P['escala_pow_per_llenc']
    with tifffile.TiffFile(SRC) as t: img = t.pages[0].asarray()
    g = img[..., 1].astype(np.float32); RSp = RS * esc
    # (a) on no satura: perfil radial de percentils de G al voltant del disc
    rr = np.arange(1.0, 6.0, 0.1); p95 = []; p50 = []
    th = np.linspace(0, 2 * np.pi, 720, endpoint=False)
    for q in rr:
        v = map_coordinates(g, [cym + q * RSp * np.sin(th), cxm + q * RSp * np.cos(th)], order=1, mode='nearest'); p95.append(np.percentile(v, 95)); p50.append(np.percentile(v, 50))
    p95 = np.array(p95); p50 = np.array(p50); ok = (p95 < 64000) & (p50 > 0.05 * 65535); rin = float(rr[ok][0]) if ok.any() else 2.0; rout = min(rin + 1.2, float(rr[ok][-1]) if ok.any() else 3.2)
    log(f'POWAAAH3: satura fins a {rr[p95 >= 64000][-1] if (p95 >= 64000).any() else 0:.1f} R☉; anell útil per a la corona {rin:.1f}–{rout:.1f} R☉')
    F = np.load(CAU38 / 'fusion_total_v38.npy', mmap_mode='r'); fg = np.log(np.maximum(np.nan_to_num(np.asarray(F[..., 1], np.float32)), 1)); pg = np.log(np.maximum(g, 1))
    pa = polar_prof(pg, cxm, cym, rin * RSp, rout * RSp); pb = polar_prof(fg, CX, CY, rin * RS, rout * RS)
    angA, valA, secA, cc = corr_az(pa, pb); angN, valN, _, _ = corr_az(pa, pb[:, ::-1])
    log(f'(a) corona {rin:.1f}–{rout:.1f} R☉: rotació {angA:+.2f}° pic {valA:.3f} (segon pic {secA:.3f}) · NUL mirallat: pic {valN:.3f}')
    # (b) mars: disc del POWAAAH3 a l'escala del llenç (sense rotació) contra la capa LROC de la V39
    psd = PSDImage.open('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V39.psb'); L = next(l for l in psd if l.name == 'Compara LROC'); a = L.numpy(); lb = L.bbox
    lroc = a[..., :3].mean(-1).astype(np.float32); la = a[..., 3] if a.shape[2] > 3 else np.ones_like(lroc); hl, wl = lroc.shape; ccx, ccy = MOON[0] - lb[0], MOON[1] - lb[1]
    np.save(CAU42 / 'lroc_capa_v39_rgba.npy', a); log(f'capa LROC: {lroc.shape} bbox {lb}; centre lunar a la capa ({ccx:.1f}, {ccy:.1f}); alfa mitjana {la.mean():.2f}')
    # disc del POWAAAH3 remostrejat a l'escala del llenç, centrat al disc, sense rotació, mida = la de la capa LROC
    yy, xx = np.mgrid[0:hl, 0:wl].astype(np.float32); px = cxm + esc * (xx - ccx); py = cym + esc * (yy - ccy); pd = cv2.remap(g, px, py, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    d = np.hypot(xx - ccx, yy - ccy); inn = d < 0.93 * RL
    def hp(z): z = np.log(np.maximum(z, 1)); return np.where(inn, z - gaussian_filter(z, 6), 0) * (d < 0.93 * RL)
    A_ = hp(pd); B_ = np.where(inn, np.log(np.maximum(lroc, 1e-3)) - gaussian_filter(np.log(np.maximum(lroc, 1e-3)), 6), 0)
    angs = np.arange(-180, 180, 0.25); best = []
    for ang in angs:
        Br = rotate(B_, ang, reshape=False, order=1); best.append(float((A_ * Br)[inn].sum() / (np.linalg.norm(A_[inn]) * np.linalg.norm(Br[inn]) + 1e-12)))
    best = np.array(best); k = int(np.argmax(best)); angB, valB = float(angs[k]), float(best[k]); second = float(np.sort(best)[-2 - 8]) if len(best) > 10 else float('nan')
    nulB = []
    for ang in angs[::4]:
        Br = rotate(B_[:, ::-1], ang, reshape=False, order=1); nulB.append(float((A_ * Br)[inn].sum() / (np.linalg.norm(A_[inn]) * np.linalg.norm(Br[inn]) + 1e-12)))
    log(f'(b) mars vs LROC: pic a {angB:+.2f}° {valB:.3f} (mediana de la corba {np.median(best):+.3f}, màxim del nul mirallat {max(nulB):.3f})')
    # coherència: la rotació que porta el POWAAAH3 al llenç és la mateixa als dos: a la LROC la rotació és la que cal aplicar a la LROC per igualar el POW → el POW→llenç és −angB
    rot_pow_llenc_b = -angB; log(f'rotació POWAAAH3→llenç: corona {angA:+.2f}°, mars {rot_pow_llenc_b:+.2f}° (diferència {((angA - rot_pow_llenc_b + 180) % 360) - 180:+.2f}°)')
    savejson(REB42 / 'P2b_rotacio.json', dict(anell_corona=[rin, rout], corona=dict(angle=angA, pic=valA, segon=secA, nul_mirallat=valN), mars=dict(angle_pow_llenc=rot_pow_llenc_b, pic=valB, nul_mirallat_max=max(nulB), mediana=float(np.median(best))), lroc_bbox=list(lb))); log('P2b fet')


if __name__ == '__main__':
    main()
