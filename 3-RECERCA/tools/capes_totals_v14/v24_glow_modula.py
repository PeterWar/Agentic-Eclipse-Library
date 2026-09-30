"""V24c2 · el glow de la vora, modulat pel relleu (declarat, artístic).

El detall del perímetre no es veia perquè el GLOW additiu (l'anell càlid del
fotograma) és llis i tapa la textura de sota. Cura: el contingut de la capa
REFLEX es modula ×(1 + 0,7·HP_norm) amb l'estructura REAL del residu viu —
la llum de la vora agafa el relleu (mars i accidents marcats DINS de la
llum). El reflex vermell també respira. Posició de Pere intacta.
"""
import json, numpy as np, cv2

CAU = "cau_v21"
CXT = CYT = 495.8
BETA = 0.7


def blur_norm(Z, m, s):
    return (cv2.GaussianBlur(Z * m, (0, 0), s)
            / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6))


def main():
    Rp = np.load(f"{CAU}/capa_reflex_pere.npy").astype(np.float32) / 65535.0
    E = np.load(f"{CAU}/vora_residu_viu.npy")
    # remap del residu viu al marc de la tessel·la (mateixa transformació)
    S22 = 453.5 / 455.5018189723177
    MB_V = (6465.398680355321, 6752.632845814709); POSV = (6257, 5969)
    yy, xx = np.mgrid[0:991, 0:991].astype(np.float32)
    rr = np.hypot(xx - CXT, yy - CYT)
    mx = ((MB_V[0] - POSV[1]) + (xx - CXT) / S22).astype(np.float32)
    my = ((MB_V[1] - POSV[0]) + (yy - CYT) / S22).astype(np.float32)
    T = cv2.remap(E, mx, my, cv2.INTER_LINEAR, borderValue=0)
    # ⚠️ la capa de Pere és 4 px a l'esquerra: el relleu s'hi ha d'alinear
    pos = json.load(open(f"{CAU}/reflex_pos_pere.json"))
    dx = pos["left"] - 4866          # −4
    dy = pos["top"] - 3279           # 0
    M = np.float32([[1, 0, -dx], [0, 1, -dy]])
    T = cv2.warpAffine(T, M, (991, 991), borderValue=0)
    dins = (rr < 460).astype(np.float32)
    HP = T - blur_norm(T, dins, 10.0)
    s = float(HP[(rr > 395) & (rr < 455)].std())
    HPn = np.clip(HP / max(3 * s, 1e-9), -1, 1)
    mod = 1.0 + BETA * HPn * np.clip((rr - 390) / 10.0, 0, 1)
    out = np.clip(Rp * mod[..., None], 0, 1)
    np.save(f"{CAU}/capa_reflex_pere.npy",
            np.clip(np.rint(out * 65535), 0, 65535).astype(np.uint16))
    print(f"glow modulat pel relleu (β={BETA}, σHP={s:.2f}) · posició de Pere "
          f"({pos['top']},{pos['left']}) respectada")


if __name__ == "__main__":
    main()
