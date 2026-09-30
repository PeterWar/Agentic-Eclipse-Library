"""Repeat the numerical opposite-green check at the final cross-green p4."""
from intermediate_common import *
code=(HERE/'c1_crossgreen_check.py').read_text()
code=code.replace(".replace('C0_','C1_')",".replace('C0_','C2_').replace('B1_physical_cascade.json','E0_physical_cascade.json')")
exec(compile(code,str(HERE/'c1_crossgreen_check.py')+' [final cross-green p4]','exec'))
