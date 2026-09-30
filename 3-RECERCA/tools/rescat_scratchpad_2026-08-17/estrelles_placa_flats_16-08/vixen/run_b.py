import numpy as np, viab

# centre lunar tipic: CY=2245 CX=3572 R=452
CY, CX, R = 2245, 3572, 452

def pos(az_deg, r):
    a = np.radians(az_deg)
    return int(CY + r*np.cos(a)), int(CX + r*np.sin(a))

REG = {
    'corona interior (az 180)': (*pos(180, R+110), 96),
    'corona interior (az 0)':   (*pos(0,   R+110), 96),
    'protuberancia (az 261)':   (*pos(261, R+25), 56),
    'protuberancia (az 47)':    (*pos(47,  R+25), 56),
    'disc lunar (control)':     (CY, CX, 128),
}

PAIRS = [
    ("572A3012.CR3", "572A3013.CR3", "1/3200 (0,65 s)"),
    ("572A3015.CR3", "572A3016.CR3", "1/3200 (0,65 s)"),
    ("572A2962.CR3", "572A2963.CR3", "1/3200 prop de C2"),
    ("572A2998.CR3", "572A3004.CR3", "1/500 (6,0 s)"),
    ("572A2999.CR3", "572A3005.CR3", "1/125 (6,0 s)"),
]

for a, b, lab in PAIRS:
    for rn, (cy, cx, h) in REG.items():
        if 'protuberancia' in rn and '1/125' in lab:
            continue
        viab.analyse(a, b, cy, cx, h, "%s | %s" % (lab, rn))
