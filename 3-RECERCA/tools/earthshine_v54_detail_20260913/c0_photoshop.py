"""Own full-canvas Camera Raw documents; preexisting documents preserved."""
from common import *
from psd_tools import PSDImage
import subprocess,sys
sys.path.insert(0,str(ROOT/'research/tools/encaix_sony'))
from psb_utils import finalize_lr16
PRE=SRC/'full_sampler_delta/C0_pre_camera_raw_full.psd'
NAME='V45 font G · dos trens · preferència temporal · vel present'
DST=OUT/'staging/C0_preCR_full.psd';RESULT=OUT/'staging/C1_camera_raw.psd'
def jsx(js):
    claim();sc='tell application id "com.adobe.Photoshop"\nwith timeout of 3600 seconds\ndo javascript '+json.dumps(js,ensure_ascii=False)+'\nend timeout\nend tell'
    p=subprocess.run(['osascript','-e',sc],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr)
    return p.stdout.strip()
def inventory():
    return jsx('var z=[];for(var i=0;i<app.documents.length;i++){var d=app.documents[i],p="";try{p=d.fullName.fsName;}catch(e){}z.push(d.id+"|"+d.name+"|"+p+"|"+d.saved);} "ACTIVE="+(app.documents.length?app.activeDocument.id:"NONE")+";DIALOGS="+app.displayDialogs.toString()+"\\n"+z.join("\\n");')
def prepare():
    claim();assert not DST.exists();s=PSDImage.open(PRE);l=next(l for l in s if l.name==NAME)
    old=np.load(SRC/'full_sampler_delta/C0_pre_camera_raw_rgb.npy');new=np.load(OUT/'arrays/B3_preCR_candidate.npy')
    for info,ch in zip(l._record.channel_info,l._channels):
        if int(info.id) in [0,1,2]:
            c=int(info.id);a=np.frombuffer(ch.get_data(N,N,16,s.version),dtype='>u2').reshape(N,N)
            assert np.array_equal(a,old[...,c]);ch.set_data(np.ascontiguousarray(new[...,c].astype('>u2')).tobytes(),N,N,16,s.version);info.length=len(ch.data)+2
    finalize_lr16(s);s._updated=False
    with DST.open('xb') as f:s.save(f)
    save('C0_prepare.json',dict(input=str(PRE),input_sha=sha(PRE),output=str(DST),output_sha=sha(DST),layer=NAME,canvas=list(s.size),depth=s.depth,change='Only target RGB; old photographic source plus predeclared corroborated band promotion'))
    print('PREPARED',flush=True)
def run():
    assert not RESULT.exists();before=inventory();save('C1_inventory_before.json',dict(inventory=before))
    # Extract exact historical JSX recipe as plain text; no imports/execution
    # of old campaign code or old writes. Substitute only own file paths.
    text=(ROOT/'research/tools/earthshine_native_psf_20260911/d1_camera_raw.py').read_text()
    js=text.split("js='''",1)[1].split("'''",1)[0]
    for key,value in [('__INPUT__',OUT/'receipts/C1_input_descriptor.bin'),('__RETURNED__',OUT/'receipts/C1_returned_descriptor.bin'),('__SRC__',DST),('__STREAM__',ROOT/'output/earthshine_reconstruction_20260911/A1_camera_raw_descriptor.bin'),('__DST__',RESULT),('__NAME__',NAME)]:js=js.replace(key,json.dumps(str(value)))
    # No modal prompts; restore dialogs and active document even on error.
    js='var oldDialogs=app.displayDialogs;app.displayDialogs=DialogModes.NO;try{'+js+'}finally{app.displayDialogs=oldDialogs;} "OWN_REPLAY_DONE";'
    (OUT/'receipts/C1_replay.jsx').write_text(js)
    out=jsx(js);after=inventory();save('C1_replay.json',dict(result=out,before=before,after=after,preserved=before==after,output=str(RESULT),sha256=sha(RESULT)))
    assert before==after;print(out,flush=True)
if __name__=='__main__':dict(prepare=prepare,run=run)[sys.argv[1]]()
