"""WOW standard with the tested A-profile biharmonic continuation.
Only numerical padding changes; full operator, original display LUT, source and
exact lunar computation domain remain fixed. Selected after known-truth A/B QA.
"""
from a20_analytic_boundary import namespace
from a13_filters import *
from a24_biharmonic_boundary import install

def main():
 out=O/'filters_wow_A';out.mkdir();ns=namespace(out);install(ns,out);a=np.load(O/'domain_v1/sources/base_G.npy');m=np.load(O/'domain_v1/sources/support.npy')&np.isfinite(a)&(a>0);r,t=ns['coords']();ent,fr=ns['farcit_perfil_A'](a,m,r);np.testing.assert_array_equal(ent[m],a[m]);q=ns['wow'](ent,np.ones_like(m),11,False);display=json.loads((O/'filters_biharmonic_E2/products/E2_purs_filters.json').read_text())['P04_WOW']['display'];lo,hi=display;u=np.round(np.clip(np.where(m,(q-lo)/(hi-lo),0),0,1)*65535).astype(np.uint16);np.save(out/'P04_WOW_u16.npy',u);np.save(out/'P04_WOW_float.npy',np.where(m,q,np.nan).astype(np.float32));save(out/'COMPLETE.json',{'PASS':True,'meaning':'numerical construction; acceptance separate','source_sha256':sha(O/'domain_v1/sources/base_G.npy'),'support_sha256':sha(O/'domain_v1/sources/support.npy'),'padding':fr,'display':display,'selection':'A-profile known-truth ablation has lower derivative and transfer error than B-profile biharmonic; no source radiance edited','products':{p.name:sha(p) for p in out.glob('*.npy')}});print('WOW_A_COMPLETE',flush=True)

if __name__=='__main__':guard();main()
