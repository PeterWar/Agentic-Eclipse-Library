"""Freeze the two current PSBs, inventory all layers, and extract Pere's marks.

No Photoshop interaction and no source writes. All rasters retain their full canvas.
"""
from pathlib import Path
import hashlib, json, shutil, subprocess, time
import numpy as np
import cv2
from PIL import Image
from psd_tools import PSDImage

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CAU = HERE / 'cau'
OUT = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v29_20260905')
CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8*1024*1024), b''): h.update(b)
    return h.hexdigest()

def channel(layer, cid):
    rec = layer._record
    W, H = layer.size
    if cid == -2:
        md = rec.mask_data
        W, H = md.right-md.left, md.bottom-md.top
    for ci, cd in zip(rec.channel_info, layer._channels):
        if ci.id == cid:
            return np.frombuffer(cd.get_data(W,H,16,layer._psd._record.header.version), '>u2').reshape(H,W).astype(np.uint16)
    return None

def inventory(p):
    s = PSDImage.open(p)
    meta = {'path':str(p),'size':list(s.size),'depth':s.depth,'layers':[]}
    for i,l in enumerate(s):
        md = l._record.mask_data
        meta['layers'].append({'i':i,'name':l.name,'bbox':list(l.bbox),
          'visible':l.visible,'opacity':l.opacity,'blend':str(l.blend_mode),
          'channels':[int(c.id) for c in l._record.channel_info],
          'mask':None if md is None else {'bbox':[md.left,md.top,md.right,md.bottom],
           'background_color':md.background_color,'flags':str(md.flags)}})
    return s,meta

def main():
    CAU.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
    manifest={'created_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'sources':{}}
    mp = CAU/'input_manifest.json'
    prior = json.loads(mp.read_text()) if mp.exists() else None
    for name in ('V28.psb','V28_Artefactes.psb'):
        src=CT/name; dst=CAU/('input_'+name)
        if not dst.exists():
            cp=subprocess.run(['/bin/cp','-c',str(src),str(dst)],capture_output=True,text=True)
            if cp.returncode: shutil.copy2(src,dst)
        h=sha(dst)
        if prior:
            assert h==prior['sources'][name]['sha256'], 'frozen input changed'
        else: assert h==sha(src), 'source changed during snapshot'
        s,meta=inventory(dst)
        manifest['sources'][name]={'original':str(src),'snapshot':str(dst),'bytes':dst.stat().st_size,'sha256':h,'inventory':meta}
        print(name, json.dumps(meta,ensure_ascii=False),flush=True)
        if 'Artefactes' not in name:
            del s; continue
        marks=[]
        for i,l in enumerate(s):
            rgb=np.stack([channel(l,c) for c in (0,1,2)],axis=2)
            # Blue brush over neutral detail; the colour base is inspected visually.
            r,g,b=(rgb[...,c].astype(np.int32) for c in range(3))
            blue=((b-r)>8000)&((b-g)>5000)&(b>18000) if i else np.zeros(rgb.shape[:2],bool)
            n, lab, stats, centres=cv2.connectedComponentsWithStats(blue.astype(np.uint8),8)
            comps=[]
            for k in range(1,n):
                x,y,w,h,area=map(int,stats[k])
                if area<15: continue
                item={'id':f'{i}-{k}','layer_i':i,'layer':l.name,'bbox':[x,y,x+w,y+h],
                      'centre_xy':list(map(float,centres[k])),'blue_pixels':area}
                comps.append(item); marks.append(item)
            np.save(CAU/f'marked_{i}_G16.npy',rgb[...,1])
            np.save(CAU/f'marked_{i}_blue.npy',blue)
            im=Image.fromarray((rgb/257).round().astype(np.uint8))
            im.resize((s.width//4,s.height//4),Image.Resampling.LANCZOS).save(OUT/f'ENTRADA_marques_{i}_llenc_sencer.png')
            print('MARKS',l.name,json.dumps(comps),flush=True)
            del rgb,r,g,b,blue,lab,im
        (CAU/'marques_pere.json').write_text(json.dumps(marks,ensure_ascii=False,indent=2)+'\n')
        del s
    if not prior: mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('DONE',str(mp),flush=True)

if __name__=='__main__': main()
