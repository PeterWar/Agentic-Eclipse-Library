"""V44 derivative of V43 B2: one normalized raw-CFA interpolation; fine shift folded in mapping. Existing calibration, geometry, color and field retained. No drizzle or output resizing."""
from comu45 import *
import rawpy
from scipy.ndimage import gaussian_filter
import importlib.util as _iu, math
_sp = _iu.spec_from_file_location('b2v38', HERE38 / 'b2_recomposicio.py'); B = _iu.module_from_spec(_sp); _sp.loader.exec_module(B)
MC = (CX + 14.8, CY + 0.9); WIN = 700; MARGE_PX = 40.0; VORA_PX = 3.0


def main():
    claim45(); tag, nom = sys.argv[1], sys.argv[2]; args = dict(a.split('=', 1) for a in sys.argv[3:] if '=' in a)
    path = RUNS[tag]; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run); pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
    meta = json.loads((CAU36 / f'{tag}_meta.json').read_text())['frames']; m = meta[[mm['name'] for mm in meta].index(nom)]; group = tag if tag == 'vixen' else m['group']
    names = [mm['name'] for mm in meta if (tag == 'vixen' or mm['group'] == group)]; j = names.index(nom)
    phis = {c: np.load(CAU36 / f'{group}_{c}_phi.npy', mmap_mode='r') for c in ('R', 'G', 'B')}; fcorr, frep = B.flat_ripple_correction(ctx, tag)
    delta = math.radians(float(args.get('delta_arcmin', 0.0)) / 60.0) if group == 'sony_B' else 0.0; corr = json.loads(Path(args['corr']).read_text()) if ('corr' in args and group == 'sony_B') else {}; cx_, cy_ = corr.get(nom, (0.0, 0.0))
    inv = cv2.invertAffineTransform(COMMON_TO_FINAL); x0, y0 = int(round(MC[0])) - WIN, int(round(MC[1])) - WIN; yy, xx = np.mgrid[y0:y0 + 2 * WIN, x0:x0 + 2 * WIN].astype(np.float32)
    sx, sy = float(args.get('sx', 0)), float(args.get('sy', 0))
    xx -= sx; yy -= sy  # combine final lunar correction BEFORE the only CFA remap
    qx = inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]; qy = inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]; dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
    if delta != 0.0: c_, s_ = math.cos(delta), math.sin(delta); dx, dy = (c_ * dx - s_ * dy), (s_ * dx + c_ * dy)
    v = pos[nom]; k = kq.get(nom, 1.0)
    # desplaçament perquè la Lluna del fotograma caigui a M_c: la posició de M_c al comú → offset respecte del Sol
    qmx = inv[0, 0] * MC[0] + inv[0, 1] * MC[1] + inv[0, 2]; qmy = inv[1, 0] * MC[0] + inv[1, 1] * MC[1] + inv[1, 2]; dmx, dmy = (qmx - ctx.CX) * ctx.k, (qmy - ctx.CY) * ctx.k
    if delta != 0.0: dmx, dmy = (c_ * dmx - s_ * dmy), (s_ * dmx + c_ * dmy)
    off_x = float(v['lluna_dx']) - (ctx.ca * dmx + ctx.sa * dmy); off_y = float(v['lluna_dy']) - (-ctx.sa * dmx + ctx.ca * dmy)   # sol' = sol + lluna − Rm·d(M_c)
    rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x'] + cx_ + off_x).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y'] + cy_ + off_y).astype(np.float32)
    mlx = v['sol_x'] + cx_ + float(v['lluna_dx']); mly = v['sol_y'] + cy_ + float(v['lluna_dy']); dl = np.hypot(rx - mlx, ry - mly)
    disc = np.clip(((ctx.RL + MARGE_PX * ctx.k) - dl) / (VORA_PX * ctx.k), 0, 1).astype(np.float32)   # DINS del limbe + marge
    num = np.zeros((2 * WIN, 2 * WIN), np.float32); den = np.zeros_like(num); plans = ctx.plans(nom, v['exp'])
    with rawpy.imread(ctx.ruta[nom]) as rawfile: raw = rawfile.raw_image.astype(np.float32)
    greens=[]; weights=[]; stricts=[]; variances=[]; vnum=np.zeros_like(num)
    phi_full=B.upsample(phis['G'][j]); phi=cv2.remap(phi_full,xx,yy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
    field=np.exp(-phi); del phi_full

    for i,(pl,w) in plans.items():
        c=comu.IDX_CANAL[i]
        if c!=1:continue
        oy,ox=ctx.orig[i]
        if fcorr is not None: pl=pl*fcorr[i]
        mx=((rx-ox)*.5).astype(np.float32);my=((ry-oy)*.5).astype(np.float32)
        rplane=raw[oy::2,ox::2]
        # EARTHSHINE: preserve negative/low-count samples. A brightness floor
        # conditions on noise and biases faint pixels upward. Inverse variance
        # gives short exposures their appropriate small weight instead.
        rawdn=rplane-ctx.cfg['pedestal_dn'];span=ctx.cfg['saturacio_dn']-ctx.cfg['pedestal_dn']
        u=np.clip((rawdn-.35*span)/(.50*span),0,1)
        w=(v['exp']*(1-u*u*(3-2*u))*ctx.valid[oy::2,ox::2]).astype(np.float32)
        rn=(rplane-ctx.cfg['pedestal_dn'])/(ctx.cfg['saturacio_dn']-ctx.cfg['pedestal_dn'])
        ix=np.floor(mx).astype(int);iy=np.floor(my).astype(int)
        inside=(ix>=0)&(iy>=0)&(ix+1<rn.shape[1])&(iy+1<rn.shape[0])
        ix=np.clip(ix,0,rn.shape[1]-2);iy=np.clip(iy,0,rn.shape[0]-2)
        maximum=np.maximum.reduce([rn[iy,ix],rn[iy+1,ix],rn[iy,ix+1],rn[iy+1,ix+1]])
        strict=inside&(maximum<.85)
        dd=cv2.remap(w,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*disc*strict
        nn=cv2.remap(pl*w*k,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*disc*strict
        # Conditional photon/read variance, excluding systematic calibration uncertainty.
        gain_e=5.08 if tag=='vixen' else 3.41
        read_dn=(1.05 if v['exp']>=1 else 2.72) if tag=='vixen' else 1.22
        vv=np.maximum(rplane-ctx.cfg['pedestal_dn'],0)/gain_e+2*read_dn**2
        if tag=='sony':
            from comu36 import lin_corr_sony
            darkplane=ctx.dark(v['exp'])[oy::2,ox::2]
            derivative=((rplane+.5-darkplane)*lin_corr_sony(rplane+.5,ctx.cfg['pedestal_dn'],ctx.cfg['saturacio_dn'])-(rplane-.5-darkplane)*lin_corr_sony(rplane-.5,ctx.cfg['pedestal_dn'],ctx.cfg['saturacio_dn']))
            vv*=derivative**2
        flat=ctx.flat[oy::2,ox::2]
        scale=(k/(np.maximum(flat,1e-12)*v['exp']))
        if fcorr is not None:scale=scale*fcorr[i]
        vv*=scale**2
        # OpenCV bilinear fractions are quantized at1/32pixel.
        qmx=np.rint(mx*32)/32;qmy=np.rint(my*32)/32
        vx=np.floor(qmx).astype(int);vy=np.floor(qmy).astype(int);fx=qmx-vx;fy=qmy-vy
        vx=np.clip(vx,0,w.shape[1]-2);vy=np.clip(vy,0,w.shape[0]-2)
        vn=np.zeros_like(num)
        for dy,dx,bb in [(0,0,(1-fy)*(1-fx)),(0,1,(1-fy)*fx),(1,0,fy*(1-fx)),(1,1,fy*fx)]:
            vn+=(bb*w[vy+dy,vx+dx])**2*vv[vy+dy,vx+dx]
        vn*=disc**2*strict*field**2
        vnum+=vn
        variances.append(np.where(dd>0,vn/np.maximum(dd**2,1e-30),np.nan))
        nn=(nn+float(m['offset_RGB'][1])*dd)*field
        num+=nn;den+=dd
        greens.append(np.where(dd>0,nn/np.maximum(dd,1e-20),np.nan));weights.append(dd/v['exp']);stricts.append(strict)
    g=np.where(den>0,num/np.maximum(den,1e-20),np.nan)
    q=(den/(2*v['exp'])).astype(np.float32)
    stem=nom.split('.')[0];target=CAU45/f'native_{tag}_{stem}.npz'
    both=(weights[0]>.9)&(weights[1]>.9)&(R<.7*RL)
    df=greens[0]-greens[1]
    noise=float(np.nanmedian(abs(df[both]-np.nanmedian(df[both])))/.67448975/2) if both.any() else None
    temporary=target.with_suffix(".writing.npz")
    np.savez_compressed(temporary,g=g,q=q,g1=greens[0],g2=greens[1],q1=weights[0],q2=weights[1],variance=np.where(den>0,vnum/np.maximum(den**2,1e-30),np.nan))
    temporary.replace(target)
    rep=dict(fotograma=nom,tren=tag,grup=group,exp=v['exp'],file=str(target),sha256=sha(target),no_brightness_floor=True,shot_read_variance='bilinear coefficient squared; Poisson5.08/3.41e perADU, read2.72/1.05Vixen1.22Sony, extra single-dark read term, SonyLUTderivative; excludes flat/field systematic/covariance',single_CFA_remap=True,shift=[sx,sy],strict_saturation='all four contributing native CFA pixels <0.85 per green plane',matrix='NONE: calibrated white-balanced native G1+G2, R/B never required',noise_Gmean_inner_MAD=noise,inner_G=float(np.nanmedian(g[R<.7*RL])),valid_inner=int(((q>0)&(R<.7*RL)).sum()),valid_limb=int(((q>0)&(R>440)&(R<454)).sum()))
    savejson(REB45/f'B1_{tag}_{stem}.json',rep)
    print(json.dumps(rep),flush=True)



if __name__ == '__main__':
    main()
