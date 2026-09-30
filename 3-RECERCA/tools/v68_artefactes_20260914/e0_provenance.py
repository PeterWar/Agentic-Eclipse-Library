from pathlib import Path
import json,hashlib,sys,platform
R=Path.cwd();O=R/'output/v68_artefactes_20260914';T=R/'research/tools/v68_artefactes_20260914'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
catalog=R/'output/earthshine_max_detail_20260913/A1_native_rgb_all.json'
frames=[q for q in json.loads(catalog.read_text())['frames'] if q['tren']=='vixen' and q['exp']>=.5]
inputs=[catalog,R/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy',R/'output/v58_correccions_20260913/sources/fusion_starless.npy',R/'output/v62_prominencies_20260913/arrays/B1_sony_linear.npy',R/'output/v62_prominencies_20260913/C1_colour_validation.json']+[Path(q['file']) for q in frames]
rep=dict(runtime=sys.version,platform=platform.platform(),inputs=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in inputs],scripts=[dict(path=str(p),sha256=sha(p)) for p in sorted(T.iterdir()) if p.suffix in ['.py','.jsx','.md']],source_V67=json.loads((O/'A1_layers.json').read_text())['sha256'],scope='Reconstruction from declared frozen intermediates, not a clean RAW-to-PSB end-to-end reproduction.',frame_count=len(frames))
(O/'E0_provenance.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2)+'\n');print('PROVENANCE',len(inputs),'inputs',len(rep['scripts']),'scripts',flush=True)
