"""Native Photoshop document API under current writer; no original document edits."""
from diffraction_common import *
import subprocess
def jsx(js):
    assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
    sc='tell application id "com.adobe.Photoshop"\nwith timeout of 3600 seconds\ndo javascript '+json.dumps(js,ensure_ascii=False)+'\nend timeout\nend tell'
    p=subprocess.run(['osascript','-e',sc],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr.strip())
    return p.stdout.strip()
if __name__=='__main__':
    script='var rows=["ACTIVE|"+(app.documents.length?app.activeDocument.id:0)];for(var i=0;i<app.documents.length;i++){var d=app.documents[i];var p="";try{p=d.fullName.fsName;}catch(e){}rows.push([d.id,d.saved,d.width.as("px"),d.height.as("px"),d.name,p].join("|"));}rows.join("\\n");'
    value=jsx(script);lines=value.splitlines();rows=[]
    for line in lines[1:]:
        i,s,w,h,n,p=line.split('|',5);rows.append(dict(id=int(i),saved=s=='true',width=float(w),height=float(h),name=n,path=p))
    save('R0_open_documents_before.json',dict(active=int(lines[0].split('|')[1]),documents=rows));print(value,flush=True)
