from pathlib import Path
import json,hashlib,copy
from psb_munta import ROOT,assemble,sha
O=ROOT/'4-RESULTATS/v110_torre_20260928';OLD=ROOT/'4-RESULTATS/v109_pixi_20260928'
source=ROOT/'1-PHOTOSHOP/V108_Artefactes.psb';manual=OLD/'entrades/pixi_capes.psb'
expected={'1-PHOTOSHOP/V108_Artefactes.psb':'e2156820a32d15e7e6816fdaf7111ef8f6e4cc6518491cf9add0041d69d2cc91',
 '1-PHOTOSHOP/V108.psb':'23be3edcf050441788122fe82eb4808009b2b81557862c3cde6054d8bac12ff2',
 '1-PHOTOSHOP/V109.psb':'d471b37677a8ded15522af53bc280e3286a9800c84abc484498f85804cdcdf8f',
 '/Users/USUARI/Downloads/V108-Pixi.tif':'ac93336f7c591bf9c7b2df80f62d62f38b4b9f669077d3390865083aac3e14ca'}
sources={}
for path,h in expected.items():
 p=ROOT/path;actual=sha(p);assert actual==h,('source changed',path)
 sources[path]={'sha256':actual,'size':p.stat().st_size}
(O/'FONTS.json').write_text(json.dumps(sources,indent=2)+'\n')
cfg={'source':str(source),'sha256':expected['1-PHOTOSHOP/V108_Artefactes.psb'],'hide':[307],
 'import':[{'source':str(source),'id':41,'new_id':410,'visible':False,'name':'NRGF original · V108'},
           {'source':str(source),'id':42,'new_id':411,'visible':False,'name':'NRGF interior original · V108'},
           {'source':str(manual),'id':308}]}
for variant in ['control','noCEL']:
 c=copy.deepcopy(cfg);c['destination']=str(O/f'{variant}_stage.psb')
 if variant=='noCEL':
  c['replace']={str(lid):{**{str(cid):str(OLD/'nrgf01'/f'L{lid}_nou.npy') for cid in [0,1,2]},'name':name} for lid,name in [(41,'P01 NRGF · V110'),(42,'P01b NRGF interior · V110')]}
 (O/f'CONFIG_{variant}.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n');assemble(c)
