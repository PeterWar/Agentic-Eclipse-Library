"""B6 · V32.psb: la V31_FiltresPurs amb els 18 filtres regenerats; tota la resta byte a byte.

Parteix de V31_FiltresPurs.psb (hash comprovat). Substitueix NOMÉS els tres canals de
color de les capes de filtre (03 V29, 03 V30, 07, 01, 02, 04, 05, 06, P01–P09, C01);
alfa, màscara, geometria, mode, opacitat, visibilitat i nom (llevat del sufix · V32)
es conserven, i les 22 capes restants (les de Pere, les bases, estrelles, reflex) queden
idèntiques en registre i canals comprimits. El compost per defecte es recompon amb
les capes visibles (mateix `compose` que la V31). Es desa a staging/, es verifica
reobrint-lo i es passa per la porta Photoshop real. `--publish` el copia a Capes Totals.
"""
import os, sys, json, copy, gc, hashlib, subprocess, shutil, datetime
from pathlib import Path
os.environ['V29_FINAL_GRID'] = '1'
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'research/tools/v31')); sys.path.insert(0, str(ROOT / 'research/tools/v29_c03_fix')); sys.path.insert(0, str(ROOT / 'research/tools/v29')); sys.path.insert(0, str(ROOT / 'research/tools/encaix_sony'))
from common import *
from package_only03 import signature, global_signature, digest
from package_v31 import compose
from inspect_inputs import sha, channel
from psb_utils import finalize_lr16
from psd_tools import PSDImage
from psd_tools.constants import Compression
from psd_tools.psd.layer_and_mask import ChannelData
from psd_tools.psd.image_data import ImageData
from PIL import Image
HERE = Path(__file__).resolve().parent          # `from common import *` (v29) sobreescriu HERE: es refà aquí
CAU32 = HERE / 'cau'; PC = HERE / 'purs/cau'; STAGING = HERE / 'staging'; STAGING.mkdir(exist_ok=True)
REB = ROOT / 'output/v32_arcs_20260907/4-rebuts'; VIS = ROOT / 'output/v32_arcs_20260907/lliurables/vistes'
SRC = CT / 'V31_FiltresPurs.psb'; EXPECTED = '89d509bcc53982307cf9e3d78b0a84ed7548f4045e8cbb95d9f8594e4e877dfd'
TARGET = STAGING / 'V32.psb'; FINAL = CT / 'V32.psb'
REPLACE = {
    '03 ACHF azimutal 8-128 · V29': CAU32 / '03_v32_u16.npy',
    '03 ACHF azimutal 8-128 · V30': CAU32 / '03v30_v32_u16.npy',
    '07 ACHF azimutal suau r8 · V30': CAU32 / '07_v32_u16.npy',
    '01 ACHF fi 2-32 · V31': CAU32 / '01_v32_u16.npy',
    '02 Passa-alt 24 · V31': CAU32 / '02_v32_u16.npy',
    '04 ACHF micro 1-16 · V31': CAU32 / '04_v32_u16.npy',
    '05 ACHF fi 2-48 · V31': CAU32 / '05_v32_u16.npy',
    '06 ACHF estructura 4-64 · V31': CAU32 / '06_v32_u16.npy',
    'P01 NRGF · V31': PC / 'P01_NRGF_u16.npy',
    'P02 RHEF · comparacio amb anells · V31': PC / 'P02_RHEF_u16.npy',
    'P03 MGN · V31': PC / 'P03_MGN_u16.npy',
    'P04 WOW sense denoise · V31': PC / 'P04_WOW_u16.npy',
    'P05 WOW bilateral sense denoise · V31': PC / 'P05_WOW_bilateral_u16.npy',
    'P06 NAFE n65 · V31': PC / 'P06_NAFE_u16.npy',
    'P07 ACHF precursor sigma16 · V31': PC / 'P07_ACHF_precursor16_u16.npy',
    'P08 ACHF precursor sigma32 · V31': PC / 'P08_ACHF_precursor32_u16.npy',
    'P09 SWAP · pilot llum blanca · V31': PC / 'P09_SWAP_pilot_u16.npy',
    'C01 Passa-alt24 lineal · control · V31': PC / 'C01_Passa_alt24_lineal_u16.npy',
}


def newname(n):
    for v in (' · V29', ' · V30', ' · V31'):
        if n.endswith(v):
            return n[:-len(v)] + ' · V32'
    return n + ' · V32'


def build():
    assert not TARGET.exists(), 'staging ja existeix'
    for p in REPLACE.values():
        assert p.exists(), p
    assert sha(SRC) == EXPECTED, 'V31_FiltresPurs.psb ha canviat'
    s = PSDImage.open(SRC); ls = list(s); assert len(ls) == 40 and s.size == (FW, FH) and s.depth == 16
    rep = {'source': str(SRC), 'source_sha256': EXPECTED, 'original_layers': [signature(l) for l in ls], 'original_global': global_signature(s), 'changed': []}
    for i, l in enumerate(ls):
        if l.name not in REPLACE:
            continue
        old = rep['original_layers'][i]; u = np.load(REPLACE[l.name], mmap_mode='r'); assert u.shape == (FH, FW) and u.dtype == np.uint16
        cd = ChannelData(Compression.ZIP); cd.set_data(np.ascontiguousarray(np.asarray(u).astype('>u2')).tobytes(), FW, FH, 16, 2)
        for k, ci in enumerate(l._record.channel_info):
            if int(ci.id) in (0, 1, 2):
                l._channels[k] = copy.copy(cd); ci.length = len(cd.data) + 2
        sig = signature(l); assert sig['record_without_color_lengths_sha256'] == old['record_without_color_lengths_sha256']
        assert all(v == old['channels'][k] for k, v in sig['channels'].items() if k not in ('0', '1', '2'))
        oldname = l.name; l.name = newname(oldname)
        rep['changed'].append({'index': i, 'old_name': oldname, 'new_name': l.name, 'source_u16': str(REPLACE[oldname]), 'u16_sha256': sha(REPLACE[oldname]), 'signature': signature(l)})
        log(f'RGB substituït {i} {l.name}'); del u, cd; gc.collect()
    assert len(rep['changed']) == len(REPLACE)
    comp = compose(s); np.save(CAU32 / 'composite_v32.npy', comp)
    im = Image.fromarray(np.uint8(np.clip(comp, 0, 1) * 255)); im.thumbnail((1800, 1800), Image.Resampling.LANCZOS); im.save(VIS / 'V32_compost_llenc_sencer.png')
    finalize_lr16(s); merged_old = s._record.image_data.get_data(s._record.header)
    data = [np.ascontiguousarray(np.round(np.clip(comp[..., c], 0, 1) * 65535).astype('>u2')).tobytes() for c in range(3)] + list(merged_old[3:])
    merged = ImageData(compression=Compression.RAW); merged.set_data(data, s._record.header); s._record.image_data = merged; s._updated = False
    rep['expected_extra_merged_channels'] = [digest(b) for b in merged_old[3:]]
    assert global_signature(s) == rep['original_global']
    changed = {x['index'] for x in rep['changed']}
    for i, l in enumerate(s):
        if i not in changed:
            assert signature(l) == rep['original_layers'][i], i
    with open(TARGET, 'xb'):
        pass
    log('desant V32.psb (staging)'); s.save(TARGET); rep['target'] = str(TARGET)
    (REB / 'B6_packaging.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False, default=lambda v: v.item() if isinstance(v, np.generic) else v.tolist()) + '\n'); log('staging desat')


def verify():
    rep = json.loads((REB / 'B6_packaging.json').read_text()); s = PSDImage.open(TARGET); ls = list(s)
    assert len(ls) == 40 and s.size == (FW, FH) and s.depth == 16
    assert global_signature(s) == rep['original_global']
    changed = {x['index']: x for x in rep['changed']}
    rows = []
    for i, l in enumerate(ls):
        if i in changed:
            u = np.load(changed[i]['source_u16'], mmap_mode='r'); ok = all(np.array_equal(channel(l, c), u) for c in (0, 1, 2)); assert ok, i
            assert l.name == changed[i]['new_name']
            rows.append({'index': i, 'name': l.name, 'RGB_exact': ok})
        else:
            assert signature(l) == rep['original_layers'][i], i
    comp = np.load(CAU32 / 'composite_v32.npy', mmap_mode='r'); merged = s._record.image_data.get_data(s._record.header)
    errs = []
    for c in range(3):
        before = np.frombuffer(merged[c], '>u2').reshape(FH, FW); after = np.round(np.clip(np.asarray(comp[..., c]), 0, 1) * 65535).astype('uint16')
        errs.append(int(np.max(np.abs(before[::3, ::3].astype('int32') - after[::3, ::3].astype('int32')))))
    assert max(errs) <= 1
    out = {'PASS': True, 'path': str(TARGET), 'sha256': sha(TARGET), 'bytes': TARGET.stat().st_size, 'layers': 40, 'size': [FW, FH], 'depth': 16, 'replaced_layers': rows, 'others_byte_identical': True, 'merged_max_err_DN16': errs}
    (REB / 'B6_psb_verification.json').write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n'); log('verificat: ' + out['sha256'])


def gate():
    v = json.loads((REB / 'B6_psb_verification.json').read_text()); assert v['PASS']
    def jsx(js):
        return subprocess.run(['osascript', '-e', 'tell application id "com.adobe.Photoshop" to do javascript ' + json.dumps(js)], check=True, capture_output=True, text=True).stdout.strip()
    old = jsx('app.displayDialogs.toString();'); assert old in ('DialogModes.ALL', 'DialogModes.ERROR', 'DialogModes.NO'), old
    try:
        res = subprocess.run(['/bin/zsh', str(ROOT / 'research/tools/capes_totals_v14/porta_photoshop.sh'), str(TARGET)], capture_output=True, text=True)
        (REB / 'porta_photoshop.log').write_text(res.stdout); (REB / 'porta_photoshop.stderr.log').write_text(res.stderr)
        assert res.returncode == 0, (res.returncode, res.stderr); assert res.stdout.strip() == 'OBRE 10551 px x 7506 px · 40 capes', res.stdout
    finally:
        jsx('app.displayDialogs = ' + old + '; app.displayDialogs.toString();')
    (REB / 'B6_photoshop_gate.json').write_text(json.dumps({'result': res.stdout.strip(), 'original_dialog_mode': old, 'restored': True, 'file': str(TARGET), 'sha256': v['sha256']}, indent=1) + '\n'); log(res.stdout.strip())


def publish():
    v = json.loads((REB / 'B6_psb_verification.json').read_text()); g = json.loads((REB / 'B6_photoshop_gate.json').read_text())
    assert v['PASS'] and g['result'] == 'OBRE 10551 px x 7506 px · 40 capes' and g['sha256'] == v['sha256']
    assert sha(TARGET) == v['sha256']; assert not FINAL.exists(), 'V32.psb ja existeix a Capes Totals'
    claim = json.loads((ROOT / '.coordination/claim.lock/owner.json').read_text()); assert claim['claim_id'] == 'CLAUDE_V32_ARCS_20260907'
    tmp = CT / 'V32_verificat.tmp.psb'; assert not tmp.exists()
    with open(TARGET, 'rb') as f, open(tmp, 'xb') as g_:
        shutil.copyfileobj(f, g_, 8 << 20)
    assert sha(tmp) == v['sha256']; os.rename(tmp, FINAL)
    assert sha(SRC) == EXPECTED
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (REB / 'B6_publish.json').write_text(json.dumps({'published_utc': now, 'path': str(FINAL), 'sha256': v['sha256'], 'bytes': FINAL.stat().st_size, 'preserved_source': str(SRC), 'preserved_source_sha256': EXPECTED}, indent=1) + '\n')
    log('publicat ' + str(FINAL))


if __name__ == '__main__':
    {'build': build, 'verify': verify, 'gate': gate, 'publish': publish}[sys.argv[1]]()
