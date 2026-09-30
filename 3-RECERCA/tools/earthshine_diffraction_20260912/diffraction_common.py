from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent;OUT=ROOT/'output/earthshine_diffraction_20260912';NATIVE=ROOT/'output/earthshine_intermediate_witness_20260911';SRC=ROOT/'output/earthshine_native_psf_20260911';CLAIM='CODEX_EARTHSHINE_DIFFRACTION_20260912'
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
CX=699.568111973117;CY=699.6475341408573;SCALE=2.1494813525884373;APERTURE_M=.090;WAVELENGTHS_NM=[500.,550.,600.]
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def airy_otf(f_world,lambda_nm):
    fc=APERTURE_M/(lambda_nm*1e-9)*(SCALE*np.pi/(180*3600));nu=np.minimum(abs(f_world)/fc,1);return (2/np.pi)*(np.arccos(nu)-nu*np.sqrt(np.maximum(1-nu*nu,0)))
