"""Single grid-scale tension variant, declared before its image/judge evaluation.
Numerical interior continuation only; no exterior smoothing or photometric edit.
"""
from a24_biharmonic_boundary import BiharmonicBoundary,install as base_install,O,save,json

class ScreenedBoundary(BiharmonicBoundary):
 def __init__(self,out):
  super().__init__(out)
  # Unit grid spacing: minimize squared curvature plus squared first derivative.
  # Fixed dimensionless tension=1, not fit to marks, sectors or external images.
  self.A=self.A+self.laplace
  self.outer2 += [(ids,yy,xx,-1.) for ids,yy,xx in self.outer]
  self.M=self.ml.aspreconditioner(cycle='V')
  row=json.loads((out/'BIHARMONIC_SOLVER.json').read_text());row.update(equation='(L^2 + L)u = boundary rhs, L is positive discrete Laplacian',tension=1.,length_px=1.,selection='single grid-scale regularization of interior derivative extrapolation, fixed before candidate evaluation',preconditioner='one symmetric fixed AMG V-cycle for Dirichlet Laplace',clip=False);save(out/'SCREENED_SOLVER.json',row)

 def extend(self,*args,**kwargs):
  ent,receipt=super().extend(*args,**kwargs);receipt['lunar_boundary']='original radial profile plus unclipped screened biharmonic log residual; unit grid-scale tension; two exterior rings fixed';receipt['tension']=1.;return ent,receipt

def install(ns,out):
 engine=base_install(ns,out,engine_class=ScreenedBoundary);row=json.loads((out/'BOUNDARY_METHOD.json').read_text());row.update(method='unclipped grid-scale screened biharmonic log residual on exact lunar photo mask',tension=1.,new_observed_exterior_change=False);save(out/'BOUNDARY_METHOD.json',row);return engine
