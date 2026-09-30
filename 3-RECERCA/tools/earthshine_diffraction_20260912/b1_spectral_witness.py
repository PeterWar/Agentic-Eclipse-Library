"""Run the predeclared spectral endpoints without choosing the best halo fit."""
from diffraction_common import *
original=(HERE/'b0_native_profile_witness.py').read_text();rows=[]
for wavelength in [500,600]:
    code=original.replace('B0_',f'B1_{wavelength}_').replace('airy550',f'airy{wavelength}').replace('Nominal550nm fixed',f'Sensitivity{wavelength}nm fixed').replace('airy_otf(abs(freq),550.)',f'airy_otf(abs(freq),{wavelength}.)')
    exec(compile(code,str(HERE/'b0_native_profile_witness.py')+f' [spectral {wavelength}]','exec'),dict(__builtins__=__builtins__))
    p=json.loads((OUT/f'B1_{wavelength}_profile_witness.json').read_text())
    rows.append(dict(wavelength_nm=wavelength,comparisons=p['comparisons'],sector_nonworse=sum(r['no_worse'] for r in p['sectors']),sector_total=len(p['sectors']),PASS=p['PASS']))
    save('B1_spectral_witness.json',dict(method=__doc__,endpoints=rows,no_best_wavelength_selection=True))
print('SPECTRAL DONE',flush=True)
