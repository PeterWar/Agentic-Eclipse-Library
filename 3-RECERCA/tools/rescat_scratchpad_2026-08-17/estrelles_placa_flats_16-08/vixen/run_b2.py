import numpy as np, viab2, lib

CY, CX, R = 2245, 3572, 452
def pos(az, r):
    a = np.radians(az); return int(CY+r*np.cos(a)), int(CX+r*np.sin(a))

print("Nyquist reixa verda quincunx: pas %.3f arcsec -> periode minim %.2f arcsec" % (viab2.STEP, 2*viab2.STEP))
print("Nyquist d'un pla de Bayer sol: pas %.3f arcsec -> periode minim %.2f arcsec\n" % (2*lib.SCALE, 4*lib.SCALE))

CASES = [
    # parelles contigues a 1/3200 (0,65 s): registre irrellevant
    ("572A3012.CR3", "572A3013.CR3", "1/3200 x2"),
    ("572A3015.CR3", "572A3016.CR3", "1/3200 x2"),
    ("572A3010.CR3", "572A3011.CR3", "1/3200 x2"),
    ("572A2963.CR3", "572A2964.CR3", "1/3200 x2 (prop C2)"),
]
REG = {
    'corona interior az 180': (*pos(180, R+110), 96),
    'corona interior az 0':   (*pos(0,   R+110), 96),
    'corona interior az 90':  (*pos(90,  R+110), 96),
    'protuberancia az 261':   (*pos(261, R+30), 48),
    'protuberancia az 47':    (*pos(47,  R+30), 48),
    'disc lunar (control)':   (CY, CX, 128),
}
for a, b, lab in CASES:
    for rn, (cy, cx, h) in REG.items():
        viab2.run(a, b, cy, cx, h, "%-20s | %-22s" % (lab, rn))
    print()

# parelles amb molta relacio senyal/soroll, nomes corona (sense limbe dins la caixa)
CASES2 = [("572A2999.CR3", "572A3005.CR3", "1/125 (6,0 s)"),
          ("572A2987.CR3", "572A2999.CR3", "1/125 (12,0 s)"),
          ("572A2998.CR3", "572A3004.CR3", "1/500 (6,0 s)"),
          ("572A2992.CR3", "572A2974.CR3", "1/250"),
          ("572A2991.CR3", "572A2973.CR3", "1/1000")]
REG2 = {k: v for k, v in REG.items() if 'corona' in k or 'control' in k}
for a, b, lab in CASES2:
    for rn, (cy, cx, h) in REG2.items():
        viab2.run(a, b, cy, cx, h, "%-20s | %-22s" % (lab, rn))
    print()
