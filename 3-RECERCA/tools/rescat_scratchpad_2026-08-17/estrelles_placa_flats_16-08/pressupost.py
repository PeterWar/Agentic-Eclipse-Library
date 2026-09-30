import numpy as np, math, pandas as pd
F0 = 8.97e5           # ph/cm2/s per a m_V=0 (banda V, 890 A)
ETA_PX  = 0.27        # optica x filtre verd x QE, per pixel
ETA_STAR= 0.135       # idem pero nomes la meitat dels pixels son verds
K, XLO, XHI = 0.37, 6.06, 6.40
A_EXT = K*6.2

trens = {
 'Sony A7RIIIA + 300GM': dict(D=10.7, scale=3.234, texp=[8.0,2.0,1.0], n=[2,3,3], npix=20, fwc=46000, rn=3.0, f=2.8),
 'R6III + VSD90SS'     : dict(D=9.0,  scale=2.158, texp=[10.3,2.0,1.0,0.5], n=[3,3,2,4], npix=40, fwc=55000, rn=5.0, f=5.5),
}
def rate_px(mu, A, om):   return F0*10**(-0.4*mu)*A*om*ETA_PX      # e-/s/px
def rate_star(m, A):      return F0*10**(-0.4*m)*A*ETA_STAR        # e-/s totals

print(f"extincio adoptada: k=0,37 mag/X, X={XLO:.2f}-{XHI:.2f}  ->  A_V = {K*XLO:.2f}-{K*XHI:.2f} mag (adopto {A_EXT:.2f})")
print()
# perfil de corona (K+F), B/B0 de disc mitja; mu_disc = -10.62 mag/arcsec2
rr  = np.array([1.2,1.5,2,2.5,3,4,5,6,8,10,14,20])
bb  = np.array([4.4e-7,1.2e-7,3.5e-8,1.4e-8,6.5e-9,2.2e-9,1.1e-9,6.0e-10,2.6e-10,1.4e-10,6e-11,2.5e-11])
mu_cor = -10.62 - 2.5*np.log10(bb) + A_EXT
print("=== corona: brillantor superficial OBSERVADA (mag/arcsec2) ===")
print("  r/Rsol: " + "  ".join(f"{x:5.1f}" for x in rr))
print("  mu    : " + "  ".join(f"{x:5.1f}" for x in mu_cor))
print()

for nom, T in trens.items():
    A  = math.pi*(T['D']/2)**2
    om = T['scale']**2
    print(f"### {nom}: D={T['D']*10:.0f} mm, A={A:.1f} cm2, escala {T['scale']}\"/px, Omega={om:.2f} arcsec2/px, f/{T['f']}")
    # saturacio de la corona
    for tex in T['texp'][:1]+[T['texp'][1]]:
        sat=[r for r,m in zip(rr,mu_cor) if rate_px(m,A,om)*tex < 0.9*T['fwc']]
        print(f"   a {tex} s la corona satura per dins de ~{min(sat) if sat else '>20'} R_sol")
    print("   fons de cel (e-/px) i magnitud limit V (SNR=5), sense corona:")
    print("   mu_cel |" + "".join(f"  {t:>5}s x{n}" for t,n in zip(T['texp'],T['n'])) + "   |  apilat")
    for mu in [11,12,13,14,15,16,17]:
        cells=[]; 
        for tex,nfr in zip(T['texp'],T['n']):
            B = rate_px(mu,A,om)*tex
            if B > 0.9*T['fwc']: cells.append("  SATURAT "); continue
            Btot = T['npix']*(B+T['rn']**2)
            S = (25+math.sqrt(625+4*25*Btot))/2
            m_obs = -2.5*math.log10(S/(ETA_STAR*F0*A*tex))
            cells.append(f"  V={m_obs-A_EXT:5.2f} ")
        # apilat: suma de tots els fotogrames vius
        Stot=0; Btot=0
        for tex,nfr in zip(T['texp'],T['n']):
            B = rate_px(mu,A,om)*tex
            if B > 0.9*T['fwc']: continue
            Btot += nfr*T['npix']*(B+T['rn']**2); Stot += nfr*ETA_STAR*F0*A*tex
        S = (25+math.sqrt(625+4*25*Btot))/2
        m_obs = -2.5*math.log10(S/Stot)
        print(f"     {mu:2d}   |" + "".join(cells) + f"   | V={m_obs-A_EXT:5.2f}")
    print()

# SNR de candidats concrets, cas Sony 8 s (2 fotogrames) i R6 10,3 s (3)
cand = [('xi Leo (HIP 46771)',4.99,3.7055),('8 Leo (HIP 47189)',5.73,2.5753),('psi Leo (HIP 47723)',5.36,3.8049),
        ('pi2 Cnc (HIP 45410)',5.36,3.1924),('HIP 46232',6.31,1.8196),('7 Leo (HIP 47096)',6.32,1.8740),
        ('HIP 45874',6.57,1.7965),('83 Cnc (HIP 45699)',6.61,3.6047),('11 Leo (HIP 47266)',6.63,2.3826),
        ('HIP 45879',6.67,2.4934),('HIP 46345',6.83,0.7036),('HIP 46464',6.88,2.5204),('HIP 46713',6.92,2.1639),
        ('HIP 45894',6.98,2.3912),('HIP 46650',7.67,1.5117),('HIP 46745',7.66,1.1598),('HIP 46335',7.77,0.5718)]
RS=947.07/3600
print("=== SNR previst (apilat) per fons de cel de 13 i 15 mag/arcsec2, corona inclosa al fons ===")
def snr(T,mu_sky,V,nfr_list):
    A=math.pi*(T['D']/2)**2; om=T['scale']**2
    Stot=0;Btot=0
    for tex,nfr in zip(T['texp'],nfr_list):
        B=rate_px(mu_sky,A,om)*tex
        if B>0.9*T['fwc']: return None
        Btot+=nfr*T['npix']*(B+T['rn']**2); Stot+=nfr*ETA_STAR*F0*A*tex
    S=Stot*10**(-0.4*(V+A_EXT))
    return S/math.sqrt(S+Btot)
hdr=f"{'estrella':22s} {'V':>5} {'sep':>6} {'r/Rs':>6} | {'Sony mu13':>9} {'Sony mu15':>9} | {'R6 mu13':>8} {'R6 mu15':>8}"
print(hdr); print('-'*len(hdr))
for nm,V,sep in cand:
    mu_c = np.interp(sep/RS, rr, mu_cor)
    def comb(mu): return -2.5*math.log10(10**(-0.4*mu)+10**(-0.4*mu_c))
    a=snr(trens['Sony A7RIIIA + 300GM'],comb(13),V,[2,3,3])
    b=snr(trens['Sony A7RIIIA + 300GM'],comb(15),V,[2,3,3])
    c=snr(trens['R6III + VSD90SS'],comb(13),V,[3,3,2,4])
    d=snr(trens['R6III + VSD90SS'],comb(15),V,[3,3,2,4])
    fm=lambda x: "  SAT   " if x is None else f"{x:8.0f}"
    print(f"{nm:22s} {V:5.2f} {sep:6.3f} {sep/RS:6.2f} | {fm(a)} {fm(b)} | {fm(c)} {fm(d)}")
