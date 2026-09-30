"""Verificació de només lectura de ``CapesTotalsV2b``.

Reobre el candidat i comprova, contra Corretgint2 i CapesTotalsV1 (pins de
``build_capes_totals_v2``):

(a) hash cru de cada canal RGB/alfa de cada capa == font;
(b) hash cru de la màscara de cada capa == font;
(c) bbox i bbox de màscara == font + offset declarat;
(f) merged RGBA del fitxer == compost offline de les capes visibles a <=1 DN;
(g) cap capa visible fora del fonament (3, 4, 5, 7);
(h) estructura: PSB RGB16 RGBA4, Lr16+Mt16, secció clàssica buida, ICC Display
    P3, ordre d'IDs, cap grup/efecte/Smart Object, tot Normal, fill 100 %,
    opacitat 100 %, noms i visibilitat de la declaració, LayerRecord cru idèntic
    a les capes no tocades.

Les proves d'imatge (estrelles i limbe) són a part (``qa_imatge_v2b.py``).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, ChannelID, Resource, Tag

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_capes_totals_v2 as base  # noqa: E402
import build_capes_totals_v2b as v2b  # noqa: E402

FONAMENT = (3, 4, 5, 7)


def layer_record_sha256(layer, *, version: int = 2) -> str:
    stream = io.BytesIO()
    layer._record.write(stream, encoding="macroman", version=version)
    return hashlib.sha256(stream.getvalue()).hexdigest()


def verify(candidate_path: Path, offsets_path: Path, config_path: Path, work_dir: Path,
           corretgint2_path: Path, capes_totals_v1_path: Path) -> dict[str, object]:
    offsets = v2b.load_offsets(offsets_path)
    with config_path.open("r", encoding="utf-8") as stream:
        config = json.load(stream)
    c2 = PSDImage.open(corretgint2_path)
    ct1 = PSDImage.open(capes_totals_v1_path)
    base._validate_file_pin(corretgint2_path, base.CORRETGINT2_SIZE, base.CORRETGINT2_SHA256)
    base._validate_file_pin(capes_totals_v1_path, base.CAPES_TOTALS_V1_SIZE, base.CAPES_TOTALS_V1_SHA256)
    source = {layer.layer_id: layer for layer in c2 if layer.layer_id in base.CORRETGINT2_LAYER_IDS}
    source.update({layer.layer_id: layer for layer in ct1 if layer.layer_id in base.CAPES_TOTALS_SOURCE_IDS})

    cand = PSDImage.open(candidate_path)
    header = cand._record.header
    checks: dict[str, object] = {}
    # (h) estructura
    actual_header = (header.version, header.depth, header.channels, cand.width, cand.height, int(cand.color_mode))
    if actual_header != (2, 16, 4, base.WIDTH, base.HEIGHT, 3):
        raise AssertionError(f"capçalera inesperada: {actual_header}")
    tags = base.document_layer_tags(cand)
    if Tag.LAYER_16 not in tags or Tag.SAVING_MERGED_TRANSPARENCY16 not in tags:
        raise AssertionError("falta Lr16 o Mt16")
    classic = cand._record.layer_and_mask_information.layer_info
    if classic is None or classic.layer_count != 0:
        raise AssertionError("la secció clàssica de capes no és buida")
    icc = cand.image_resources.get_data(Resource.ICC_PROFILE)
    if hashlib.sha256(icc).hexdigest() != base.DISPLAY_P3_ICC_SHA256:
        raise AssertionError("ICC Display P3 no preservat")
    layers = list(cand)
    if tuple(l.layer_id for l in layers) != base.OUTPUT_LAYER_IDS:
        raise AssertionError(f"ordre/selecció incorrectes: {[l.layer_id for l in layers]}")
    if any(base.layer_has_forbidden_structure(l) for l in layers):
        raise AssertionError("hi ha grup, efecte, Smart Object o capa no píxel")
    checks["h_estructura"] = "PASS"

    per_layer: dict[str, object] = {}
    for layer in layers:
        lid = layer.layer_id
        src = source[lid]
        dx, dy = offsets.get(lid, (0, 0))
        # (a)+(b): canals crus (RGB, alfa i màscara)
        if base.raw_channel_fingerprints(layer) != base.raw_channel_fingerprints(src):
            raise AssertionError(f"layer_id={lid}: canals crus divergents de la font")
        # màscara decodificada (hash u16) == font
        m_c, md_c = base._decoded_mask_u16(layer, header)
        m_s, md_s = base._decoded_mask_u16(src, src._psd._record.header)
        if (m_c is None) != (m_s is None):
            raise AssertionError(f"layer_id={lid}: presència de màscara divergent")
        mask_hash = None
        if m_c is not None:
            mask_hash = base.sha256_u16_be(np.asarray(m_c))
            if mask_hash != base.sha256_u16_be(np.asarray(m_s)):
                raise AssertionError(f"layer_id={lid}: màscara decodificada divergent")
            if md_c.background_color != md_s.background_color:
                raise AssertionError(f"layer_id={lid}: background de màscara divergent")
        # (c) bbox i bbox de màscara == font + offset
        exp_bbox = (src.left + dx, src.top + dy, src.right + dx, src.bottom + dy)
        if tuple(layer.bbox) != exp_bbox:
            raise AssertionError(f"layer_id={lid}: bbox {layer.bbox} != {exp_bbox}")
        exp_mask_bbox = None
        if md_s is not None:
            exp_mask_bbox = (md_s.left + dx, md_s.top + dy, md_s.right + dx, md_s.bottom + dy)
            if (md_c.left, md_c.top, md_c.right, md_c.bottom) != exp_mask_bbox:
                raise AssertionError(f"layer_id={lid}: bbox de màscara divergent")
        # (h) estat
        exp_name = config["name_overrides"].get(str(lid), src.name)
        exp_vis = config["visibility"][str(lid)]
        if layer.name != exp_name or layer.visible != exp_vis:
            raise AssertionError(f"layer_id={lid}: nom o visibilitat divergents")
        if layer.blend_mode != BlendMode.NORMAL or layer.fill_opacity != 255 or layer.opacity != 255:
            raise AssertionError(f"layer_id={lid}: no és Normal/100 %/fill 100 %")
        untouched = lid not in offsets and str(lid) not in config["name_overrides"] and str(lid) not in config["opacity_overrides"]
        if untouched and layer_record_sha256(layer) != layer_record_sha256(src):
            raise AssertionError(f"layer_id={lid}: LayerRecord cru divergent en una capa no tocada")
        per_layer[str(lid)] = {
            "name": layer.name, "visible": layer.visible, "opacity": layer.opacity,
            "bbox": list(layer.bbox), "mask_bbox": None if exp_mask_bbox is None else list(exp_mask_bbox),
            "offset": [dx, dy], "channels": base.raw_channel_fingerprints(layer), "mask_decoded_sha256": mask_hash,
            "layer_record_identical_to_source": layer_record_sha256(layer) == layer_record_sha256(src),
        }
    checks["a_b_c_canals_mascares_bbox"] = "PASS"
    # (g)
    visible = [l.layer_id for l in layers if l.visible]
    if tuple(visible) != FONAMENT:
        raise AssertionError(f"capes visibles {visible} != {FONAMENT}")
    checks["g_visibles"] = visible
    # (f) merged == compost offline
    merged = cand._record.image_data.get_data(header, split=True)
    if len(merged) != 4:
        raise AssertionError("merged no és RGBA4")
    with tempfile.TemporaryDirectory(dir=work_dir) as tmp:
        tmp = Path(tmp)
        rgba = base.compose_normal_rgba4_to_npy(cand, header, tmp / "f.npy", tmp / "rgba.npy")
        maxdiff = []
        for k in range(4):
            file_ch = np.frombuffer(merged[k], dtype=">u2").reshape(base.HEIGHT, base.WIDTH)
            d = 0
            for r0 in range(0, base.HEIGHT, 256):
                r1 = min(base.HEIGHT, r0 + 256)
                d = max(d, int(np.abs(file_ch[r0:r1].astype(np.int32) - rgba[r0:r1, :, k].astype(np.int32)).max()))
            maxdiff.append(d)
        del rgba
    if max(maxdiff) > 1:
        raise AssertionError(f"merged divergeix del compost offline: max diff {maxdiff}")
    checks["f_merged_vs_compost_maxdiff_DN"] = maxdiff
    checks["f_merged_channel_sha256"] = [hashlib.sha256(ch).hexdigest() for ch in merged]
    # alfa del merged a la vora (documentació de la franja descoberta per ID4/ID5)
    alpha = np.frombuffer(merged[3], dtype=">u2").reshape(base.HEIGHT, base.WIDTH)
    checks["merged_alpha_vora"] = {
        "col_7647_min": int(alpha[:, -1].min()), "fila_5352_min": int(alpha[-1].min()),
        "col_0_min": int(alpha[:, 0].min()), "fila_0_min": int(alpha[0].min()),
        "interior_min": int(alpha[1:-1, 1:-1].min()),
    }
    return {
        "status": "PASS", "candidate": {"path": str(candidate_path), "size": candidate_path.stat().st_size, "sha256": base.sha256_file(candidate_path)},
        "checks": checks, "layers": per_layer,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="QA de només lectura de CapesTotalsV2b")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--offsets", type=Path, default=HERE / "offsets_v2b.json")
    parser.add_argument("--final-config", type=Path, default=HERE / "final_config_v2b.json")
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--corretgint2", type=Path, default=base.DEFAULT_CORRETGINT2)
    parser.add_argument("--capes-totals-v1", type=Path, default=base.DEFAULT_CAPES_TOTALS_V1)
    parser.add_argument("--out", type=Path, help="rebut JSON (no-clobber)")
    args = parser.parse_args()
    receipt = verify(args.candidate.resolve(), args.offsets, args.final_config, args.work_dir.resolve(), args.corretgint2.resolve(), args.capes_totals_v1.resolve())
    if args.out is not None:
        base.write_json_no_clobber(args.out, receipt)
    print(json.dumps({"status": receipt["status"], "candidate": receipt["candidate"], "checks": receipt["checks"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
