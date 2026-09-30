"""Recompose only after filter generation exits; frozen base and foreground."""
from common import *
from build_canvas import png,over
def main():
    m=np.load(CAU/'fusion_support.npy');al=np.load(CAU/'detail_mask_final.npy');den=warp(m.astype(np.float32),True)
    for name in ('achf','passalt24','gran'):
        a=np.load(CAU/f'{name}_u16.npy').astype(np.float32)/65535-.5
        f=.5+np.where(al>1e-6,warp(a*m,True)/np.maximum(den,1e-6),0);f=np.clip(f,0,1).astype(np.float32)
        np.save(CAU/f'{name}_final.npy',f);png(f,f'V29_{name}_llenc_sencer.png')
    # Same actual editable opacity for every candidate; contrast normalization
    # is a declared layer parameter, never a mask selected by visual appeal.
    b=np.load(CAU/'composite_base.npy');fg=np.load(CAU/'foreground_add.npy',mmap_mode='r')
    for tag,amp in [('natural',.2),('mig',.4),('fort',.65),('maxim',1.)]:
        comp=b.copy()
        for name,op in [('gran',.5),('achf',.7),('passalt24',.4)]:
            f=np.load(CAU/f'{name}_final.npy',mmap_mode='r');d=.5+(f-.5)*amp
            comp=over(comp,d[...,None],al,op,'overlay')
        comp=np.clip(comp+fg,0,1);png(comp,f'PILOT_NRGF_{tag}_llenc_sencer.png')
        if tag=='mig':np.save(CAU/'composite_final.npy',comp)
    log('NRGF full-canvas candidates ready')
if __name__=='__main__':main()
