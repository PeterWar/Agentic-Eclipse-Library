"""Run the same numerical scenes with opposite-green-only optical terms."""
from intermediate_common import *
code=(HERE/'c0_native_lattice_check.py').read_text().replace('C0_','C1_')
code=code.replace('rec_world=g.copy();rec_native=g.copy()','rec_cross=g.copy();parity=(nxy[:,0]%2).reshape(U.shape)')
start=code.index('        for sigma,coef in terms:');end=code.index('        for name,recovered in ',start)
code=code[:start]+'''        for sigma,coef in terms:
            for source_parity in [0,1]:
                mask=(parity==source_parity).astype(float);den=gaussian_filter(mask,sigma/np.sqrt(2),truncate=5,mode='nearest');field=gaussian_filter(matrix*mask,sigma/np.sqrt(2),truncate=5,mode='nearest')/np.maximum(den,1e-30);target=(parity.ravel()!=source_parity);rec_cross[target]+=coef*field.ravel()[target]
'''+code[end:]
code=code.replace("[('world_predictors',rec_world/norm),('native_lattice',rec_native/norm)]","[('cross_green',rec_cross/norm)]")
code=code.replace("['world_predictors','native_lattice']","['cross_green']")
code=code.replace("operators=['Resampled observed predictor Gaussian on world grid','Direct Gaussian on native green lattice with sigma divided bysqrt2; final values stay native']","operators=['Each target green uses opposite-green Gaussian predictors; normalized plane support; native target radiance never interpolated']")
exec(compile(code,str(HERE/'c0_native_lattice_check.py')+' [cross-green numeric variant]','exec'))
