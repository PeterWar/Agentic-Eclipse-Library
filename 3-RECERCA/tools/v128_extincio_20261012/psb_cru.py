"""psb_cru · Lector mínim del format PSB (Photoshop «Large Document», versió 2), escrit a mà, SENSE psd-tools.

Serveix per a dues coses de la V128:
  1. saber on és cada tros de la V125-FINAL (capçalera, recursos, bloc de capes Lr16, registres i canals de cada capa,
     blocs globals, imatge fusionada) per poder-ne fer una còpia on només canvia el que s'afegeix;
  2. comprovar el fitxer escrit amb un lector que no comparteix cap línia de codi amb psd-tools.
Només llegeix (mmap en mode de lectura). Format: Adobe Photoshop File Formats Specification (PSB: longituds de 8 bytes a
la secció de capes i màscares, a la informació de capes, a la longitud de cada canal i als blocs «grossos»).
"""
import mmap
import struct
from pathlib import Path

# Blocs amb longitud de 8 bytes en PSB (especificació d'Adobe) — a més, tot bloc amb signatura «8B64».
CLAUS_GROSSES = {b'LMsk', b'Lr16', b'Lr32', b'Layr', b'Mt16', b'Mt32', b'Mtrn', b'Alph', b'FMsk', b'lnk2', b'FEid',
                 b'FXid', b'PxSD', b'lnkE', b'lnk3', b'pths', b'anFX', b'cinf', b'extd', b'artd'}


def u16(b, o): return struct.unpack_from('>H', b, o)[0]
def i16(b, o): return struct.unpack_from('>h', b, o)[0]
def u32(b, o): return struct.unpack_from('>I', b, o)[0]
def i32(b, o): return struct.unpack_from('>i', b, o)[0]
def u64(b, o): return struct.unpack_from('>Q', b, o)[0]


class PSB:
    """Mapa de bytes d'un PSB. Totes les posicions són absolutes dins del fitxer."""

    def __init__(s, ruta):
        s.ruta = Path(ruta)
        s.fh = open(s.ruta, 'rb')
        s.b = mmap.mmap(s.fh.fileno(), 0, access=mmap.ACCESS_READ)
        b = s.b
        if b[:4] != b'8BPS':
            raise ValueError('no és un PSD/PSB')
        s.versio = u16(b, 4)
        if s.versio != 2:
            raise ValueError(f'no és PSB (versió {s.versio})')
        s.canals, s.alt, s.ample, s.bits, s.mode = u16(b, 12), u32(b, 14), u32(b, 18), u16(b, 22), u16(b, 24)
        o = 26
        s.color_mode = (o, 4 + u32(b, o)); o += 4 + u32(b, o)
        s.recursos_pos = o
        n = u32(b, o)
        s.recursos = s._recursos(o + 4, o + 4 + n)
        o += 4 + n
        s.lmi_pos = o                                   # longitud (8) de la secció de capes i màscares
        s.lmi_len = u64(b, o)
        s.lmi_fi = o + 8 + s.lmi_len
        o += 8
        s.li_pos = o                                    # informació de capes «principal» (al 16 bits sol ser buida)
        s.li_len = u64(b, o)
        o += 8 + s.li_len
        s.gmask_pos = o
        o += 4 + u32(b, o)
        s.blocs = []                                    # (signatura, clau, pos, mida_longitud, longitud, pos_dades, fi_amb_farciment)
        while o + 12 <= s.lmi_fi:
            sig, clau = bytes(b[o:o + 4]), bytes(b[o + 4:o + 8])
            if sig not in (b'8BIM', b'8B64'):
                break
            gros = sig == b'8B64' or clau in CLAUS_GROSSES
            ml = 8 if gros else 4
            ln = u64(b, o + 8) if gros else u32(b, o + 8)
            dades = o + 8 + ml
            fi = dades + ln + ((-ln) % 4)
            s.blocs.append(dict(sig=sig, clau=clau, pos=o, mida_longitud=ml, longitud=ln, dades=dades, fi=fi))
            o = fi
        s.blocs_fi = o
        s.id_pos = s.lmi_fi                             # imatge fusionada: compressió (2) + dades fins al final
        s.id_compressio = u16(b, s.id_pos)
        s.mida = len(b)
        s.capes = None
        lr = [k for k in s.blocs if k['clau'] in (b'Lr16', b'Lr32')]
        if lr:
            s.lr = lr[0]
            s.capes = s._capes(s.lr['dades'], s.lr['dades'] + s.lr['longitud'])

    def _recursos(s, o, fi):
        b, out = s.b, []
        while o < fi:
            assert b[o:o + 4] == b'8BIM', o
            rid = u16(b, o + 4)
            nl = b[o + 6]
            pn = 1 + nl; pn += pn % 2
            mida = u32(b, o + 6 + pn)
            d = o + 6 + pn + 4
            out.append(dict(id=rid, pos=o, dades=d, mida=mida, fi=d + mida + (mida % 2)))
            o = d + mida + (mida % 2)
        return out

    def _capes(s, o, fi):
        b = s.b
        s.lr_count_pos = o
        s.lr_count = i16(b, o)
        n = abs(s.lr_count)
        o += 2
        capes = []
        for _ in range(n):
            r0 = o
            top, left, bottom, right = struct.unpack_from('>4i', b, o); o += 16
            nc = u16(b, o); o += 2
            ch = []
            for _c in range(nc):
                ch.append((i16(b, o), u64(b, o + 2))); o += 10
            blend_sig, blend = bytes(b[o:o + 4]), bytes(b[o + 4:o + 8]); o += 8
            opac, clip, flags = b[o], b[o + 1], b[o + 2]; o += 4
            extra = u32(b, o); o += 4
            e0 = o
            mask_len = u32(b, o); mask_pos = o
            o2 = o + 4 + mask_len
            br_len = u32(b, o2)
            o3 = o2 + 4 + br_len
            nl = b[o3]
            nom = bytes(b[o3 + 1:o3 + 1 + nl]).decode('mac_roman')
            o = e0 + extra
            capes.append(dict(reg=(r0, o), caixa=(left, top, right, bottom), canals=ch, blend_sig=blend_sig, blend=blend,
                              opacitat=opac, clipping=clip, flags=flags, visible=not (flags & 2), nom_pascal=nom,
                              mascara=(mask_pos, 4 + mask_len), extra=(e0, extra)))
        s.registres_fi = o
        for c in capes:
            cd = []
            for cid, ln in c['canals']:
                cd.append(dict(id=cid, pos=o, longitud=ln, compressio=u16(b, o)))
                o += ln
            c['dades'] = cd
        s.canals_fi = o
        s.lr_cos_fi = fi
        return capes

    def tros(s, a, z):
        return s.b[a:z]

    def tanca(s):
        s.b.close(); s.fh.close()


def resum(p):
    return dict(versio=p.versio, canals=p.canals, alt=p.alt, ample=p.ample, bits=p.bits, mode=p.mode, mida=p.mida,
                recursos=[(r['id'], r['mida']) for r in p.recursos], lmi=(p.lmi_pos, p.lmi_len), li_principal=p.li_len,
                blocs=[(k['sig'].decode(), k['clau'].decode('latin-1'), k['longitud']) for k in p.blocs],
                blocs_fi_igual_lmi_fi=p.blocs_fi == p.lmi_fi, lmi_fi=p.lmi_fi,
                compressio_fusionada=p.id_compressio, capes=len(p.capes or []), lr_count=getattr(p, 'lr_count', None))
