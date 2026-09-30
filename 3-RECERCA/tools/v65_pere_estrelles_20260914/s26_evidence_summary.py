from pathlib import Path
import numpy as np,json,pandas as pd,hashlib
R=Path.cwd();O=R/'output/v65_pere_estrelles_20260914';d=json.loads((O/'S22_final_catalog.json').read_text());joint=json.loads((O/'S15_joint_catalog.json').read_text());extra=json.loads((O/'S17_extra_detection.json').read_text());keys={(r['kind'],r['TYC']) for r in joint['rows']}|{(r['kind'],r['TYC']) for r in extra['rows']};d['detection_audit']=dict(unique_catalogue_positions_tested=sum(k[0]=='catalog' for k in keys),unique_reflected_control_positions_tested=sum(k[0]=='rotated_null' for k in keys),accepted_reflected_controls=0,completeness_proven=False);d['photometry_limits']=['Formal errors describe the fitted native model and aperture calibration. They do not bound all PSF, extinction or inter-instrument systematics.','Deliberately mismatched trailed-PSF injections show up to33.8% conditional flux bias; no universal10% natural-source photometric accuracy is claimed.','Reserved inter-instrument flux ratios differ by up to22% from the training median.','Colour has atmospheric and model uncertainty; native CFA values, spectral regularization and matrices are retained.','Fainter catalogue positions without repeated RAW signal have not been drawn.']
for r in d['stars']:r['formal_flux_error_excludes_model_systematics']=True
# Standards-compliant machine-readable catalogue; unavailable quantities are null.
def clean(v):
 if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
 if isinstance(v,list):return [clean(x) for x in v]
 if isinstance(v,float) and not np.isfinite(v):return None
 return v
d=clean(d);(O/'S22_final_catalog.json').write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False));csv=[]
for r in d['stars']:
 q={k:v for k,v in r.items() if k not in ['native_photometry','detection_support']};q.update(r['detection_support']);q['identifications']=';'.join(r['identifications']);csv.append(q)
pd.DataFrame(csv).to_csv(O/'V65_estrelles.csv',index=False)
# Sources are read-only; verify the frozen extraction identity metadata and physical calibration hashes.
raw=[]
for n in ['S9_native_manifest','S11_vixen_manifest']:
 m=json.loads((O/(n+'.json')).read_text());flat=Path(m['flat']);assert hashlib.file_digest(flat.open('rb'),'sha256').hexdigest()==m['flat_sha']
 for f in m['frames']:
  p=Path(f['path']);assert p.stat().st_size==f['bytes'] and p.stat().st_mtime_ns==f['mtime_ns'];raw.append(dict(path=str(p),bytes=f['bytes'],mtime_ns=f['mtime_ns'],sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),exposure=f['exposure']))
rep=dict(selected_RAW=raw,raw_count=len(raw),raw_metadata_exact=True,flat_hashes_exact=True,raw_total_exposure_seconds=sum(r['exposure'] for r in raw),native_detection=d['detection_audit'],source_layers_geometry_changed=False,Gaussian_output_sigma=1.5,stellar_surface_resolution_claimed=False,photon_metrics_remain_separate_from_display_transfer=True);(O/'S26_evidence_summary.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2));print(rep['native_detection'],len(raw),flush=True)
