"""Estimate photon-transfer slope and read-noise variance from paired flats.

The fixed ROI and input folders are observation-specific; adapt them before use.
Pair differencing suppresses fixed illumination structure. The mean reference
from dark/ is subtracted before measuring signal; its exposure must be appropriate
for the flats. Results remain in native DN, without a propagated uncertainty budget.
"""
import glob, numpy as np, rawpy

def load(f):
    with rawpy.imread(f) as r:
        return r.raw_image_visible.astype(np.float64)  # Native DN, without demosaicing.

bias = np.mean([load(f) for f in sorted(glob.glob("dark/*.NEF"))], axis=0)
flats = sorted(glob.glob("flat/*.NEF"))           # Consecutive pairs at the same illumination level.
roi = (slice(1000, 2000), slice(1500, 2500))      # Central region chosen to avoid vignetting.

means, variances = [], []
for a, b in zip(flats[::2], flats[1::2]):
    A = load(a)[roi] - bias[roi]
    B = load(b)[roi] - bias[roi]
    means.append(0.5 * (A.mean() + B.mean()))
    variances.append(np.var(A - B) / 2)

g, r2 = np.polyfit(means, variances, 1)           # var = g*mean + r^2
print(f"g = {g:.4f} DN/ph,  r = {np.sqrt(max(r2, 0)):.3f} DN")