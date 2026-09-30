import numpy as np, eb_core as E
rng=np.random.default_rng(4); RS=E.RSUN27

EXT_GAIN = 10**(0.4*(0.37*6.03 - 0.20*1.011))   # Leon 6.03 airmass -> Luxor 1.011
print(f"extinction gain Leon->Luxor = {2.5*np.log10(EXT_GAIN):.2f} mag  (x{EXT_GAIN:.1f})")
FILT = {'bayer luminance, no filter':1.00,'bayer red plane only':0.33,
        'mono + Sloan r\'':1.30,'mono, no filter':3.00}

print("\n"+"="*78); print("LIMITING MAGNITUDE AT LUXOR  (SNR=7, 240 s on the eclipse field)")
print("="*78)
print(f"{'train / optic':30s} {'filter':26s} {'FWHM':>5} {'V(7s) @3Rsun':>13} {'@6':>6} {'@10':>6}")
def vlim(area,t,thru,fwhm,rho,msky=12.0,snrmin=7.):
    V=np.linspace(6,16,401)
    s,_=E.star_sigma(V,rho,area,t,thru,fwhm,msky)
    return np.interp(-snrmin,-s,V)
for tl,area,fw in [('A  Sony 300/2.8',90.1,5.4),('B  VSD90SS',63.3,3.8),
                   ('C  100mm apo (new)',78.5,3.2)]:
    for fl,ft in FILT.items():
        thru=EXT_GAIN*ft
        print(f"{tl:30s} {fl:26s} {fw:5.1f} "
              f"{vlim(area,240,thru,fw,3.0):13.2f} {vlim(area,240,thru,fw,6.0):6.2f}"
              f" {vlim(area,240,thru,fw,10.0):6.2f}")

print("\n"+"="*78)
print("WHERE THE BACKGROUND COMES FROM AT LUXOR (sky 12.0 mag/arcsec2)")
print("="*78)
print(f"{'r (Rsun)':>9} {'corona':>8} {'sky':>7} {'total':>7}  dominant")
for rho in [2,2.5,3,4,5,6,8,10,13]:
    mc=E.m_corona(rho); mt=E.m_bg(rho,12.0)
    print(f"{rho:9.1f} {mc:8.2f} {12.0:7.2f} {mt:7.2f}  "
          f"{'CORONA' if mc<12.0 else 'sky'}")

print("\n"+"="*78)
print("PHOTON-LIMITED CENTROID sigma vs V and radius  [train B, mono r', 240 s, FWHM 3.8\"]")
print("="*78)
thru=EXT_GAIN*1.30
print(f"{'V':>5} " + "".join(f"{r:>9.1f}" for r in [2,3,5,8,12]))
for V in [5,6,7,8,9,10,11,12]:
    row=f"{V:5.1f} "
    for rho in [2,3,5,8,12]:
        s,sg=E.star_sigma(float(V),float(rho),63.3,240,thru,3.8,12.0)
        row+=f"{sg:9.3f}" if s>=7 else f"{'--':>9}"
    print(row)
