"""Existing project native Photoshop document API, without screen/key automation."""
import subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'output/earthshine_detail_20260911'
def claim():
    assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_DETAIL_20260911'
def jsx(js):
    claim()
    sc='tell application id "com.adobe.Photoshop"\nwith timeout of 3600 seconds\ndo javascript '+json.dumps(js,ensure_ascii=False)+'\nend timeout\nend tell'
    p=subprocess.run(['osascript','-e',sc],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr.strip())
    return p.stdout.strip()
