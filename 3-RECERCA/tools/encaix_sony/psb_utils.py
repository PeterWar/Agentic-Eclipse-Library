"""Utilitats per escriure un PSB (Photoshop Large Document) de 16 bits amb capes de píxels + màscara,
sobre psd-tools 1.18. Els canals de color es passen com a numpy uint16 (H, W, 3); la màscara com a
uint8 (H, W), que aquí es converteix a 16 bits: ⚠️ psd-tools (`create_mask`) escriu les màscares
sempre a 8 bits i diu que el PSD ho fa així, però és FALS als documents de 16 bits: Photoshop hi
desa la màscara a 16 bits (comprovat amb UnintCapes3.psb: el canal de màscara descomprimeix a
W×H×2 bytes, i el mateix psd-tools la llegeix amb la profunditat del document). Amb `create_mask`
la màscara surt amb mitja fila cada fila."""
import numpy as np
from PIL import Image
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import Compression, ChannelID, BlendMode, Resource
from psd_tools.psd.layer_and_mask import LayerRecord, ChannelInfo, ChannelData, ChannelDataList
from psd_tools.psd.image_resources import ImageResource, ImageResources
from psd_tools.psd.image_data import ImageData


def new_psb(width, height, icc_bytes=None, resources_from=None):
    """Document RGB 16 bits, versió 2 (PSB). Copia (opcionalment) els recursos d'un altre document
    (ICC, resolució, etc.) i sobreescriu l'ICC si es dona."""
    psd = PSDImage.new('RGB', (width, height), color=0, depth=16)
    psd._record.header.version = 2
    if resources_from is not None:
        keep = (Resource.RESOLUTION_INFO, Resource.ICC_PROFILE, Resource.PRINT_FLAGS, Resource.PIXEL_ASPECT_RATIO,
                Resource.GLOBAL_ANGLE, Resource.GLOBAL_ALTITUDE, Resource.BACKGROUND_COLOR, Resource.PRINT_SCALE)
        for k in keep:
            if k in resources_from._record.image_resources:
                psd._record.image_resources[k] = resources_from._record.image_resources[k]
    if icc_bytes is not None:
        psd._record.image_resources[Resource.ICC_PROFILE] = ImageResource(signature=b'8BIM', key=Resource.ICC_PROFILE, name='', data=icc_bytes)
    return psd


def add_pixel_layer(psd, rgb16, name, top=0, left=0, mask8=None, blend=BlendMode.NORMAL, opacity=255, visible=True,
                    compression=Compression.ZIP, parent=None):
    """rgb16: uint16 (H, W, 3). mask8: uint8 (H, W) o None (mateixa mida i posició que la capa)."""
    parent = parent if parent is not None else psd
    H, W = rgb16.shape[:2]
    version = psd._record.header.version
    rec = LayerRecord(top=top, left=left, bottom=top + H, right=left + W, channel_info=[])
    from psd_tools.psd.tagged_blocks import TaggedBlocks
    rec.tagged_blocks = TaggedBlocks()
    rec.name = name
    chans = ChannelDataList()
    # transparència (opaca)
    cd = ChannelData(compression)
    cd.set_data(np.full((H, W), 65535, np.uint16).astype('>u2').tobytes(), W, H, 16, version)
    rec.channel_info.append(ChannelInfo(ChannelID.TRANSPARENCY_MASK, len(cd.data) + 2)); chans.append(cd)
    for c in range(3):
        cd = ChannelData(compression)
        cd.set_data(np.ascontiguousarray(rgb16[..., c]).astype('>u2').tobytes(), W, H, 16, version)
        rec.channel_info.append(ChannelInfo(ChannelID(c), len(cd.data) + 2)); chans.append(cd)
    layer = PixelLayer(parent, rec, chans)
    parent.append(layer)
    layer.name = name          # posa també el nom Unicode ('luni'), com fa Photoshop
    if mask8 is not None:
        assert mask8.shape == (H, W)
        add_mask16(layer, (mask8.astype(np.uint16) * 257), top=top, left=left, compression=compression)
    layer.blend_mode = blend
    layer.opacity = int(opacity)
    layer.visible = bool(visible)
    return layer


def set_merged(psd, rgb16, compression=Compression.RAW):
    """Posa la imatge fusionada (previsualització) del document i marca que no cal recompondre."""
    H, W = rgb16.shape[:2]
    assert (W, H) == (psd.width, psd.height)
    idata = ImageData(compression=compression)
    idata.set_data([np.ascontiguousarray(rgb16[..., c]).astype('>u2').tobytes() for c in range(3)], psd._record.header)
    psd._record.image_data = idata
    psd._updated = False
    return idata


def finalize_lr16(psd):
    """Com fa Photoshop als documents de 16 bits: les capes van al bloc 'Lr16' i la secció clàssica
    queda buida. Cal cridar-ho DESPRÉS de l'últim append/create_mask i ABANS de set_merged/save."""
    from psd_tools.constants import Tag
    from psd_tools.psd.layer_and_mask import LayerInfo, LayerInfoBlock
    from psd_tools.psd.tagged_blocks import TaggedBlocks
    psd._update_record()
    lm = psd._record.layer_and_mask_information
    li = lm.layer_info
    if lm.tagged_blocks is None:
        lm.tagged_blocks = TaggedBlocks()
    # set_data construeix la classe registrada amb els arguments posicionals (no accepta una instància)
    lm.tagged_blocks.set_data(Tag.LAYER_16, li.layer_count, li.layer_records, li.channel_image_data)
    lm.layer_info = LayerInfo()
    return lm.tagged_blocks.get_data(Tag.LAYER_16)


def add_mask16(layer, mask16, top, left, compression=Compression.ZIP_WITH_PREDICTION):
    """Màscara de capa a 16 bits (mask16: uint16 (H, W), 65535 = opac/visible), com fa Photoshop als
    documents de 16 bits. Rèplica de Layer.create_mask amb el canal a la profunditat del document."""
    from psd_tools.psd.layer_and_mask import MaskData, MaskFlags
    H, W = mask16.shape
    version = layer._psd._record.header.version
    cd = ChannelData(compression)
    cd.set_data(np.ascontiguousarray(mask16).astype('>u2').tobytes(), W, H, 16, version)
    layer._record.mask_data = MaskData(top=top, left=left, bottom=top + H, right=left + W, background_color=0, flags=MaskFlags())
    layer._record.channel_info.append(ChannelInfo(id=ChannelID.USER_LAYER_MASK, length=len(cd.data) + 2))
    layer._channels.append(cd)
    if hasattr(layer, '_mask'):
        del layer._mask
    layer._psd._mark_updated()
    return layer.mask
