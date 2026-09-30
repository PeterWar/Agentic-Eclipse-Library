"""Lector de capes d'un TIFF de Photoshop (ImageSourceData, tag 37724), a resolució completa.

Reutilitza el que ja s'havia après a research/tools/capes_photoshop (17-08) i encaix_sony/parse_layers.py:
- signatura de 36 bytes («...Data Block\\0» o «...Data V0002\\0»), blocs «8BIM» girats (MIB8) en little-endian;
- dos formats de longitud (4 o 8 bytes) segons el document: s'autodetecta amb la primera capa;
- els píxels de 16 bits de cada canal van en big-endian encara que tot el TIFF sigui little-endian.
Només lectura.
"""
import mmap, struct
import numpy as np
import tifffile
from psd_tools.compression import decompress

K64 = ("LMsk", "Lr16", "Lr32", "Layr", "Mt16", "Mt32", "Mtrn", "Alph", "FMsk", "lnk2", "FEid", "FXid", "PxSD", "cinf")


class TiffCapes:
    def __init__(self, path):
        self.path = path
        with tifffile.TiffFile(path) as t:
            p = t.pages[0]
            self.shape = p.shape[:2]
            tag = p.tags[37724]
            self.off, self.cnt = tag.valueoffset, tag.count
        self.f = open(path, "rb")
        self.mm = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
        mm = self.mm
        sig = mm[self.off:self.off + 36]
        assert sig.startswith(b"Adobe Photoshop Document Data"), sig
        i = self.off + 36
        key = mm[i + 4:i + 8][::-1].decode("latin1")
        assert key in ("Lr16", "Lr32", "Layr"), key
        self.key = key
        mode = None
        for LN in (4, 8):
            ln = (self._u32 if LN == 4 else self._u64)(i + 8)
            off = i + 8 + LN
            if ln > self.off + self.cnt - off:
                continue
            try:
                n = abs(self._i16(off))
                top, left, bottom, right = self._i32(off + 2), self._i32(off + 6), self._i32(off + 10), self._i32(off + 14)
                nch = self._u16(off + 18)
                clen = (self._u32 if LN == 4 else self._u64)(off + 22)
                if 1 <= n <= 2000 and 0 < right - left < 100000 and 0 < bottom - top < 100000 and 1 <= nch <= 8 \
                        and 0 < clen <= (right - left) * (bottom - top) * 2 + 2:
                    mode = LN
                    break
            except Exception:
                continue
        assert mode is not None, "no he sabut llegir la capçalera de capes"
        self.mode = mode
        self.CLEN = self._u32 if mode == 4 else self._u64
        self.blk_off = i + 8 + mode
        self.blk_len = ln
        self._parse()

    def _u8(self, p): return self.mm[p]
    def _u16(self, p): return struct.unpack("<H", self.mm[p:p + 2])[0]
    def _i16(self, p): return struct.unpack("<h", self.mm[p:p + 2])[0]
    def _u32(self, p): return struct.unpack("<I", self.mm[p:p + 4])[0]
    def _i32(self, p): return struct.unpack("<i", self.mm[p:p + 4])[0]
    def _u64(self, p): return struct.unpack("<Q", self.mm[p:p + 8])[0]

    def _parse(self):
        mm = self.mm
        j = self.blk_off
        n_signed = self._i16(j); j += 2
        n = abs(n_signed)
        capes = []
        for k in range(n):
            rect = [self._i32(j), self._i32(j + 4), self._i32(j + 8), self._i32(j + 12)]; j += 16
            nch = self._u16(j); j += 2
            canals = []
            for c in range(nch):
                cid = self._i16(j); clen = self.CLEN(j + 2); j += 2 + self.mode
                canals.append([cid, clen])
            j += 4
            blend = mm[j:j + 4][::-1].decode("latin1"); j += 4
            opac, clip, flags = mm[j], mm[j + 1], mm[j + 2]; j += 4
            extra = self._u32(j); j += 4; e0 = j
            mlen = self._u32(j); mrect = None; mdef = None
            if mlen >= 20:
                mrect = [self._i32(j + 4), self._i32(j + 8), self._i32(j + 12), self._i32(j + 16)]
                mdef = mm[j + 20]
            j += 4 + mlen
            blen = self._u32(j); j += 4 + blen
            nl = mm[j]; nom = mm[j + 1:j + 1 + nl].decode("macroman", "replace"); j += 1 + nl; j += (-(1 + nl)) % 4
            extres = {}
            while j < e0 + extra:
                k4 = mm[j + 4:j + 8][::-1].decode("latin1")
                if k4 in K64:
                    L = self._u64(j + 8); j += 16
                else:
                    L = self._u32(j + 8); j += 12
                if k4 == "luni":
                    nn = self._u32(j); nom = mm[j + 4:j + 4 + 2 * nn].decode("utf-16-le", "replace")
                if k4 == "lsct":
                    extres["seccio"] = self._u32(j)
                extres[k4] = L
                j += L + (L & 1)
            j = e0 + extra
            capes.append(dict(idx=k, nom=nom, rect=rect, mrect=mrect, mdef=mdef, canals=canals, blend=blend,
                              opac=opac, clip=clip, flags=flags, visible=not (flags & 2), extres=extres))
        pos = j
        for c in capes:
            for ch in c["canals"]:
                cid, clen = ch
                comp = self._u16(pos)
                ch.append(comp); ch.append(pos + 2); ch.append(clen - 2)   # [cid, clen, comp, data_off, data_len]
                pos += clen
        self.capes = capes
        self.n_signed = n_signed

    def canal(self, k, cid):
        """array uint16 (h, w) del canal `cid` de la capa k (0=R, 1=G, 2=B, -1=alfa, -2=màscara)."""
        c = self.capes[k]
        for ch in c["canals"]:
            if ch[0] == cid:
                _, clen, comp, doff, dlen = ch
                break
        else:
            return None
        if cid == -2 and c["mrect"]:
            t, l, b, r = c["mrect"]
        else:
            t, l, b, r = c["rect"]
        h, w = b - t, r - l
        dat = bytes(self.mm[doff:doff + dlen])
        raw = decompress(dat, comp, w, h, 16, version=2)
        arr = np.frombuffer(raw, dtype=">u2").reshape(h, w)
        # comprovació d'endianitat pel gradient entre veïns
        s = arr[::64, ::64].astype(np.int32)
        g_be = float(np.mean(np.abs(np.diff(s, axis=1))))
        s2 = arr.byteswap()[::64, ::64].astype(np.int32)
        g_le = float(np.mean(np.abs(np.diff(s2, axis=1))))
        if g_le < g_be:
            arr = arr.byteswap()
        return np.ascontiguousarray(arr.astype(np.uint16))

    def rgb(self, k):
        return np.stack([self.canal(k, i) for i in range(3)], -1)

    def resum(self):
        out = [f"{self.path}: llenç {self.shape[1]}x{self.shape[0]}, bloc {self.key} de {self.blk_len} bytes, longituds de {self.mode} bytes, {len(self.capes)} capes"]
        for c in self.capes:
            t, l, b, r = c["rect"]
            out.append(f"  [{c['idx']}] {c['nom']!r:45s} {c['blend']} op={100*c['opac']/255:.0f}% {'vis' if c['visible'] else 'OCULTA'} "
                       f"rect(top,left,bottom,right)={c['rect']} {r-l}x{b-t} canals={[ (ch[0], ch[2]) for ch in c['canals']]}"
                       + (f" màscara={c['mrect']} def={c['mdef']}" if c['mrect'] else ""))
        return "\n".join(out)
