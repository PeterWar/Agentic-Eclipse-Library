"""Fail-closed provenance gate for the declared V110 tower reconstruction.

Checks delivered pixels and records, never layer names as evidence. A structure
pass is not a scientific pass. Full pass additionally requires paired native
renders and exact native composite readback. The contract is frozen separately.
"""
from pathlib import Path
import argparse, copy, hashlib, io, json, sys, struct
import numpy as np
import tifffile
from psd_tools.constants import Tag

ROOT = Path(__file__).resolve().parents[3]
CONTRACT_SHA256 = '839f2468705eb8e1dd55b19d84670913bb2c2de5ff2d6e71d27186b4cc2ae0b5'
sys.path.insert(0, str(ROOT / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, llegeix_registres, rid, q_blocs, sha, renomena
from psd_tools.psd.image_resources import ImageResources
from psd_tools.constants import Resource


def inventory(actual, base):
    """Exact order and complete allowlist, including invisible extra layers."""
    expected = base + [410, 411, 308]
    return [] if actual == expected else [dict(
        check='exact_layer_inventory_and_order', expected=expected, actual=actual,
        unexpected=sorted(set(actual) - set(expected)),
        missing=sorted(set(expected) - set(actual)))]


def record_bytes(r):
    r = copy.deepcopy(r)
    for c in r.channel_info:
        c.length = 0  # Compression size is not layer content.
    if Tag.METADATA_SETTING in r.tagged_blocks:
        for item in r.tagged_blocks[Tag.METADATA_SETTING].data:
            if item.key == b'cust' and b'layerTime' in item.data:
                item.data[b'layerTime'].value = 0
    out = io.BytesIO()
    r.write(out, version=2)
    return out.getvalue()


def same_array(a, b):
    # TIFF is big-endian; the PSB decoder returns native-endian uint16.
    # Compare equal numeric types/values, not their byte-order marker.
    if a.shape != b.shape or (a.dtype.kind, a.dtype.itemsize) != (b.dtype.kind, b.dtype.itemsize):
        return False
    return all(np.array_equal(a[y:y+256], b[y:y+256])
               for y in range(0, a.shape[0], 256))


def colour(path):
    with open(path, 'rb') as f:
        header = f.read(26)
        n = struct.unpack('>I', f.read(4))[0]
        f.seek(n, 1)
        resources = ImageResources.read(f)
    return struct.unpack('>H', header[24:26])[0], resources.get_data(Resource.ICC_PROFILE)


def channel_digest(p, lid, cid):
    off, size = p.layer(lid)['chans'][cid]
    h = hashlib.sha256()
    with open(p.path, 'rb') as f:
        f.seek(off)
        while size:
            x = f.read(min(size, 8 << 20))
            if not x:
                raise IOError('Short channel')
            h.update(x)
            size -= len(x)
    return h.digest()


def paired_evidence(e, c, base, check):
    """Verify actual staged channels and recompute native response, not booleans."""
    stages = [PSB(e['files'][key]['path']) for key in ('control_stage', 'candidate_stage')]
    a, z = stages
    base_ids = [l['id'] for l in base.layers]
    if not all(check(not inventory([l['id'] for l in p.layers], base_ids),
                     'paired_stage_inventory', file=p.path) for p in stages):
        return {}
    rr = [{rid(r): r for r, _ in llegeix_registres(Path(p.path))['recs']} for p in stages]
    manual = PSB(c['manual']['path'])
    source_records = {s.path: {rid(r): r for r, _ in llegeix_registres(Path(s.path))['recs']}
                      for s in (base, manual)}
    for lid in [l['id'] for l in a.layers]:
        src = manual if lid == 308 else base
        sid = {410: 41, 411: 42}.get(lid, lid)
        wanted_record = copy.deepcopy(source_records[src.path][sid])
        if lid in (410, 411):
            wanted_record.tagged_blocks.set_data(Tag.LAYER_ID, lid)
            wanted_record.flags.visible = False
            renomena(wanted_record, c['original_names'][str(lid)])
        elif lid == 307:
            wanted_record.flags.visible = False
        elif lid in (41, 42):
            renomena(wanted_record, c['replacement'][str(lid)]['name'])
        check(record_bytes(rr[1][lid]) == record_bytes(wanted_record),
              'candidate_stage_metadata_matches_frozen_source', layer=lid)
        zr = copy.deepcopy(rr[1][lid])
        if lid in (41, 42):
            zr.name = rr[0][lid].name
            zr.tagged_blocks[Tag.UNICODE_LAYER_NAME] = copy.deepcopy(rr[0][lid].tagged_blocks[Tag.UNICODE_LAYER_NAME])
        check(record_bytes(rr[0][lid]) == record_bytes(zr), 'paired_metadata', layer=lid)
        ac, zc = set(a.layer(lid)['chans']), set(z.layer(lid)['chans'])
        if not check(ac == zc, 'paired_channel_inventory', layer=lid):
            continue
        wanted = q_blocs(np.load(c['replacement'][str(lid)]['path'], mmap_mode='r')) if lid in (41, 42) else None
        for cid in ac:
            if lid in (41, 42) and cid in (0, 1, 2):
                check(channel_digest(a, lid, cid) == channel_digest(base, lid, cid),
                      'control_origin_is_original', layer=lid, channel=cid)
                check(same_array(z.channel(lid, cid)[0], wanted),
                      'candidate_origin_is_recomputed', layer=lid, channel=cid)
            else:
                check(channel_digest(a, lid, cid) == channel_digest(z, lid, cid),
                      'paired_unchanged_channel', layer=lid, channel=cid)
                check(channel_digest(z, lid, cid) == channel_digest(src, sid, cid),
                      'candidate_stage_channel_matches_frozen_source', layer=lid, channel=cid)
        del wanted
    # Four complete native renders: active stack and 239/241 disabled.
    keys = ('control_render', 'candidate_render', 'control_without_adjustments', 'candidate_without_adjustments')
    imgs = [tifffile.memmap(e['files'][k]['path']) for k in keys]
    shape = (base.height, base.width, 3)
    if not check(all(x.shape == shape and x.dtype.kind == 'u' and x.dtype.itemsize == 2 for x in imgs), 'native_shapes_depth'):
        return {}
    effect = response = 0
    maxresponse = 0
    for y in range(0, base.height, 128):
        p, q, p0, q0 = [x[y:y+128].astype(np.int32) for x in imgs]
        delta = q-p
        downstream = delta-(q0-p0)
        effect += int(np.any(delta != 0, axis=2).sum())
        response += int(np.any(downstream != 0, axis=2).sum())
        maxresponse = max(maxresponse, int(np.max(np.abs(downstream))))
    check(effect > 0, 'correction_reaches_composite')
    check(response > 0, 'real_downstream_adjustment_response')
    for k in ('control_log', 'candidate_log', 'control_off_log', 'candidate_off_log'):
        log = Path(e['files'][k]['path']).read_text()
        check('COMPLET' in log and 'ERROR' not in log, 'native_render_completed', log=k)
    routes = [('control', 'control_stage', 'control_render', []),
              ('candidate', 'candidate_stage', 'candidate_render', []),
              ('control_off', 'control_stage', 'control_without_adjustments', [239, 241]),
              ('candidate_off', 'candidate_stage', 'candidate_without_adjustments', [239, 241])]
    for prefix, stage, render, hidden in routes:
        jsx = Path(e['files'][prefix+'_jsx']['path']).read_text()
        folder = str(Path(e['files'][render]['path']).parent)
        binding = ('var SRC=new File('+json.dumps(e['files'][stage]['path'])+'),DIR=new Folder('
                   +json.dumps(folder)+'),HIDE='+json.dumps(hidden)+';')
        check(binding in jsx, 'native_render_source_and_hidden_ids_binding', render=render)
    return dict(candidate_effect_pixels=effect, adjustment_response_pixels=response,
                maximum_adjustment_response_DN=maxresponse)


def gate(path, contract_path, native=None):
    c = json.loads(contract_path.read_text())
    report = dict(file=str(path), sha256=sha(path),
                  contract_sha256=sha(contract_path), gate_sha256=sha(Path(__file__)),
                  status='FAIL', scientific_status='NOT_ASSESSED', failures=[], layers=[])
    failures = report['failures']
    def check(ok, label, **data):
        if not ok:
            failures.append(dict(check=label, **data))
        return ok
    # The implementation's roles cannot be expanded by editing an allowlist.
    check(report['contract_sha256'] == CONTRACT_SHA256, 'frozen_contract_hash')
    check(c.get('schema') == 'torre-pisa-v110-1', 'contract_schema')
    sources = {}
    for role in ('base', 'manual'):
        spec = c[role]
        check(sha(spec['path']) == spec['sha256'], 'source_hash', role=role)
        sources[role] = PSB(spec['path'])
    for lid in (41, 42):
        spec = c['replacement'][str(lid)]
        check(sha(spec['path']) == spec['sha256'], 'operator_hash', layer=lid)
    if failures:
        return report
    p, b, m = PSB(str(path)), sources['base'], sources['manual']
    failures.extend(inventory([l['id'] for l in p.layers], [l['id'] for l in b.layers]))
    check((p.width, p.height, p.depth) == (b.width, b.height, b.depth), 'canvas_depth')
    check(p.channels in (3, 4), 'RGB_or_RGB_with_merged_alpha')
    check(colour(path) == colour(b.path), 'colour_mode_and_exact_ICC_profile')
    # Negative controls stop here instead of decoding 10 GB of irrelevant data.
    if failures:
        return report
    records = {rid(r): r for r, _ in llegeix_registres(path)['recs']}
    refs = {role: {rid(r): r for r, _ in llegeix_registres(Path(s.path))['recs']}
            for role, s in sources.items()}
    jobs = [(l['id'], 'base', l['id']) for l in b.layers]
    jobs += [(410, 'base', 41), (411, 'base', 42), (308, 'manual', 308)]
    for lid, role, source_id in jobs:
        src = sources[role]
        wanted = copy.deepcopy(refs[role][source_id])
        if lid in (410, 411):
            wanted.tagged_blocks.set_data(Tag.LAYER_ID, lid)
            wanted.flags.visible = False
            renomena(wanted, c['original_names'][str(lid)])
        elif lid == 307:
            wanted.flags.visible = False
        elif lid in (41, 42):
            renomena(wanted, c['replacement'][str(lid)]['name'])
        check(record_bytes(records[lid]) == record_bytes(wanted),
              'all_metadata_except_compression_and_native_layerTime', layer=lid)
        channels = set(src.layer(source_id)['chans'])
        check(set(p.layer(lid)['chans']) == channels, 'channel_inventory', layer=lid)
        raster = None
        if lid in (41, 42):
            raster = q_blocs(np.load(c['replacement'][str(lid)]['path'], mmap_mode='r'))
        samples, changed = 0, 0
        for cid in sorted(channels):
            a, origin_a = src.channel(source_id, cid)
            z, origin_z = p.channel(lid, cid)
            expected = raster if raster is not None and cid in (0, 1, 2) else a
            check(origin_a == origin_z and same_array(expected, z),
                  'decoded_pixels_and_origin', layer=lid, channel=cid)
            if raster is not None and cid == 0:
                changed = sum(int(np.count_nonzero(a[y:y+256] != z[y:y+256]))
                              for y in range(0, len(a), 256))
                check(changed > 0, 'origin_layer_must_actually_change', layer=lid)
            samples += z.size
            del a, z
        del raster
        report['layers'].append(dict(id=lid, source=role, source_id=source_id,
                                     channels=len(channels), samples=samples,
                                     changed_source_pixels=changed))
        print('checked layer', lid, flush=True)
    if not failures:
        report['status'] = 'STRUCTURE_PASS'
    if native is not None and not failures:
        e = json.loads(native.read_text())
        check(e['delivered_sha256'] == report['sha256'], 'native_delivery_binding')
        check(e['contract_sha256'] == report['contract_sha256'], 'native_contract_binding')
        for spec in e['files'].values():
            check(sha(spec['path']) == spec['sha256'], 'native_file_hash', path=spec['path'])
        if not failures:
            report['native_dependency'] = paired_evidence(e, c, b, check)
        if not failures:
            view = tifffile.memmap(e['files']['final_render']['path'])
            composite = p.composite()
            check(same_array(composite[..., :3], view), 'ImageData_equals_native_full_render')
            if p.channels == 4:
                alpha = composite[..., 3]
                amin, amean = int(alpha.min()), float(alpha.mean())
                # Same established acceptance criterion as p6, applied to ALL
                # samples here rather than p6's stride-7 diagnostic sampling.
                check(amin > 60000 and amean > 65000, 'merged_alpha_full_canvas_matches_p6_policy')
                report['merged_alpha'] = dict(min=amin, mean=amean, max=int(alpha.max()),
                                              policy='existing p6: min>60000,mean>65000; full canvas')
            del composite
            check(same_array(view, tifffile.memmap(e['files']['candidate_render']['path'])),
                  'saved_delivery_equals_paired_candidate')
        if not failures:
            report['status'] = 'METHOD_AND_NATIVE_PASS'
    if failures:
        report['status'] = 'FAIL'
    return report


def selftest():
    base = [3, 41, 307, 42, 239, 241, 242]
    good = base + [410, 411, 308]
    cases = {'valid_inventory': good, 'renamed_patch_new_id': good+[9123],
             'hidden_untraced_layer': good+[9124], 'missing_308': good[:-1],
             'reordered_origin': [3, 42, 307, 41, 239, 241, 242, 410, 411, 308],
             'duplicate_allowed_id': good+[308]}
    result = {name: ('REJECT' if inventory(ids, base) else 'ACCEPT')
              for name, ids in cases.items()}
    assert result['valid_inventory'] == 'ACCEPT'
    assert all(v == 'REJECT' for k, v in result.items() if k != 'valid_inventory')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('psb', nargs='?', type=Path)
    ap.add_argument('--contract', type=Path)
    ap.add_argument('--native', type=Path)
    ap.add_argument('--output', type=Path)
    ap.add_argument('--selftest', action='store_true')
    args = ap.parse_args()
    if args.selftest:
        selftest()
    else:
        if not (args.psb and args.contract and args.output):
            ap.error('psb, --contract and --output are required')
        try:
            r = gate(args.psb.resolve(), args.contract.resolve(), args.native)
        except Exception as exc:
            r = dict(status='FAIL', failures=[dict(check='unhandled_input_or_read_error',
                                                   error=repr(exc))])
        args.output.write_text(json.dumps(r, ensure_ascii=False, indent=2)+'\n')
        print(r['status'], args.output)
        sys.exit(1 if r['status'] == 'FAIL' else 0)
