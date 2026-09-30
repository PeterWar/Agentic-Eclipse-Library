"""B4e (V41) · Segona RHEF amb un paràmetre PUBLICAT diferent: la funció «upsilon» de la implementació de referència (sunkit-image `rhef`, Gilly & Cranmer 2025),
que la V38 no aplicava (rang lineal, υ = None). υ és una gamma de dos costats sobre la imatge equalitzada: per sota de la mediana y = (2x)^υ / 2, per sobre
y = 1 − (2 − 2x)^υ / 2 (codi de referència: `sunkit_image.utils.apply_upsilon`, amb el punt de tall a la mitjana de la imatge). Amb υ = 0,35 (valor per defecte de
la referència) TOT valor s'acosta a 0,5 (x < mid puja, x > mid baixa: quantils 1/10/90/99 % 0,016/0,151/0,925/0,999 → 0,151/0,329/0,743/0,945): en Superposar, on l'efecte
d'una capa és proporcional a (a − 0,5), la P02b és una RHEF MÉS FEBLE pertot (la meitat d'amplitud al gruix); el pendent només és > 1 dins de l'1–10 % més fosc i més
brillant (x < 0,099 i el simètric), o sigui que el contrast LOCAL creix només a les cues. Salt inherent al punt de tall (mitjana 0,532, no 0,5): +0,00045 (30 nivells u16)
sobre la isolínia de rang 0,532, el que fa la referència; en Superposar al 5 % són ~4 nivells de 65535 a la base. S'aplica sobre la RHEF FLOAT de la V38 (mateix rang continu, mateixes vores): cap píxel nou de rang."""
from comu41 import *
PC38 = ROOT / 'research/tools/v38_20260908/purs/cau'; UPS = float(sys.argv[1]) if len(sys.argv) > 1 else 0.35


def apply_upsilon(x, ups, mid):
    lo = x < mid; out = np.full_like(x, np.nan)
    out[lo] = ((2 * x[lo]) ** ups) / 2; hi = ~lo & np.isfinite(x); out[hi] = 1 - ((2 - 2 * x[hi]) ** ups) / 2; return out


def main():
    f = np.load(PC38 / 'P02_RHEF_float.npy', mmap_mode='r'); u = np.load(PC38 / 'P02_RHEF_u16.npy', mmap_mode='r'); x = np.asarray(f, np.float32); m = np.isfinite(x)
    mid = float(np.nanmean(x)); log(f'RHEF V38: suport {int(m.sum()):,} px · mitjana (punt de tall de la referència) {mid:.4f} · mediana {float(np.nanmedian(x)):.4f}')
    y = apply_upsilon(np.clip(x, 0, 1), UPS, mid).astype(np.float32); y16 = np.where(m, np.round(np.clip(y, 0, 1) * 65535), np.asarray(u)).astype(np.uint16)
    # comprovacions: monòtona, mateixos extrems, i quant es mou la meitat central
    q = np.nanpercentile(x, [1, 10, 25, 50, 75, 90, 99]); qy = apply_upsilon(q.astype(np.float32), UPS, mid)
    rep = dict(upsilon=UPS, mid=mid, quantils_x=q.tolist(), quantils_y=qy.tolist(), fora_suport='valor u16 de la P02 V38 (idèntic)', font_float=str(PC38 / 'P02_RHEF_float.npy'), font_float_sha256=sha(PC38 / 'P02_RHEF_float.npy'), referencia='sunkit_image.utils.apply_upsilon (Gilly & Cranmer 2025), υ escalar → alpha = alpha_high = υ')
    log('quantils 1/10/25/50/75/90/99 %: x ' + ' '.join(f'{v:.3f}' for v in q) + ' → y ' + ' '.join(f'{v:.3f}' for v in qy))
    np.save(CAU39 / f'P02b_RHEF_ups{UPS:g}_u16.npy', y16); np.save(CAU39 / f'P02b_RHEF_ups{UPS:g}_float.npy', np.where(m, y, np.nan).astype(np.float32)); rep['u16'] = str(CAU39 / f'P02b_RHEF_ups{UPS:g}_u16.npy'); rep['u16_sha256'] = sha(Path(rep['u16']))
    savejson(REB41 / 'B4e_rhef_upsilon.json', rep); log('B4e fet ' + rep['u16'])


if __name__ == '__main__':
    main()
