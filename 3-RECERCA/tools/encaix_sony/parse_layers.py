"""Llegeix l'estructura de capes de Photoshop incrustada al TIFF (tag 37724),
en little-endian i amb longituds de 8 bytes (estil PSB), que és com ho escriu
Photoshop en un TIFF 'II'."""
import sys, struct, mmap, json
import numpy as np
import tifffile

path = sys.argv[1]
with tifffile.TiffFile(path) as t:
    tag = t.pages[0].tags[37724]
    off, cnt = tag.valueoffset, tag.count
f = open(path, 'rb')
mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
end = off + cnt
sig = b'Adobe Photoshop Document Data V0002\x00'
assert mm[off:off+len(sig)] == sig
pos = off + len(sig)

def u8(p): return mm[p]
def u16(p): return struct.unpack('<H', mm[p:p+2])[0]
def i16(p): return struct.unpack('<h', mm[p:p+2])[0]
def u32(p): return struct.unpack('<I', mm[p:p+4])[0]
def i32(p): return struct.unpack('<i', mm[p:p+4])[0]
def u64(p): return struct.unpack('<Q', mm[p:p+8])[0]
def key4(p): return mm[p:p+4][::-1].decode('latin1')

EIGHT = {'LMsk','Lr16','Lr32','Layr','Mt16','Mt32','Mtrn','Alph','FMsk','lnk2','FEid','FXid','PxSD','cinf'}

def parse_tagged_blocks(p, stop):
    out = []
    while p + 12 <= stop:
        s = key4(p)
        if s not in ('8BIM', '8B64'):
            p += 1
            continue
        k = key4(p+4)
        if k in EIGHT:
            ln = u64(p+8); hdr = 16
        else:
            ln = u32(p+8); hdr = 12
        out.append((k, p+hdr, ln))
        p = p + hdr + ln
        p += ln % 2  # padding a parell
    return out

def pascal(p):
    n = u8(p)
    return mm[p+1:p+1+n].decode('macroman', 'replace'), n

layers = []
blocks = parse_tagged_blocks(pos, end)
print('blocs de nivell superior:', [(k, ln) for k, ln, _ in [(b[0], b[2], 0) for b in blocks]])

for k, p, ln in blocks:
    if k not in ('Lr16', 'Lr32', 'Layr'):
        continue
    stop = p + ln
    count = i16(p); p += 2
    print('layer_count', count)
    recs = []
    for i in range(abs(count)):
        top, left, bottom, right = i32(p), i32(p+4), i32(p+8), i32(p+12); p += 16
        nch = u16(p); p += 2
        chans = []
        for c in range(nch):
            cid = i16(p); clen = u64(p+2); p += 10
            chans.append((cid, clen))
        assert key4(p) == '8BIM', key4(p)
        blend = key4(p+4); p += 8
        opac, clip, flags = u8(p), u8(p+1), u8(p+2); p += 4
        extra_len = u32(p); p += 4
        extra_end = p + extra_len
        # mask
        mlen = u32(p); p += 4
        mask = None
        if mlen:
            mtop, mleft, mbot, mright = i32(p), i32(p+4), i32(p+8), i32(p+12)
            mdef = u8(p+16); mflags = u8(p+17)
            mask = dict(top=mtop, left=mleft, bottom=mbot, right=mright, default=mdef, flags=mflags, len=mlen)
            p += mlen
        # blending ranges
        brl = u32(p); p += 4 + brl
        name, n = pascal(p); p += 1 + n
        p += (-(1+n)) % 4
        tbs = parse_tagged_blocks(p, extra_end)
        uni = None
        sect = None
        tbkeys = []
        for tk, tp, tl in tbs:
            tbkeys.append(tk)
            if tk == 'luni':
                nn = u32(tp)
                uni = mm[tp+4:tp+4+2*nn].decode('utf-16-le', 'replace')
            if tk == 'lsct':
                sect = u32(tp)
        p = extra_end
        rec = dict(idx=i, name=uni or name, blend=blend, opacity=opac, clipping=clip, flags=flags,
                   visible=not (flags & 2), bbox=(top, left, bottom, right), channels=chans, mask=mask,
                   section=sect, tagged=tbkeys)
        recs.append(rec)
    # channel image data follows, in order
    for rec in recs:
        rec['channel_data'] = []
        for cid, clen in rec['channels']:
            comp = u16(p)
            rec['channel_data'].append(dict(id=cid, compression=comp, offset=p+2, length=clen-2))
            p += clen
    layers = recs
    print('final de dades de canals a', p, 'stop', stop, 'diferència', stop - p)

for r in layers:
    print(f"[{r['idx']}] {r['name']!r} blend={r['blend']} opac={r['opacity']} clip={r['clipping']} vis={r['visible']} "
          f"flags={r['flags']:#04x} bbox={r['bbox']} sect={r['section']} chans={[(c['id'], c['compression'], c['length']) for c in r['channel_data']]}")
    if r['mask']: print('     mask', r['mask'])
    print('     tagged', r['tagged'])

json.dump([{k: v for k, v in r.items()} for r in layers], open('layers_index.json', 'w'), indent=1, default=str)
