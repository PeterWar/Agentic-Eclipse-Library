#!/usr/bin/env python3
"""Bounded, read-only source pilot. All output must be under its --out directory.

No project modules are imported. Native observed G is the unmodified carrier.
A small log-luminance residual is measured tangentially to a D21 contour proxy.
Every polar interpolation requires all four source pixels; every smoothing
kernel requires complete observed support. Unsupported residual is exactly zero.
This is not a new base, edge correction, calibrated radiance, or PSB delivery.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter1d, minimum_filter1d
from scipy.special import erf


def digest(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def contour(theta, coef, radius, cx, cy):
    e = np.full_like(theta, coef[0], dtype=np.float64)
    e1 = np.zeros_like(theta, dtype=np.float64)
    e2 = np.zeros_like(theta, dtype=np.float64)
    for k in (1, 2):
        a, b = coef[2*k-1:2*k+1]
        z = k * theta
        e += a * np.cos(z) + b * np.sin(z)
        e1 += k * (-a*np.sin(z) + b*np.cos(z))
        e2 -= k*k * (a*np.cos(z) + b*np.sin(z))
    r = radius + e
    ct, st = np.cos(theta), np.sin(theta)
    x, y = cx+r*ct, cy-r*st
    tx, ty = e1*ct-r*st, -e1*st-r*ct
    ax, ay = (e2-r)*ct-2*e1*st, -(e2-r)*st-2*e1*ct
    speed = np.hypot(tx, ty)
    nx, ny = -ty/speed, tx/speed
    return x, y, tx, ty, ax, ay, nx, ny, speed


def strict_remap(a, valid, mx, my, wrap_x=False):
    """Bilinear interpolation, with explicit eligibility of all four pixels.

    Array values at ineligible locations never influence a returned sample.
    wrap_x is periodic physical azimuth, not reflection or missing-data filling.
    """
    h, w = a.shape
    x0, y0 = np.floor(mx).astype(np.int32), np.floor(my).astype(np.int32)
    inside = (y0 >= 0) & (y0+1 < h)
    if wrap_x:
        ix0, ix1 = x0 % w, (x0+1) % w
    else:
        inside &= (x0 >= 0) & (x0+1 < w)
        ix0, ix1 = np.clip(x0, 0, w-1), np.clip(x0+1, 0, w-1)
    iy0, iy1 = np.clip(y0, 0, h-1), np.clip(y0+1, 0, h-1)
    ok = inside & valid[iy0, ix0] & valid[iy0, ix1] & valid[iy1, ix0] & valid[iy1, ix1]
    fx, fy = mx-x0, my-y0
    values = ((1-fx)*(1-fy)*a[iy0, ix0] + fx*(1-fy)*a[iy0, ix1]
              + (1-fx)*fy*a[iy1, ix0] + fx*fy*a[iy1, ix1])
    return np.where(ok, values, 0).astype(np.float32), ok


class TangentOperator:
    def __init__(self, valid, box, centre, coef, sigmas, gain, cap, nt, dstep, dmax):
        self.valid = valid
        self.sigmas, self.gain, self.cap = sigmas, gain, cap
        self.box, self.centre, self.coef = box, centre, coef
        y0, y1, x0, x1 = box
        cx, cy, R = centre
        yy, xx = np.mgrid[y0:y1, x0:x1]
        theta = np.mod(np.arctan2(-(yy-cy), xx-cx), 2*np.pi)
        for _ in range(5):
            x, y, tx, ty, ax, ay, nx, ny, speed = contour(theta, coef, R, cx, cy)
            f = (xx-x)*tx + (yy-y)*ty
            fp = -(tx*tx+ty*ty) + (xx-x)*ax + (yy-y)*ay
            theta -= np.clip(f/np.minimum(fp, -1e-9), -.05, .05)
        theta %= 2*np.pi
        x, y, tx, ty, ax, ay, nx, ny, speed = contour(theta, coef, R, cx, cy)
        self.dnormal = ((xx-x)*nx + (yy-y)*ny).astype(np.float32)
        self.theta = theta.astype(np.float32)
        self.dcircle = (np.hypot(xx-cx, yy-cy)-R).astype(np.float32)
        self.pa_circle = np.mod(np.degrees(np.arctan2(-(yy-cy), xx-cx)), 360)
        # Uniform contour arc-length, with analytic normal offsets.
        tdense = np.linspace(0, 2*np.pi, 65537)
        sp = contour(tdense, coef, R, cx, cy)[-1]
        sdense = np.r_[0, np.cumsum((sp[:-1]+sp[1:])*.5*np.diff(tdense))]
        self.length = float(sdense[-1])
        self.arc = np.interp(theta, tdense, sdense).astype(np.float32)
        self.ds = self.length/nt
        tg = np.interp(np.arange(nt)*self.ds, sdense, tdense)
        x, y, tx, ty, ax, ay, nx, ny, speed = contour(tg, coef, R, cx, cy)
        self.dg = np.arange(-8, dmax+dstep*.5, dstep, dtype=np.float32)
        self.mx = (x[None, :]+self.dg[:, None]*nx[None, :]-x0).astype(np.float32)
        self.my = (y[None, :]+self.dg[:, None]*ny[None, :]-y0).astype(np.float32)
        self.bx = (self.arc/self.ds).astype(np.float32)
        self.by = ((self.dnormal-self.dg[0])/dstep).astype(np.float32)
        _, self.polar_valid = strict_remap(np.zeros_like(valid, dtype=np.float32), valid, self.mx, self.my)
        # Complete support prevents one-sided means. Unit circle approximation
        # changes sigma by the normal-offset circumference, recorded in receipt.
        self.row_scale = 1+self.dg/float(R+coef[0])
        self.kernel_valid = self.polar_valid.copy()
        self.row_radii = []
        for i, scale in enumerate(self.row_scale):
            rad = int(4*max(sigmas)/(self.ds*scale)+.5)
            self.row_radii.append(rad)
            self.kernel_valid[i] &= minimum_filter1d(self.polar_valid[i].astype(np.uint8), 2*rad+1, mode='wrap') > 0
        _, self.native_eligible = strict_remap(np.zeros_like(self.polar_valid, dtype=np.float32), self.kernel_valid, self.bx, self.by, wrap_x=True)
        self.native_eligible &= valid & (self.dnormal >= -6) & (self.dnormal <= dmax-1)

    def apply(self, log_native):
        p, pv = strict_remap(log_native, self.valid, self.mx, self.my)
        residual = np.zeros_like(p)
        for i, scale in enumerate(self.row_scale):
            row = p[i]
            sm = sum(gaussian_filter1d(row, s/(self.ds*scale), mode='wrap', truncate=4)
                     for s in self.sigmas)/len(self.sigmas)
            residual[i] = np.where(self.kernel_valid[i], row-sm, 0)
        r, ok = strict_remap(residual, self.kernel_valid, self.bx, self.by, wrap_x=True)
        ok &= self.native_eligible
        r = np.where(ok, r, 0).astype(np.float32)
        correction = self.gain*self.cap*np.tanh(r/self.cap)
        out = np.asarray(log_native, np.float32)+correction
        # Native base retained exactly where enhancement has no eligible support.
        return out, r, correction


def fit_phase(delta, ph, selected):
    n = int(selected.sum())
    if n < 80:
        return {'n': n, 'unavailable': True}
    pp, yy = ph[selected].astype(float), delta[selected].astype(float)
    X = np.stack([np.ones(n), np.cos(pp), np.sin(pp)], axis=1)
    co = np.linalg.lstsq(X, yy, rcond=None)[0]
    err = yy-X@co
    return dict(n=n, amplitude=float(np.hypot(co[1], co[2])), cosine=float(co[1]),
                sine=float(co[2]), phase_deg=float(np.degrees(np.arctan2(co[2], co[1]))),
                rmse=float(np.sqrt(np.mean(err*err))), offset=float(co[0]))


def statistics(values, selected):
    v = values[selected]
    if len(v) == 0:
        return {'n': 0}
    return {'n': int(len(v)), 'median': float(np.median(v)), 'rms': float(np.sqrt(np.mean(v*v))),
            'abs_p95': float(np.percentile(abs(v), 95)), 'abs_max': float(abs(v).max())}


def panel_image(panels, path, title):
    w, h = 700, 700
    im = Image.new('RGB', (w*len(panels), h+70), '#17191d')
    draw = ImageDraw.Draw(im)
    draw.text((15, 9), title, fill='white')
    for i, (name, arr) in enumerate(panels):
        if arr.ndim == 2:
            a = np.repeat(arr[..., None], 3, axis=-1)
        else:
            a = arr
        thumb = Image.fromarray(np.uint8(np.clip(a, 0, 1)*255)).resize((w, h), Image.Resampling.LANCZOS)
        im.paste(thumb, (i*w, 70))
        draw.text((i*w+15, 42), name, fill='white')
    im.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path('/Users/USUARI/Desktop/Eclipse 2026'))
    ap.add_argument('--npz', type=Path)
    ap.add_argument('--contour', type=Path)
    ap.add_argument('--out', type=Path, default=Path('/private/tmp/v105_filter_pilot_20260926'))
    ap.add_argument('--sigmas', type=float, nargs='+', default=[1., 2., 4.])
    ap.add_argument('--gain', type=float, default=.35)
    ap.add_argument('--cap', type=float, default=.1)
    ap.add_argument('--epsilon', type=float, default=.01)
    ap.add_argument('--nt', type=int, default=8192)
    ap.add_argument('--dstep', type=float, default=.5)
    ap.add_argument('--dmax', type=float, default=65)
    args = ap.parse_args()
    args.out = args.out.resolve()
    assert str(args.out).startswith('/private/tmp/v105_filter_pilot_20260926'), 'pilot output boundary'
    args.out.mkdir(parents=True, exist_ok=True)
    source = args.npz or args.root/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A3C_franja_silueta.npz'
    sil = args.contour or args.root/'4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz'
    q = np.load(source)
    contourq = np.load(sil)
    g = np.asarray(q['G'], np.float32)
    valid = np.asarray(q['domini'], bool) & np.isfinite(g) & (g > 0)
    base = np.where(valid, np.log(np.maximum(g, 1e-30)), 0).astype(np.float32)
    box, centre = [int(x) for x in q['box']], np.asarray(q['centre'], float)
    start = time.monotonic()
    op = TangentOperator(valid, box, centre, contourq['coef'], args.sigmas, args.gain,
                         args.cap, args.nt, args.dstep, args.dmax)
    baseline, residual, correction = op.apply(base)
    dv = op.dcircle-np.maximum(q['DMIN'], 0)[(op.pa_circle/360*len(q['DMIN'])).astype(int) % len(q['DMIN'])]
    bands = [(0,.5),(.5,1),(1,2),(2,3),(3,5),(5,8),(8,12),(15,30)]
    sectors = {'all': np.ones_like(valid), 'top_60_130': (op.pa_circle >= 60)&(op.pa_circle < 130),
               'left_130_230': (op.pa_circle >= 130)&(op.pa_circle < 230)}
    evalmask = valid & (op.dnormal > -4) & (op.dnormal < 45)
    report = {'source': str(source), 'source_sha256': digest(source), 'contour': str(sil), 'contour_sha256': digest(sil),
              'script_sha256': digest(Path(__file__)), 'parameters': vars(args).copy(), 'box': box, 'centre': centre.tolist(),
              'scope': 'PROTOTYPE ONLY. Existing E domain retained. No new base, no radiometric edge correction, no Photoshop composition.',
              'contour_convention': 'D21 order-2 coefficients about E presentation centre and radius. Proxy; not a newly validated contour or anchor.',
              'units': 'dnormal: normal distance to contour proxy; dv: radial distance beyond E DMIN domain; lambda and sigma: canvas pixels along contour.',
              'algorithm': 'Native log G carrier + 0.35 * 0.1 * tanh(mean multiscale tangential highpass / 0.1). Complete observed kernel support only.',
              'invalid_data_behavior': 'Unsupported residual exactly zero; native base never replaced by a continued level. No mirror, no synthetic product samples.',
              'periodicity': 'Angular wrap closes the physically observed contour; it does not fill missing samples.',
              'smooth_nulls': {}, 'injections': {}, 'eligibility_by_dv': {}, 'noise_probe': {},
              'limits': ['No independent detector noise model or per-frame cross-validation.', 'E excludes original near-edge data; this pilot cannot recover excluded input.',
                         'Analytic nulls are QA only, never product data.', 'No final alpha, physical edge blending, color or Photoshop stack validation.']}
    report['parameters'] = {k: str(v) if isinstance(v, Path) else v for k,v in report['parameters'].items()}
    for name, sector in sectors.items():
        report['eligibility_by_dv'][name] = {}
        for lo,hi in bands:
            z=evalmask & sector & (dv>=lo)&(dv<hi)
            report['eligibility_by_dv'][name][f'{lo:g}-{hi:g}'] = dict(n=int(z.sum()), eligible=int((z&op.native_eligible).sum()),
                fraction=float(np.mean(op.native_eligible[z])) if z.any() else None)
    yy,xx=np.mgrid[box[0]:box[1],box[2]:box[3]]
    solar_r=np.hypot(xx-5361.768111973117, yy-3775.747534140857)
    edge=np.log(np.maximum(.5+.5*erf(op.dnormal/(np.sqrt(2)*1.2)),1e-5))
    nulls = {'contour_smooth': (-.015*op.dnormal).astype(np.float32),
             'solar_gradient_psf_proxy': (-.015*(solar_r-440.60304883027544)+edge+.03*np.cos(2*op.theta)).astype(np.float32)}
    null_corrections={}
    for name, inp in nulls.items():
        _,_,c=op.apply(inp)
        null_corrections[name]=c
        report['smooth_nulls'][name]={'all':statistics(c,evalmask),'bins':{}}
        for lo,hi in bands:
            report['smooth_nulls'][name]['bins'][f'{lo:g}-{hi:g}']=statistics(c,evalmask&(dv>=lo)&(dv<hi))
    # Known native-pixel phase, no angle median or redefinition to dv.
    for lam in (8.,24.):
        for quadrature in (0.,np.pi/2):
            ph=2*np.pi*op.arc/lam+quadrature
            inj=args.epsilon*np.cos(ph).astype(np.float32)
            plus,_,_=op.apply(base+inj)
            minus,_,_=op.apply(base-inj)
            derivative=(plus-minus)/(2*args.epsilon)
            asymmetry=(plus+minus-2*baseline)/(2*args.epsilon)
            key=f'lambda_{lam:g}_phase_{int(round(np.degrees(quadrature)))}'
            report['injections'][key]={'by_sector':{},'nonlinearity':statistics(asymmetry,evalmask)}
            theoretical=1+args.gain*np.mean([1-np.exp(-.5*(2*np.pi*s/lam)**2) for s in args.sigmas])
            report['injections'][key]['ideal_unsaturated_fully_sampled_gain']=float(theoretical)
            for name, sector in sectors.items():
                row={}
                for lo,hi in bands:
                    z=evalmask&sector&(dv>=lo)&(dv<hi)
                    fit=fit_phase(derivative,ph,z)
                    if 'amplitude' in fit: fit['relative_to_ideal_unsaturated_gain']=fit['amplitude']/theoretical
                    row[f'{lo:g}-{hi:g}']=fit
                ref=row.get('15-30',{}).get('amplitude')
                if ref:
                    for v in row.values():
                        if 'amplitude' in v: v['relative_to_same_sector_15_30']=v['amplitude']/ref
                report['injections'][key]['by_sector'][name]=row
    # White log noise gives only algorithmic amplification, not detector S/N.
    rng=np.random.default_rng(60526)
    noise=rng.normal(0,.002,base.shape).astype(np.float32)
    noisy,_,_=op.apply(base+noise)
    difference=noisy-baseline
    for lo,hi in bands:
        z=evalmask&(dv>=lo)&(dv<hi)
        report['noise_probe'][f'{lo:g}-{hi:g}']=dict(n=int(z.sum()),
            rms_gain=float(np.std(difference[z])/np.std(noise[z])) if z.any() else None)
    report['unchanged_unsupported_max_abs_log_difference']=float(np.max(abs((baseline-base)[~op.native_eligible])))
    report['max_abs_log_correction']=float(abs(correction).max())
    report['elapsed_seconds']=time.monotonic()-start
    # Acceptance gate concerns preservation by the complete base+residual, not
    # inverse compensation of attenuated filter-only amplitudes.
    transfer=[v['relative_to_same_sector_15_30'] for r in report['injections'].values()
              for v in r['by_sector']['top_60_130'].values() if 'relative_to_same_sector_15_30' in v]
    report['predeclared_gate']={'target_relative_transfer':[.9,1.1], 'top_all_measured_bins_pass': bool(all(.9<=v<=1.1 for v in transfer)),
        'note':'No tuning performed. Passing this restricted pilot is not promotion or scientific validation.'}
    (args.out/'PILOT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    np.savez_compressed(args.out/'pilot_arrays.npz', box=np.asarray(box),centre=centre,valid=valid,
                        native_eligible=op.native_eligible,dnormal=op.dnormal,dv=dv,
                        base_log=base,candidate_log=baseline,residual=residual,log_correction=correction)
    # Single fixed view curve shared by both image panels.
    view=np.clip(.55+.18*(base-np.median(base[evalmask])),0,1)
    view2=np.clip(.55+.18*(baseline-np.median(base[evalmask])),0,1)
    view[~valid]=.08;view2[~valid]=.08
    diff=np.stack([.5+15*correction,.5+15*correction,.5+15*correction],-1)
    diff[~valid]=.08
    panel_image([('Observed E G; same fixed log display',view),('Native carrier + bounded tangential residual',view2),
                 ('Correction; visual scale 15x (grey = zero)',diff)],args.out/'01_full_roi.png',
                'DIAGNOSTIC: complete 1400 px ROI, not complete final canvas; proxy contour / existing E domain')
    eligible=np.zeros((*valid.shape,3),np.float32)+.06
    eligible[valid]=[.6,.3,.1];eligible[op.native_eligible]=[.2,.75,.55]
    nullpic=.5+100*null_corrections['solar_gradient_psf_proxy']
    nullpic[~valid]=.08
    panel_image([('Green: residual eligible; amber: exact native base only',eligible),
                 ('Smooth-null correction x100; grey = zero',nullpic)],args.out/'02_support_and_null.png',
                'No missing samples are filled. Eligibility is not an output mask on the native base.')
    # Native 4x upper limb supplement, no rescaling independent of first view.
    sx0,sx1,sy0,sy1=640,850,210,300
    crops=[]
    for name,arr in [('base',view),('candidate',view2),('correction15x',diff)]:
        aa=arr[sy0:sy1,sx0:sx1]
        if aa.ndim==2:aa=np.repeat(aa[...,None],3,-1)
        img=Image.fromarray(np.uint8(np.clip(aa,0,1)*255)).resize((4*(sx1-sx0),4*(sy1-sy0)),Image.Resampling.NEAREST)
        img.save(args.out/f'03_top_4x_{name}.png')
    print(json.dumps({'out':str(args.out),'elapsed':report['elapsed_seconds'],'gate':report['predeclared_gate'],
                      'nulls':{k:v['all'] for k,v in report['smooth_nulls'].items()},
                      'unchanged_unsupported':report['unchanged_unsupported_max_abs_log_difference']}))


if __name__=='__main__':
    main()
