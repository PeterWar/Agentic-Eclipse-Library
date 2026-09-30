"""m1 (V98) · Vistes de les marques de Pere de V97_Artefactes.psb (i Artefactes_V95.psb): cada capa de marques sobre el filtre que té
just a sota, retallat a la caixa de la marca (+ marge), a 1:1 i ampliat. Només lectura dels PSB. Sortida: 4-RESULTATS/v98_20260925/marques/."""
import sys, json
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
O = ARREL / '4-RESULTATS/v98_20260925/marques'; O.mkdir(parents=True, exist_ok=True)
def rgba(s, lid, box):
    ch = [s.channel_box(lid, c, box) for c in (0, 1, 2)]; al = s.channel_box(lid, -1, box)
    return np.dstack(ch).astype(np.float32) / 65535, (al.astype(np.float32) / 65535 if al is not None else np.ones(ch[0].shape, np.float32))
def vista(psbp, parelles, pref, marge=80):
    s = PSB(psbp); rep = {}
    for marca, filtre in parelles:
        L = s.layer(marca); x0, y0, x1, y1 = L['left'] - marge, L['top'] - marge, L['right'] + marge, L['bottom'] + marge
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, s.width), min(y1, s.height); box = (x0, y0, x1, y1)
        f, fa = rgba(s, filtre, box); mk, ma = rgba(s, marca, box)
        ma_raw = ma; ma = np.clip(ma / max(float(ma.max()), 1e-6), 0, 1) * 0.7   # Pere pinta amb opacitat baixa (≤ 19 %): normalitzat per veure-ho
        base = f * fa[..., None] + 0.5 * (1 - fa[..., None])
        comp = base * (1 - ma[..., None]) + mk * ma[..., None]
        nom = f"{pref}_{marca}_{s.layer(filtre)['name'][:24].replace(' ', '_').replace('/', '-').replace('·', '')}"
        for k, im in (('filtre', base), ('marques', comp)):
            u8 = (np.clip(im, 0, 1) * 255).astype(np.uint8)[..., ::-1]; cv2.imwrite(str(O / f'{nom}_{k}.png'), u8)
        # màscara de les marques per colors (tons dominants)
        mm = ma_raw > 0; cols = (mk[mm] * 4).round().astype(int) if mm.any() else np.zeros((0, 3), int)
        u, n = np.unique(cols, axis=0, return_counts=True) if len(cols) else (np.zeros((0, 3)), np.zeros(0))
        rep[marca] = dict(filtre=filtre, nom_filtre=s.layer(filtre)['name'], nom_marca=L['name'], caixa=box, px_marcats=int(mm.sum()),
                          colors=[(c.tolist(), int(k)) for c, k in sorted(zip(u, n), key=lambda z: -z[1])[:6]])
        print(marca, rep[marca], flush=True)
    return rep
if __name__ == '__main__':
    V97A = [(313, 54), (311, 43), (310, 44), (309, 41), (306, 42), (307, 47), (304, 51), (305, 45), (301, 55), (314, 56)]
    rep = vista(ARREL / '1-PHOTOSHOP/V97_Artefactes.psb', V97A, 'V97A')
    V95A = [(284, 48), (283, 50), (282, 53), (280, 43), (279, 44), (277, 41), (276, 42), (275, 47), (274, 49), (273, 51), (272, 45), (271, 46), (270, 56), (269, 56)]
    rep.update({f'V95_{k}': v for k, v in vista(ARREL / '1-PHOTOSHOP/Artefactes_V95.psb', V95A, 'V95A').items()})
    (O / 'M1_MARQUES.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
