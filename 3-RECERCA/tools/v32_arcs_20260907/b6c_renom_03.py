"""B6c · Correcció de noms a V32.psb: les dues capes 03 (recepta V29 σr0 i V30 σr4) havien
quedat amb el mateix nom «03 ACHF azimutal 8-128 · V32». Es renomenen «… r0 · V32» i
«… r4 · V32»; cap canal ni cap altra capa canvia. Es desa a staging, es verifica i es passa
per la porta; després `publish` substitueix el fitxer publicat (còpia de l'anterior conservada
al rebut per hash)."""
import os, sys, json, copy, subprocess, shutil
from pathlib import Path
os.environ['V29_FINAL_GRID'] = '1'
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'research/tools/v29_c03_fix')); sys.path.insert(0, str(ROOT / 'research/tools/v29')); sys.path.insert(0, str(ROOT / 'research/tools/encaix_sony'))
from common import *
from package_only03 import signature, global_signature, digest
from inspect_inputs import sha, channel
from psb_utils import finalize_lr16
from psd_tools import PSDImage
HERE = Path(__file__).resolve().parent; STAGING = HERE / 'staging'; STAGING.mkdir(exist_ok=True); REB = ROOT / 'output/v32_arcs_20260907/4-rebuts'
FINAL = CT / 'V32.psb'; TMP = STAGING / 'V32_renom.psb'
NEW = {20: '03 ACHF azimutal 8-128 r0 · V32', 21: '03 ACHF azimutal 8-128 r4 · V32'}
def build():
    v = json.loads((REB / 'B6_publish.json').read_text()); assert sha(FINAL) == v['sha256'], 'V32 publicat ha canviat'
    s = PSDImage.open(FINAL); ls = list(s); assert len(ls) == 40
    before = [signature(l) for l in ls]; g = global_signature(s); merged = digest(s._record.image_data.tobytes())
    for i, n in NEW.items():
        assert ls[i].name == '03 ACHF azimutal 8-128 · V32', ls[i].name; ls[i].name = n
    finalize_lr16(s); s._updated = False
    assert global_signature(s) == g
    for i, l in enumerate(s):
        sg = signature(l)
        if i in NEW:
            assert sg['channels'] == before[i]['channels'] and sg['name'] == NEW[i]
        else:
            assert sg == before[i], i
    assert digest(s._record.image_data.tobytes()) == merged
    with open(TMP, 'xb'):
        pass
    s.save(TMP); json.dump({'previous_sha256': v['sha256'], 'previous_bytes': v['bytes'], 'renamed': NEW, 'staging': str(TMP)}, open(REB / 'B6c_renom.json', 'w'), indent=1, ensure_ascii=False); log('desat ' + str(TMP))
def verify():
    r = json.loads((REB / 'B6c_renom.json').read_text()); a = PSDImage.open(FINAL); b = PSDImage.open(TMP)
    assert global_signature(a) == global_signature(b) and digest(a._record.image_data.tobytes()) == digest(b._record.image_data.tobytes())
    for i, (la, lb) in enumerate(zip(a, b)):
        sa, sb = signature(la), signature(lb)
        if i in {int(k) for k in r['renamed']}:
            assert sa['channels'] == sb['channels'] and lb.name == r['renamed'][str(i)]
        else:
            assert sa == sb, i
    r.update({'staging_sha256': sha(TMP), 'staging_bytes': TMP.stat().st_size, 'PASS': True}); json.dump(r, open(REB / 'B6c_renom.json', 'w'), indent=1, ensure_ascii=False); log('verificat ' + r['staging_sha256'])
def gate():
    r = json.loads((REB / 'B6c_renom.json').read_text()); assert r['PASS']
    def jsx(js):
        return subprocess.run(['osascript', '-e', 'tell application id "com.adobe.Photoshop" to do javascript ' + json.dumps(js)], check=True, capture_output=True, text=True).stdout.strip()
    old = jsx('app.displayDialogs.toString();')
    try:
        res = subprocess.run(['/bin/zsh', str(ROOT / 'research/tools/capes_totals_v14/porta_photoshop.sh'), str(TMP)], capture_output=True, text=True)
        assert res.returncode == 0 and res.stdout.strip() == 'OBRE 10551 px x 7506 px · 40 capes', res.stdout + res.stderr
    finally:
        jsx('app.displayDialogs = ' + old + '; app.displayDialogs.toString();')
    r['gate'] = res.stdout.strip(); json.dump(r, open(REB / 'B6c_renom.json', 'w'), indent=1, ensure_ascii=False); log(r['gate'])
def publish():
    r = json.loads((REB / 'B6c_renom.json').read_text()); assert r['PASS'] and r['gate'].startswith('OBRE') and sha(TMP) == r['staging_sha256'] and sha(FINAL) == r['previous_sha256']
    os.replace(TMP, FINAL); assert sha(FINAL) == r['staging_sha256']
    r['published'] = True; json.dump(r, open(REB / 'B6c_renom.json', 'w'), indent=1, ensure_ascii=False); log('V32.psb substituït amb els noms corregits')
if __name__ == '__main__':
    {'build': build, 'verify': verify, 'gate': gate, 'publish': publish}[sys.argv[1]]()
