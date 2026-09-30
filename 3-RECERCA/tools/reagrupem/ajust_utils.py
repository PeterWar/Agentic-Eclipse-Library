"""Capes d'AJUST de veritat (Nivells, Corbes, Exposició) en un PSB.

`psd_tools` només les llegeix; aquí es CREEN. Provades el 26-08 amb anada i
tornada: `Nivells`, `Corbes` i `Exposició` es tornen a llegir amb el seu
`kind` correcte. ⛔ `BrightnessContrast` NO: torna com a `pixel`, o sigui que
el bloc no queda reconegut, i per això no s'hi posa.

Van amb valors d'IDENTITAT: no toquen res fins que Pere hi posa la mà. És el
que demanava («uns filtres d'ajust»).
"""
from __future__ import annotations

from psd_tools.api.layers import AdjustmentLayer
from psd_tools.constants import BlendMode, ChannelID, Compression, Tag
from psd_tools.psd.adjustments import (Curves, CurvesExtraItem, CurvesExtraMarker,
                                       Exposure, LevelRecord, Levels)
from psd_tools.psd.layer_and_mask import (ChannelData, ChannelDataList, ChannelInfo,
                                          LayerRecord)
from psd_tools.psd.tagged_blocks import TaggedBlock, TaggedBlocks

IDENTITAT = {
    "Nivells": (Tag.LEVELS,
                lambda: Levels([LevelRecord(0, 255, 0, 255, 100) for _ in range(29)],
                               version=2)),
    "Corbes": (Tag.CURVES,
               lambda: Curves(is_map=False, version=1, count_map=1,
                              data=[[(0, 0), (255, 255)]],
                              extra=CurvesExtraMarker(
                                  [CurvesExtraItem(channel_id=0,
                                                   points=[(0, 0), (255, 255)])],
                                  version=4))),
    "Exposició": (Tag.EXPOSURE,
                  lambda: Exposure(version=1, exposure=0.0, offset=0.0, gamma=1.0)),
}


def afegeix_ajust(psd, nom: str, mena: str, visible: bool = False):
    tag, fab = IDENTITAT[mena]
    H, W = psd.height, psd.width
    rec = LayerRecord(top=0, left=0, bottom=H, right=W, channel_info=[])
    tb = TaggedBlocks(); tb[tag] = TaggedBlock(key=tag.value, data=fab())
    rec.tagged_blocks = tb; rec.name = nom
    chans = ChannelDataList()
    for cid in (ChannelID.TRANSPARENCY_MASK, ChannelID(0), ChannelID(1), ChannelID(2)):
        cd = ChannelData(Compression.RAW)
        cd.set_data(b"", 0, 0, 16, psd._record.header.version)
        rec.channel_info.append(ChannelInfo(cid, len(cd.data) + 2)); chans.append(cd)
    lay = AdjustmentLayer(psd, rec, chans)
    psd.append(lay); lay.name = nom
    lay.blend_mode = BlendMode.NORMAL; lay.opacity = 255; lay.visible = visible
    return lay
