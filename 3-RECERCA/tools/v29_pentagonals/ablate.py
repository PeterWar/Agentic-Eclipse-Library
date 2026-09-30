"""Minimal operator/display ablations on unchanged source and coordinates."""
from diagnose import *

def main():
    roi=(slice(2350,5200),slice(3935,6785))
    d=load('gran_raw')[roi];sm=load('gran_smoothed')[roi];final=load('gran_final')[roi]
    panel([.5+.08*d,.5+.5*np.tanh(d/.176680843),.5+sm,final],['Lineal: sense tanh ni H1','Tanh, sense S/N ni H1','Tanh + S/N, sense H1','V29 final'],'ABLA_01_lineal_tanh_h1.png',700)
    # Same source rings, same exact Fourier angular operator, one variable:
    # fixed physical arc scale (V29) versus fixed angle referenced at 2R.
    nr=1250;nt=4096;r=np.linspace(445,1700,nr,dtype=np.float32)[:,None]
    th=np.arange(nt,dtype=np.float32)[None,:]*2*np.pi/nt
    mx=(cx+r*np.cos(th)).astype('float32');my=(cy+r*np.sin(th)).astype('float32')
    source=load('vixen_total')[...,1]
    xp=cv2.remap(np.log(np.maximum(source,1e-8)),mx,my,cv2.INTER_LINEAR)
    f=np.fft.rfft(xp,axis=1);k=np.arange(nt//2+1)[None,:]
    def filt(f,denr):
        gs=[np.exp(-.5*(k*s/denr)**2) for s in [8,32,64,128]]
        return np.fft.irfft(f*(gs[0]-(gs[1]+gs[2]+gs[3])/3),n=nt,axis=1).astype('float32')
    variable=filt(f,r);fixed=filt(f,2*rs)
    yy,xx=np.ogrid[roi[0],roi[1]];rr=np.hypot(xx-cx,yy-cy);theta=np.mod(np.arctan2(yy-cy,xx-cx),2*np.pi)
    def back(a):
        ex=np.concatenate([a[:,-1:],a,a[:,:1]],axis=1)
        return cv2.remap(ex,(theta*nt/(2*np.pi)+1).astype('float32'),((rr-445)*(nr-1)/(1700-445)).astype('float32'),cv2.INTER_LINEAR)
    vv=back(variable);ff=back(fixed)
    panel([.5+.5*np.tanh(vv/.05),.5+.5*np.tanh(ff/.05)],['Vixen: angles varien amb r (V29)','Vixen: angles fixos (ancora 2R), PILOT'],'ABLA_02_escala_angular.png')
    # Analytic input constant in radius: angular morphology must be retained.
    syn=np.log(1.2+.7*np.cos(5*th)+.25*np.cos(10*th+.3)+.15*np.sin(17*th))
    sf=np.fft.rfft(np.broadcast_to(syn,(nr,nt)),axis=1)
    sv=filt(sf,r);ss=filt(sf,2*rs)
    panel([.5+.3*back(np.broadcast_to(syn,(nr,nt))),.5+.5*np.tanh(back(sv)/.05),.5+.5*np.tanh(back(ss)/.05)],['Control: estructura constant en angle','V29: resposta varia amb el radi','Angle fix: control'],'ABLA_03_control_sintetic.png',700)
    (HERE/'ablation_receipt.json').write_text(json.dumps({'synthetic_radii_px':[445,1700],'angular_constant_input':True,'variable_operator_radial_std':float(np.std(sv,axis=0).mean()),'fixed_operator_radial_std':float(np.std(ss,axis=0).mean()),'scope':'diagnostic Vixen polar rings, no product or source edits'},indent=2)+'\n')
    print('Ablations ready')
if __name__=='__main__':main()
