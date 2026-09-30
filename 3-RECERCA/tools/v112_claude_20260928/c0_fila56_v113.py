"""c0_fila56_v113 · crida c0_fila56_v108.py (sense canvis) amb el claim de la V112-V113: comu_v108.claim() exigeix l'identificador del claim viu."""
import sys, runpy
from pathlib import Path
TC = Path(__file__).resolve().parents[1] / 'v108_20260926/cadena'
sys.path.insert(0, str(TC))
import comu_v108
comu_v108.CLAIM_ID = 'CLAUDE_V112_MUNTATGE_20260928'
sys.argv[0] = str(TC / 'c0_fila56_v108.py')
runpy.run_path(sys.argv[0], run_name='__main__')
