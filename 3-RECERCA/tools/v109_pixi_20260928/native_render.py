"""Render an owned PSB in Photoshop, preserving the user's document and settings."""
from pathlib import Path
import sys,json,subprocess
ROOT=Path(__file__).resolve().parents[3]
src,out=map(lambda s:Path(s).resolve(),sys.argv[1:3]);out.mkdir(exist_ok=True,parents=True)
assert src.exists() and not (out/'visible_complet.tif').exists()
template=r'''#target photoshop
var SRC=new File(__SRC__),DIR=new Folder(__DIR__),HIDE=__HIDE__;
var prior=app.documents.length?app.activeDocument:null,dialogs=app.displayDialogs,units=app.preferences.rulerUnits,d=null;
function log(s){var f=new File(DIR.fsName+'/RENDER.log');f.open('a');f.writeln(new Date().toUTCString()+' '+s);f.close();}
function vista(name,w){app.activeDocument=d;var x=d.duplicate('CODEX_V109_'+name,true);
try{if(w)x.resizeImage(UnitValue(w,'px'),null,null,ResampleMethod.BICUBIC);var t=new TiffSaveOptions();t.layers=false;t.alphaChannels=false;t.embedColorProfile=true;t.imageCompression=TIFFEncoding.NONE;
var f=new File(DIR.fsName+'/'+name+'.tif');if(f.exists)throw Error('Existeix '+f);x.saveAs(f,t,true,Extension.LOWERCASE);
}finally{x.close(SaveOptions.DONOTSAVECHANGES);}log('VISTA '+name);}
try{app.displayDialogs=DialogModes.NO;app.preferences.rulerUnits=Units.PIXELS;
d=app.open(SRC);for(var k=0;k<HIDE.length;k++){var found=0;for(var i=0;i<d.layers.length;i++)if(d.layers[i].id==HIDE[k]){d.layers[i].visible=false;found++;}if(found!=1)throw Error('No layer '+HIDE[k]);}var v=d.layers[0].visible;d.layers[0].visible=!v;d.layers[0].visible=v;app.refresh();var hist=d.histogram;
log('OBRE '+d.name+' capes '+d.layers.length);vista('visible_complet',null);vista('llenc_sencer',2400);log('COMPLET');
}catch(e){log('ERROR '+e+' line '+e.line);throw e;}
finally{if(d)d.close(SaveOptions.DONOTSAVECHANGES);if(prior)app.activeDocument=prior;app.displayDialogs=dialogs;app.preferences.rulerUnits=units;}
'V109_RENDER_FET';
'''
js=template.replace('__SRC__',json.dumps(str(src))).replace('__DIR__',json.dumps(str(out))).replace('__HIDE__',json.dumps([int(x) for x in sys.argv[3:]]))
f=out/'render.jsx';f.write_text(js)
sys.exit(subprocess.run(['zsh',str(ROOT/'3-RECERCA/tools/v108_20260926/cadena/corre_jsx.sh'),str(f)]).returncode)
