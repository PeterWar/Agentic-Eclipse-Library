"""Canonical Photoshop gate on the unique V31 staging document."""
import sys
from pathlib import Path
D=Path(__file__).parent
sys.path.insert(0,str(D.parent/'v30'))
import photoshop_gate as gate
gate.D=D
gate.TARGET=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V31_verificacio.psb')
if __name__=='__main__':gate.main()
