import numpy as np, sys
sys.path.insert(0, '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/604fa71e-4fd9-4d66-a0e5-157c6621ceb3/scratchpad')
from model import *

xi, eta_, V = make_field(seed=3)
MU = 12.5
YIELD = 0.50      # fraction of nominally-detectable stars that survive a real pipeline
MARGIN = 1.20     # model is ~20% optimistic vs Bruns's published star-fit term

def budget(F, D, pix, sw, sh, eta, fwhm, aext, csys, order,
           distres_mas, coronares_mas, extcal=False, dS=0.0, t=200.0, mu=MU,
           yield_=YIELD, offset=0.0):
    p = 206265*pix*1e-3/F
    w, h = np.rad2deg(sw/F), np.rad2deg(sh/F)
    fe = 2.355*np.hypot(fwhm/2.355, p/np.sqrt(12))
    pa = np.deg2rad(314.3); cx, cy = offset*np.sin(pa), offset*np.cos(pa)
    m = (np.abs(xi-cx) < w/2) & (np.abs(eta_-cy) < h/2)
    x, y, v = xi[m], eta_[m], V[m]
    r = np.hypot(x, y)/RSUN_DEG
    sn = snr(v, mu_bg(r, mu), D, t, fe, eta, aext)
    ok = sn >= 7.0
    x, y, sn = x[ok], y[ok], sn[ok]
    sig = np.hypot(0.425*fe/sn, csys*fwhm)
    rnd, N = sigma_eps(x, y, sig, order=order, fix_scale=extcal, rmin=1.8)
    rnd = rnd * MARGIN / np.sqrt(yield_)
    N = int(N*yield_)
    lk = {1: 0.334, 3: 0.110, 5: 0.036}[order]
    bd = lk*distres_mas/1000.0
    bc = 1.15*coronares_mas/1000.0
    Rd = np.hypot(w, h)/2
    bs = (dS*1e6)*(0.0037*Rd/1.18) if extcal else 0.0
    return dict(N=N, rnd=rnd, bd=bd, bc=bc, bs=bs,
                tot=np.sqrt(rnd**2+bd**2+bc**2+bs**2), p=p, w=w, h=h, fwhm=fwhm)

VSD = dict(F=494, D=89.8, sw=36, sh=24)
rows = [
 ('0  as flown: R6III Bayer, no filter, linear plate fit', 0,
  dict(**VSD, pix=5.17, eta=ETA_BAYER, fwhm=4.13, aext=0.20, csys=0.070, order=1,
       distres_mas=800, coronares_mas=60)),
 ('1  R6III + red long-pass, 3rd-order fit, careful reduction', 60,
  dict(**VSD, pix=5.17, eta=ETA_BAYER, fwhm=3.90, aext=0.14, csys=0.035, order=3,
       distres_mas=150, coronares_mas=10)),
 ('2  A7RIIIA (4.51um) + red long-pass, 3rd order', 60,
  dict(F=494, D=89.8, sw=35.9, sh=23.9, pix=4.51, eta=ETA_BAYER, fwhm=3.90,
       aext=0.14, csys=0.033, order=3, distres_mas=150, coronares_mas=10)),
 ('3  ASI2600MM APS-C mono + r\', 3rd order', 2300,
  dict(F=494, D=89.8, sw=23.5, sh=15.7, pix=3.76, eta=ETA_MONO_R, fwhm=3.50,
       aext=0.12, csys=0.020, order=3, distres_mas=40, coronares_mas=8)),
 ('4  ASI6200MM FF mono + r\', 3rd order', 4900,
  dict(**VSD, pix=3.76, eta=ETA_MONO_R, fwhm=3.50, aext=0.12, csys=0.020, order=3,
       distres_mas=40, coronares_mas=8)),
 ('5  ASI6200MM FF mono + r\', 3rd order, offset 0.55deg to M44', 4900,
  dict(**VSD, pix=3.76, eta=ETA_MONO_R, fwhm=3.50, aext=0.12, csys=0.020, order=3,
       distres_mas=40, coronares_mas=8, offset=0.55)),
 ('6  ASI6200MM FF mono + r\', 5th order', 4900,
  dict(**VSD, pix=3.76, eta=ETA_MONO_R, fwhm=3.50, aext=0.12, csys=0.020, order=5,
       distres_mas=40, coronares_mas=8)),
 ('7  ASI6200MM + r\' + calibration fields (scale external)  <== BEST', 4900,
  dict(**VSD, pix=3.76, eta=ETA_MONO_R, fwhm=3.50, aext=0.12, csys=0.020, order=3,
       distres_mas=40, coronares_mas=8, extcal=True, dS=5e-7)),
 ('8  ASI6200MM + r\' + 0.79x reducer (390mm), 3rd order', 5700,
  dict(F=390, D=89.8, sw=36, sh=24, pix=3.76, eta=ETA_MONO_R, fwhm=3.50, aext=0.12,
       csys=0.020, order=3, distres_mas=80, coronares_mas=8)),
 ('9  Sony 300/2.8 @f/4 + ASI6200MM + r\', 3rd order', 4900,
  dict(F=300, D=75, sw=36, sh=24, pix=3.76, eta=ETA_MONO_R, fwhm=5.50, aext=0.12,
       csys=0.035, order=3, distres_mas=250, coronares_mas=20)),
 ('10 Sony 300/2.8 + A7RIIIA as flown, 3rd order', 0,
  dict(F=300, D=107, sw=35.9, sh=23.9, pix=4.51, eta=ETA_BAYER, fwhm=6.50, aext=0.20,
       csys=0.050, order=3, distres_mas=600, coronares_mas=30)),
 ('11 BUY NP101is 540/101 + ASI6200MM + r\' + cal fields', 10000,
  dict(F=540, D=101, sw=36, sh=24, pix=3.76, eta=ETA_MONO_R, fwhm=3.30, aext=0.12,
       csys=0.020, order=3, distres_mas=25, coronares_mas=8, extcal=True, dS=5e-7)),
]
hdr = (f"{'configuration':58s} {'N*':>5s} {'random':>7s} {'dist':>6s} {'coro':>6s} "
       f"{'scale':>6s} {'TOTAL':>7s} {'GRs':>5s} {'E-N':>5s} {'EUR':>6s}")
print("=== TOTAL sigma(epsilon), with a 50% star-yield discount and a 20% model margin ===\n")
print(hdr); print('-'*len(hdr))
B = {}
for nm, cost, kw in rows:
    b = budget(**kw); B[nm[:2].strip()] = b
    print(f"{nm:58s} {b['N']:5d} {b['rnd']*100:6.2f}% {b['bd']*100:5.2f}% {b['bc']*100:5.2f}% "
          f"{b['bs']*100:5.2f}% {b['tot']*100:6.2f}% {1/b['tot']:5.0f} {0.5/b['tot']:5.1f} {cost:6d}")

print("\n=== TWO TRAINS: proper correlated inverse-variance combination ===")
def comb(a, b, rho):
    sa, sb = a['tot'], b['tot']
    ca = np.sqrt(a['bd']**2+a['bc']**2+a['bs']**2)
    cb = np.sqrt(b['bd']**2+b['bc']**2+b['bs']**2)
    cov = rho*ca*cb
    return np.sqrt((sa**2*sb**2 - cov**2)/(sa**2 + sb**2 - 2*cov))
P = B['7']
_pa = "primary alone (VSD90SS + FF mono + r' + cal)"
print(f"   {_pa:52s} {P['tot']*100:6.2f}%")
for nm, k, rho in [('+ Sony 300 @f/4 + FF mono (indep. optics, rho=0.3)', '9', 0.3),
                   ('+ Sony 300 + A7RIIIA as flown (rho=0.3)', '10', 0.3),
                   ('+ R6III on a 2nd VSD-class scope (rho=0.6)', '1', 0.6),
                   ('+ an identical twin rig (rho=1.0, no new info)', '7', 1.0),
                   ('+ an identical twin rig (rho=0.0, ideal)', '7', 0.0)]:
    print(f"   {nm:52s} {comb(P, B[k], rho)*100:6.2f}%")

print("\n=== WHAT IF THE SYSTEMATICS ARE WORSE THAN HOPED (config 7) ===")
for lbl, kw in [('as costed above', {}),
                ('coronal/radial residual 25 mas not 8', dict(coronares_mas=25)),
                ('coronal/radial residual 50 mas', dict(coronares_mas=50)),
                ('distortion residual 200 mas not 40', dict(distres_mas=200)),
                ('per-star floor 0.060" not 0.020xFWHM', dict(csys=0.060/3.5)),
                ('per-star floor 0.150"', dict(csys=0.150/3.5)),
                ('daytime seeing 5" (FWHM 5.3")', dict(fwhm=5.3)),
                ('only 100 s of totality usable', dict(t=100.0)),
                ('star yield 20% not 50%', dict(yield_=0.20)),
                ('ALL of the above pessimistic together',
                 dict(coronares_mas=50, distres_mas=200, csys=0.150/3.5, fwhm=5.3,
                      t=100.0, yield_=0.20))]:
    a = dict(**VSD, pix=3.76, eta=ETA_MONO_R, fwhm=3.50, aext=0.12, csys=0.020,
             order=3, distres_mas=40, coronares_mas=8, extcal=True, dS=5e-7)
    a.update(kw); b = budget(**a)
    print(f"   {lbl:42s} sigma(eps)={b['tot']*100:6.2f}%   GR {1/b['tot']:5.0f} sigma,"
          f"  Einstein-vs-Newton {0.5/b['tot']:5.1f} sigma")

print("\n=== DELIVERED PRECISION IN THE USUAL UNITS ===")
for k, nm in (('0','as flown'), ('1','R6III + red filter'), ('4','FF mono + r\''),
              ('7','FF mono + r\' + cal fields')):
    t = B[k]['tot']
    print(f"   {nm:28s} sigma(eps)={t*100:5.2f}%  ->  L = 1.7516 +/- {1.7516*t:.4f}\" "
          f"; gamma to +/-{2*t*100:5.2f}%")
print(f"   {'Bruns 2017 (the record)':28s} sigma(eps)= 3.40%  ->  L = 1.7512 +/- 0.0600\" "
      f"; gamma to +/- 6.80%")
