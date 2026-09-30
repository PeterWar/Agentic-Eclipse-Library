"""Run the canonical Photoshop gate and restore its previous dialog mode."""
import json,subprocess
from pathlib import Path
D=Path(__file__).parent;ROOT=D.parents[2]
TARGET=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V29_c03_verificacio.psb')

def jsx(s):
    return subprocess.run(['osascript','-e','tell application id "com.adobe.Photoshop" to do javascript '+json.dumps(s)],check=True,capture_output=True,text=True).stdout.strip()
def main():
    assert json.loads((D/'psb_verification.json').read_text())['PASS']
    old=jsx('app.displayDialogs.toString();');assert old in ('DialogModes.ALL','DialogModes.ERROR','DialogModes.NO'),old
    result=None
    try:
        result=subprocess.run(['/bin/zsh',str(ROOT/'research/tools/capes_totals_v14/porta_photoshop.sh'),str(TARGET)],capture_output=True,text=True)
        (D/'porta_photoshop.log').write_text(result.stdout)
        (D/'porta_photoshop.stderr.log').write_text(result.stderr)
        assert result.returncode==0,(result.returncode,result.stderr)
        assert result.stdout.strip()=='OBRE 10551 px x 7506 px · 25 capes',result.stdout
    finally:
        jsx('app.displayDialogs = '+old+'; app.displayDialogs.toString();')
        (D/'photoshop_gate_meta.json').write_text(json.dumps({'original_dialog_mode':old,'restored':True,'staging_document':str(TARGET),'closed_without_saving_by_canonical_gate':bool(result and result.stdout.startswith('OBRE'))},indent=2)+'\n')
    print(result.stdout.strip(),flush=True)
if __name__=='__main__':main()
