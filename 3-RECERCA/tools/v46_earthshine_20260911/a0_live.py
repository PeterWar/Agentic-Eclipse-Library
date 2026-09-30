"""Read the user's current V45 merged pixels without changing their document."""
from comu46 import *
from c5_fonts_psb import jsx,CI
import tifffile

def main():
    claim46();p=OUT46/'lliurables/V45_live_before_RGBA.tif';assert not p.exists()
    source=CI/'Earthshine_V45_Fonts.psb';assert sha(source)=='d8bfd4cfc39346b025dd8f071d8b9acd235ae879b62dd576cbf2a25c9199adbc'
    script='var source=new File('+json.dumps(str(source))+').fsName;var d=null;for(var i=0;i<app.documents.length;i++){var p="";try{p=app.documents[i].fullName.fsName;}catch(e){}if(p===source)d=app.documents[i];}if(!d)throw new Error("Expected existing V45 document not open");var before=d.saved;var t=null;try{t=d.duplicate("V46_before_QA",true);var o=new TiffSaveOptions();o.imageCompression=TIFFEncoding.TIFFZIP;o.layers=false;o.alphaChannels=true;o.transparency=true;o.embedColorProfile=true;t.saveAs(new File('+json.dumps(str(p))+'),o,true,Extension.LOWERCASE);}finally{if(t)t.close(SaveOptions.DONOTSAVECHANGES);app.activeDocument=d;} "V45_BEFORE|"+before+"|AFTER|"+d.saved;'
    status=jsx(script)
    with tifffile.TiffFile(p) as tf:
        a=tf.asarray();extras=list(map(int,tf.pages[0].extrasamples))
    assert a.shape==(H,W,4) and a.dtype==np.uint16 and extras==[1]
    roi=a[Y0:Y0+N,X0:X0+N];assert np.all(roi[...,3]==65535)
    old=np.load(CAU45/'expected_fonts_moon_u16.npy');delta=abs(roi[...,:3].astype(int)-old.astype(int));assert delta.max()<=6,'Live source differs: preserve edits before continuing'
    np.save(CAU46/'before_live_rgb_u16.npy',roi[...,:3]);png46('A0_V45_abans_1a1.png',roi[...,:3]/65535)
    savejson(REB46/'A0_source.json',dict(source=str(source),sha256=sha(source),live=str(p),live_sha256=sha(p),original_live_state=status,live_vs_published_max_DN16=int(delta.max()),canvas=[W,H],screenshot='/Users/USUARI/Downloads/Captura de pantalla 2026-09-11 a las 3.12.25.png',screenshot_sha256=sha(Path('/Users/USUARI/Downloads/Captura de pantalla 2026-09-11 a las 3.12.25.png')),request='darken last lunar pixels with gradients; preserve textures and top/right prominences; unattended'))
    print(status,'live vs disk',delta.max(),flush=True)
if __name__=='__main__':main()
