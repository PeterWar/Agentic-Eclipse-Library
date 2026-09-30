"""Apply the identical physical estimator and gates to cross-green observations.
Input/output substitutions only; the nuisance system and optimizer are unchanged.
"""
from intermediate_common import *
code=(HERE/'b1_physical_cascade.py').read_text().replace('A1_inputs.json','D1_inputs.json').replace('A1_cells_','D1_cells_').replace('B1_','E0_')
exec(compile(code,str(HERE/'b1_physical_cascade.py')+' [cross-green input/output substitution]','exec'))
