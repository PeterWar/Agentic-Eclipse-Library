"""Builder de ``CapesTotalsV3b``: V2b (fonts pinades Corretgint2 + CT1, offsets_v2b) + màscares noves u16 a les capes
declarades a ``masks`` del final_config + visibilitat/noms. Reutilitza ``build_capes_totals_v2b`` (offsets) i
``build_capes_totals_v2`` (clonació crua, declaració final, compositor RGBA4, promoció no-clobber). L'única diferència
amb el builder v2b és la comprovació d'integritat: a les capes amb màscara nova es verifica que RGB+alfa crus no han
canviat i que la màscara decodificada és exactament la declarada; a la resta, tots els canals (màscara inclosa) són
byte-idèntics a la font."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'capes_totals_v2'))
import build_capes_totals_v2 as base
import build_capes_totals_v2b as v2b


def materialize_v3b(*, corretgint2_path, capes_totals_v1_path, config_path, mask_dir, offsets_path, work_dir, candidate_path, manifest_path):
    candidate_path = base._candidate_path_without_clobber(candidate_path)
    manifest_path = manifest_path.expanduser().parent.resolve() / manifest_path.name
    if manifest_path.exists() or manifest_path.is_symlink():
        raise FileExistsError(f'no se sobreescriu el manifest: {manifest_path}')
    work_dir = work_dir.resolve()
    offsets = v2b.load_offsets(offsets_path)
    declaration = base.load_final_declaration(config_path, mask_dir)
    document, manifest = base.build_selected_document(corretgint2_path, capes_totals_v1_path)
    original_all = {l.layer_id: base.raw_channel_fingerprints(l) for l in document}
    original_nonmask = {l.layer_id: base.raw_nonmask_fingerprints(l) for l in document}
    base.apply_final_declaration(document, declaration)
    offsets_receipt = v2b.apply_offsets(document, offsets)
    new_mask_ids = set(declaration['masks'])
    mask_receipt = {}
    for layer in document:
        i = layer.layer_id
        if i in new_mask_ids:
            if base.raw_nonmask_fingerprints(layer) != original_nonmask[i]:
                raise AssertionError(f'layer_id={i}: RGB/alfa crus alterats')
            decoded, md = base._decoded_mask_u16(layer, document._record.header)
            sha = base.sha256_u16_be(decoded)
            if sha != declaration['masks'][i]['decoded_sha256']:
                raise AssertionError(f'layer_id={i}: la màscara escrita no és la declarada')
            mask_receipt[str(i)] = {'decoded_sha256': sha, 'bbox': [md.left, md.top, md.right, md.bottom], 'background_color': md.background_color}
        else:
            if base.raw_channel_fingerprints(layer) != original_all[i]:
                raise AssertionError(f'layer_id={i}: canal cru alterat')
        if layer.blend_mode != base.BlendMode.NORMAL or layer.fill_opacity != 255 or layer.opacity != 255:
            raise AssertionError(f'layer_id={i}: no és Normal/100 %/farciment 100 %')
    base.finalize_lr16(document)
    float_path = work_dir / 'merged_float32.npy'; rgba_path = work_dir / 'merged_rgba16.npy'
    rgba = base.compose_normal_rgba4_to_npy(document, document._record.header, float_path, rgba_path)
    merged_hashes = base.set_merged_rgba4(document, rgba)
    manifest.update({
        'status': 'FINAL_CANDIDATE_READY_TO_SAVE', 'variant': 'V3b',
        'final_declaration': base.final_declaration_manifest(declaration),
        'offsets': {'path': str(offsets_path.resolve()), 'sha256': base.sha256_file(offsets_path), 'applied': offsets_receipt,
                    'semantics': 'metadades: LayerRecord i MaskData desplaçats pel mateix vector enter; cap píxel remostrejat'},
        'new_masks': mask_receipt,
        'visible_layer_ids': [l.layer_id for l in document if l.visible],
        'layer_state': {str(l.layer_id): {'name': l.name, 'opacity': l.opacity, 'visible': l.visible, 'blend_mode': l.blend_mode.value.decode('ascii'),
                                          'fill_opacity': l.fill_opacity, 'bbox': list(l.bbox),
                                          'mask_bbox': None if l._record.mask_data is None else [l._record.mask_data.left, l._record.mask_data.top, l._record.mask_data.right, l._record.mask_data.bottom],
                                          'channels': base.raw_channel_fingerprints(l)} for l in document},
        'modified_mask_ids': sorted(new_mask_ids), 'merged_status': 'RGBA4_SET',
        'merged_rgba16_npy': {'path': str(rgba_path), 'sha256': base.sha256_file(rgba_path), 'channel_sha256': merged_hashes},
    })
    receipt = base.save_candidate_no_clobber(document, candidate_path, expected_layer_ids=base.OUTPUT_LAYER_IDS)
    manifest.update({'status': 'FINAL_CANDIDATE_SAVED', 'psb_saved': True, 'candidate': receipt, 'manifest_path': str(manifest_path)})
    base.write_json_no_clobber(manifest_path, manifest)
    return manifest


def main():
    p = argparse.ArgumentParser(description='Materialització fail-closed de CapesTotalsV3b.')
    p.add_argument('--corretgint2', type=Path, default=base.DEFAULT_CORRETGINT2)
    p.add_argument('--capes-totals-v1', type=Path, default=base.DEFAULT_CAPES_TOTALS_V1)
    p.add_argument('--final-config', type=Path, required=True)
    p.add_argument('--mask-dir', type=Path, required=True)
    p.add_argument('--offsets', type=Path, required=True)
    p.add_argument('--work-dir', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    a = p.parse_args()
    m = materialize_v3b(corretgint2_path=a.corretgint2, capes_totals_v1_path=a.capes_totals_v1, config_path=a.final_config, mask_dir=a.mask_dir,
                        offsets_path=a.offsets, work_dir=a.work_dir, candidate_path=a.candidate, manifest_path=a.manifest)
    print(json.dumps({k: m[k] for k in ('status', 'candidate', 'visible_layer_ids', 'new_masks')}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
