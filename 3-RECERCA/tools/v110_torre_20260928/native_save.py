from pathlib import Path
import sys,json,subprocess
ROOT=Path(__file__).resolve().parents[3]
stage,dest,folder=map(lambda x:Path(x).resolve(),sys.argv[1:4]);folder.mkdir(parents=True,exist_ok=True)
assert stage.exists() and not dest.exists()
# A native file can be useful for diagnosis while quality is still FAIL.
# Such files stay in research results, never in the delivery directory.
assert dest.parent == ROOT/'4-RESULTATS/v110_torre_20260928', 'Use the guarded promotion step for 1-PHOTOSHOP'
assert dest.name == 'V110_DIAGNOSTIC.psb', 'Scientific quality is not validated'
template=r'''#target photoshop
var STAGE=new File(__STAGE__),DST=new File(__DEST__),DIR=new Folder(__DIR__);
var prior=(app.documents.length?app.activeDocument:null),dialogs=app.displayDialogs,units=app.preferences.rulerUnits,d=null;
function log(s){var f=new File(DIR.fsName+'/NATIU.log');f.open('a');f.writeln(new Date().toUTCString()+' '+s);f.close();}
function vista(name,w){app.activeDocument=d;var x=d.duplicate('CODEX_V110_'+name,true);
 try{if(w)x.resizeImage(UnitValue(w,'px'),null,null,ResampleMethod.BICUBIC);var t=new TiffSaveOptions();t.layers=false;t.alphaChannels=false;t.embedColorProfile=true;t.imageCompression=TIFFEncoding.NONE;
 var f=new File(DIR.fsName+'/'+name+'.tif');if(f.exists)throw Error('Existeix '+f);x.saveAs(f,t,true,Extension.LOWERCASE);
 }finally{x.close(SaveOptions.DONOTSAVECHANGES);}log('VISTA '+name);}
try{app.displayDialogs=DialogModes.NO;app.preferences.rulerUnits=Units.PIXELS;if(DST.exists)throw Error('No clobber '+DST);
 d=app.open(STAGE);log('OBRE '+d.name+' capes '+d.layers.length);
 // Invalidate the stored merged cache, which belongs to the stage source.
 // All mutations are on this owned stage document, never on Pere's document.
 var original=d,copydoc=d.duplicate('CODEX_V110_NATIVE_COPY',false);d=copydoc;original.close(SaveOptions.DONOTSAVECHANGES);
 var v=d.layers[0].visible;d.layers[0].visible=!v;d.layers[0].visible=v;app.refresh();var hist=d.histogram;
 var sd=new ActionDescriptor(),so=new ActionDescriptor();so.putBoolean(stringIDToTypeID('maximizeCompatibility'),true);
 sd.putObject(charIDToTypeID('As  '),stringIDToTypeID('largeDocumentFormat'),so);sd.putPath(charIDToTypeID('In  '),DST);sd.putBoolean(charIDToTypeID('Cpy '),true);
 executeAction(charIDToTypeID('save'),sd,DialogModes.NO);log('DESAT COM A COPIA');vista('visible_complet',null);vista('llenc_sencer',2400);log('COMPLET');
}catch(e){log('ERROR '+e+' line '+e.line);throw e;}
finally{if(d)d.close(SaveOptions.DONOTSAVECHANGES);if(prior)app.activeDocument=prior;app.displayDialogs=dialogs;app.preferences.rulerUnits=units;}
'V110_NATIU_FET';
'''
js=template.replace('__STAGE__',json.dumps(str(stage))).replace('__DEST__',json.dumps(str(dest))).replace('__DIR__',json.dumps(str(folder)))
f=folder/'desa_natiu.jsx';f.write_text(js)
r=subprocess.run(['zsh',str(ROOT/'3-RECERCA/tools/v108_20260926/cadena/corre_jsx.sh'),str(f)])
sys.exit(r.returncode)
