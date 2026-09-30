"""Frozen V30 method, actual V30 and V31 merged pixels, identical fixed references."""
import sys
from pathlib import Path
D=Path(__file__).parent
sys.path.insert(0,str(D.parent/'v30'))
import compare_brno as judge
judge.D=D
judge.SOURCES={'V30_merged':judge.CT/'V30.psb','V31_merged':judge.CT/'V31_verificacio.psb'}
if __name__=='__main__':judge.main()
