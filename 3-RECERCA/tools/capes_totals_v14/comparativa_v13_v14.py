"""V13 contra V14, al llenç sencer de cadascuna, una al costat de l'altra."""
import os, numpy as np, cv2
from psd_tools import PSDImage
D = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals"
V = f"{D}/CapesTotalsV14_vistes"
def merged(p):
    psd = PSDImage.open(p)
    a = np.asarray(psd.numpy())[..., :3]
    return np.clip(a, 0, 1)
for nom, fitxer in (("V13", "CapesTotalsV13.psd"), ("V13_Pere", "CapesTotalsV13_Pere.psd")):
    a = merged(f"{D}/{fitxer}")
    cv2.imwrite(f"{V}/{nom}_compost.png", (a*255).astype(np.uint8)[::6, ::6][..., ::-1])
    print(nom, a.shape, "mitjana %.4f"%a.mean())
