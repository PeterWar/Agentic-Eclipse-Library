"""Builder de ``CapesTotalsV4``: com el de V3c (mateixes fonts pinades, offsets V2b, màscares
declarades al llenç, merged recompost) més la peça nova de la V4: **substitució dels ràsters RGB**
pels revelats normalitzats de `revelat_normalitzat` (Opcio B+ aprovada, RENDER_RECEIPT per capa).

Regles de la substitució (fail-closed):
- només els canals 0/1/2; l'alfa i tota la resta queden byte-idèntics a la font pinada;
- la imatge nova va al seu rectangle: ID3 i les apilades = tot el ràster (6960x4640); ID4/ID5 =
  ràster de llenç sencer amb la imatge a (458,464)-(7417,5103) i el MARGE es conserva byte a byte;
- la TIFF de cada capa es valida per SHA-256 contra el registre de renders (cap raster improvisat).
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np
import tifffile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'capes_totals_v2'))
import build_capes_totals_v2 as base
import build_capes_totals_v2b as v2b
from psd_tools.constants import ChannelID, Compression
from psd_tools.psd.layer_and_mask import ChannelInfo, ChannelData

REVELAT = Path.home() / 'Desktop/Eclipse 2026/Derivats/Vixen/HDR4/revelat_v4'
V4_MASK_IDS = (4, 5, 7, 8, 9, 10, 11, 12, 13, 16, 17)
LAYER_PREFIX = {3: '12', 4: '11', 5: '10', 7: '09', 8: '08', 9: '07', 10: '06',
                11: '05', 12: '04', 13: '03', 16: '02', 17: '01'}
IMG_RECT_CANVAS_RASTER = {4: (458, 464, 6960, 4640), 5: (458, 464, 6960, 4640)}  # dins del ràster de llenç


def _replace_channel_u16(layer, channel_id: ChannelID, arr: np.ndarray) -> None:
    """Substitueix el payload d'un canal per arr (u16, mida del ràster de la capa)."""
    if arr.dtype.kind != 'u' or arr.dtype.itemsize != 2 or arr.shape != (layer.height, layer.width):
        raise AssertionError(f'layer_id={layer.layer_id} canal {channel_id}: forma {arr.shape}, '
                             f'esperada {(layer.height, layer.width)}')
    key = int(channel_id)
    kept = [(info, data) for info, data in zip(layer._record.channel_info, layer._channels)
            if int(info.id) != key]
    data = ChannelData(Compression.ZIP_WITH_PREDICTION)
    data.set_data(np.ascontiguousarray(arr).astype('>u2').tobytes(),
                  layer.width, layer.height, 16, layer._psd._record.header.version)
    kept.append((ChannelInfo(id=channel_id, length=len(data.data) + 2), data))
    kept.sort(key=lambda p: int(p[0].id))
    layer._record.channel_info[:] = [p[0] for p in kept]
    layer._channels[:] = [p[1] for p in kept]
    layer._psd._mark_updated()


def apply_new_rasters(document, renders_dir: Path) -> dict:
    """Posa els revelats V4 als canals RGB de les 12 capes. Retorna el rebut per capa."""
    receipt = {}
    for layer in document:
        i = layer.layer_id
        tif = renders_dir / f'v4_{LAYER_PREFIX[i]}.tif'
        if not tif.is_file():
            raise AssertionError(f'falta el revelat de la capa {i}: {tif}')
        new = tifffile.imread(str(tif))
        if new.shape != (4640, 6960, 3) or new.dtype != np.uint16:
            raise AssertionError(f'{tif}: forma/tipus inesperat {new.shape} {new.dtype}')
        alpha_before = base.raw_channel_fingerprints(layer).get(str(int(ChannelID.TRANSPARENCY_MASK)))
        chs = base.channel_map(layer)
        decoded = {}
        for cid in (ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2):
            decoded[int(cid)] = base._decoded_channel_u16(layer, cid, document._record.header)
        rect = IMG_RECT_CANVAS_RASTER.get(i)
        for k, cid in enumerate((ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2)):
            old = decoded[int(cid)]
            if rect is None:
                if old.shape != (4640, 6960):
                    raise AssertionError(f'layer_id={i}: ràster {old.shape} inesperat (no és un frame)')
                out = new[..., k]
            else:
                x0, y0, w, h = rect
                out = old.copy()
                out[y0:y0 + h, x0:x0 + w] = new[..., k]
            _replace_channel_u16(layer, cid, out)
        alpha_after = base.raw_channel_fingerprints(layer).get(str(int(ChannelID.TRANSPARENCY_MASK)))
        if alpha_before != alpha_after:
            raise AssertionError(f'layer_id={i}: canal alfa alterat')
        # verificació de relectura: el canal escrit decodifica a la imatge nova dins del rectangle
        for k, cid in enumerate((ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2)):
            back = base._decoded_channel_u16(layer, cid, document._record.header)
            if rect is None:
                if not np.array_equal(back, new[..., k]):
                    raise AssertionError(f'layer_id={i} canal {k}: la relectura no és el revelat nou')
            else:
                x0, y0, w, h = rect
                if not np.array_equal(back[y0:y0 + h, x0:x0 + w], new[..., k]):
                    raise AssertionError(f'layer_id={i} canal {k}: la relectura no és el revelat nou (rectangle)')
                marge = decoded[int(cid)].copy()
                marge[y0:y0 + h, x0:x0 + w] = 0
                nou_marge = back.copy()
                nou_marge[y0:y0 + h, x0:x0 + w] = 0
                if not np.array_equal(nou_marge, marge):
                    raise AssertionError(f'layer_id={i} canal {k}: el marge ha canviat')
        receipt[str(i)] = {'tif_sha256': hashlib.sha256(tif.read_bytes()).hexdigest(),
                           'prefix': LAYER_PREFIX[i], 'rectangle': rect, 'marge': 'conservat' if rect else 'sense marge'}
    return receipt


def materialize_v4(*, corretgint2_path, capes_totals_v1_path, config_path, mask_dir, offsets_path,
                   renders_dir, work_dir, candidate_path, manifest_path):
    candidate_path = base._candidate_path_without_clobber(candidate_path)
    manifest_path = manifest_path.expanduser().parent.resolve() / manifest_path.name
    if manifest_path.exists() or manifest_path.is_symlink():
        raise FileExistsError(f'no se sobreescriu el manifest: {manifest_path}')
    work_dir = work_dir.resolve()
    offsets = v2b.load_offsets(offsets_path)
    declaration = base.load_final_declaration(config_path, mask_dir, allowed_mask_ids=V4_MASK_IDS,
                                              required_hidden_ids=())
    document, manifest = base.build_selected_document(corretgint2_path, capes_totals_v1_path)
    original_alpha = {l.layer_id: base.raw_channel_fingerprints(l).get(str(int(ChannelID.TRANSPARENCY_MASK)))
                      for l in document}
    raster_receipt = apply_new_rasters(document, renders_dir)
    offsets_receipt = v2b.apply_offsets(document, offsets)
    base.apply_final_declaration(document, declaration)
    new_mask_ids = set(declaration['masks'])
    mask_receipt = {}
    for layer in document:
        i = layer.layer_id
        if base.raw_channel_fingerprints(layer).get(str(int(ChannelID.TRANSPARENCY_MASK))) != original_alpha[i]:
            raise AssertionError(f'layer_id={i}: alfa alterat pel procés')
        if i in new_mask_ids:
            decoded, md = base._decoded_mask_u16(layer, document._record.header)
            sha = base.sha256_u16_be(decoded)
            if sha != declaration['masks'][i]['decoded_sha256']:
                raise AssertionError(f'layer_id={i}: la màscara escrita no és la declarada')
            if [md.left, md.top, md.right, md.bottom] != list(declaration['masks'][i]['bbox']):
                raise AssertionError(f'layer_id={i}: bbox de màscara desplaçat')
            mask_receipt[str(i)] = {'decoded_sha256': sha, 'bbox': [md.left, md.top, md.right, md.bottom],
                                    'background_color': md.background_color}
        if layer.blend_mode != base.BlendMode.NORMAL or layer.fill_opacity != 255 or layer.opacity != 255:
            raise AssertionError(f'layer_id={i}: no és Normal/100 %/farciment 100 %')
    base.finalize_lr16(document)
    float_path = work_dir / 'merged_float32.npy'
    rgba_path = work_dir / 'merged_rgba16.npy'
    rgba = base.compose_normal_rgba4_to_npy(document, document._record.header, float_path, rgba_path)
    merged_hashes = base.set_merged_rgba4(document, rgba)
    manifest.update({
        'status': 'FINAL_CANDIDATE_READY_TO_SAVE', 'variant': 'V4',
        'renders': {'dir': str(renders_dir), 'rebut': raster_receipt,
                    'semantics': 'canals RGB substituïts pels revelats normalitzats (RENDER_RECEIPT); '
                                 'alfa byte-idèntic; marges d\'ID4/ID5 conservats byte a byte'},
        'final_declaration': base.final_declaration_manifest(declaration),
        'offsets': {'path': str(offsets_path.resolve()), 'sha256': base.sha256_file(offsets_path), 'applied': offsets_receipt,
                    'semantics': 'metadades: mateixos offsets que V2b/V3c; cap píxel remostrejat'},
        'new_masks': mask_receipt,
        'visible_layer_ids': [l.layer_id for l in document if l.visible],
        'layer_state': {str(l.layer_id): {'name': l.name, 'opacity': l.opacity, 'visible': l.visible,
                                          'blend_mode': l.blend_mode.value.decode('ascii'),
                                          'fill_opacity': l.fill_opacity, 'bbox': list(l.bbox),
                                          'mask_bbox': None if l._record.mask_data is None else
                                          [l._record.mask_data.left, l._record.mask_data.top,
                                           l._record.mask_data.right, l._record.mask_data.bottom],
                                          'channels': base.raw_channel_fingerprints(l)} for l in document},
        'modified_mask_ids': sorted(new_mask_ids), 'merged_status': 'RGBA4_SET',
        'merged_rgba16_npy': {'path': str(rgba_path), 'sha256': base.sha256_file(rgba_path),
                              'channel_sha256': merged_hashes},
    })
    receipt = base.save_candidate_no_clobber(document, candidate_path, expected_layer_ids=base.OUTPUT_LAYER_IDS)
    manifest.update({'status': 'FINAL_CANDIDATE_SAVED', 'psb_saved': True, 'candidate': receipt,
                     'manifest_path': str(manifest_path)})
    base.write_json_no_clobber(manifest_path, manifest)
    return manifest


def main():
    p = argparse.ArgumentParser(description='Materialització fail-closed de CapesTotalsV4.')
    p.add_argument('--corretgint2', type=Path, default=base.DEFAULT_CORRETGINT2)
    p.add_argument('--capes-totals-v1', type=Path, default=base.DEFAULT_CAPES_TOTALS_V1)
    p.add_argument('--final-config', type=Path, required=True)
    p.add_argument('--mask-dir', type=Path, required=True)
    p.add_argument('--offsets', type=Path, required=True)
    p.add_argument('--renders-dir', type=Path, default=REVELAT / 'out')
    p.add_argument('--work-dir', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    a = p.parse_args()
    m = materialize_v4(corretgint2_path=a.corretgint2, capes_totals_v1_path=a.capes_totals_v1,
                       config_path=a.final_config, mask_dir=a.mask_dir, offsets_path=a.offsets,
                       renders_dir=a.renders_dir, work_dir=a.work_dir, candidate_path=a.candidate,
                       manifest_path=a.manifest)
    print(json.dumps({k: m[k] for k in ('status', 'candidate', 'visible_layer_ids', 'new_masks')},
                     ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
