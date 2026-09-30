from common import *
import subprocess
TARGET=D/'staging/V31.psb'
def jsx(s):return subprocess.run(['osascript','-e','tell application id "com.adobe.Photoshop" to do javascript '+json.dumps(s)],check=True,capture_output=True,text=True).stdout.strip()
def main():
 assert json.loads((D/'receipts/psb_verification.json').read_text())['PASS']
 inventory=jsx('var z=[]; for(var i=0;i<app.documents.length;i++){var d=app.documents[i],p="";try{p=d.fullName.fsName;}catch(e){} z.push(d.name+"\\t"+p+"\\t"+d.saved);} z.join("\\n");')
 (D/'receipts/photoshop_documents_before.txt').write_text(inventory+'\n')
 old=jsx('app.displayDialogs.toString();');assert old in ['DialogModes.ALL','DialogModes.ERROR','DialogModes.NO']
 result=None
 try:
  result=subprocess.run(['/bin/zsh',str(ROOT/'research/tools/capes_totals_v14/porta_photoshop.sh'),str(TARGET)],capture_output=True,text=True)
  (D/'receipts/porta_photoshop.log').write_text(result.stdout);(D/'receipts/porta_photoshop.stderr.log').write_text(result.stderr)
  assert result.returncode==0 and result.stdout.strip()=='OBRE 10551 px x 7506 px · 40 capes',(result.returncode,result.stdout,result.stderr)
 finally:
  restored=jsx('app.displayDialogs = '+old+'; app.displayDialogs.toString();')
  savejson(D/'receipts/photoshop_gate.json',{'original_dialog_mode':old,'restored':restored==old,'target':str(TARGET),'closed_without_saving':bool(result and result.stdout.startswith('OBRE')),'result':result.stdout.strip() if result else None})
 print(result.stdout.strip(),flush=True)
if __name__=='__main__':main()
