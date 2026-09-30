import os, sys
from psd_tools import PSDImage
from psd_tools.constants import Tag
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/')
for fn in sys.argv[1:]:
    psd = PSDImage.open(D + fn)
    h = psd._record.header
    print('=====', fn, h.width, 'x', h.height, 'depth', h.depth, 'channels', h.channels, 'mode', h.color_mode, 'version', h.version)
    def walk(group, ind=0):
        for l in group:
            m = l.mask
            mi = ''
            if m is not None:
                mi = f' MASK bbox={m.bbox} bg={m.background_color} disabled={m.disabled} rel={getattr(m,"relative_to_layer",None)}'
                # real (vector) mask?
                md = l._record.mask_data
                if md is not None:
                    mi += f' flags={md.flags} params={getattr(md,"parameters",None)} real_flags={getattr(md,"real_flags",None)} density={getattr(md,"user_mask_density",None)} feather={getattr(md,"user_mask_feather",None)}'
            tb = l._record.tagged_blocks
            keys = [k.name if hasattr(k,'name') else str(k) for k in (tb.keys() if tb else [])]
            print(' '*ind + f'[{l.kind}] "{l.name}" bbox={l.bbox} blend={l.blend_mode} op={l.opacity} fill={getattr(l,"fill_opacity",None)} vis={l.visible} clip={l._record.clipping}{mi}')
            print(' '*ind + '    tags:', keys)
            if l.is_group():
                walk(l, ind+2)
    walk(psd)
