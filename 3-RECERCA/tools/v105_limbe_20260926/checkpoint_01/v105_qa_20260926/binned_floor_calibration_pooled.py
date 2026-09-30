"""Exact same cell experiment for summed eight 1/3200 observations.
The source script is transformed in memory; no source or RAW is modified.
"""
from pathlib import Path
path=Path('/private/tmp/v105_qa_20260926/binned_floor_calibration.py')
code=path.read_text()
replacements={
    'for j,f in enumerate(frames):':"for j,f in [(-1, dict(name='POOLED_2959_2966', exposure=8/3200))]:",
    'dr=dreal(j);physical=dr>=10':"dr=np.minimum.reduce([dreal(k) for k in range(8)]);physical=dr>=10",
    "n=np.asarray(data[mode]['numerator'][j,iy,ix],float);w=np.asarray(data[mode]['weight'][j,iy,ix],float)":
    "n=sum(np.asarray(data[mode]['numerator'][k,iy,ix],float) for k in range(8));w=sum(np.asarray(data[mode]['weight'][k,iy,ix],float) for k in range(8))",
    "'binned_floor_calibration.json'":"'binned_floor_calibration_pooled.json'",
    "'no_floor_tile16_coefficients_candidates.json'":"'no_floor_tile16_pooled_coefficients_candidates.json'"
}
for old,new in replacements.items():
    assert code.count(old)==1,(old,code.count(old))
    code=code.replace(old,new)
exec(compile(code,str(path),'exec'),{'__name__':'__main__','__file__':str(path)})
