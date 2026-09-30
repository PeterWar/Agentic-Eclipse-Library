"""Known-physics alias-aware inverse; preserve the same full seeing target.
The prior is white latent power blurred by seeing and the physical pixel. It
only combines aliases; no Moon contour, spectral exponent or halo fit is used.
"""
from diffraction_common import *
def alias_inverse(fu,fv,lam,sigma):
    numerator=np.zeros(np.broadcast_shapes(fu.shape,fv.shape));denominator=numerator.copy()
    for i in range(-3,4):
        for j in range(-3,4):
            u=fu+i;v=fv+j;f=np.sqrt(u*u+v*v)/np.sqrt(2);pixel=np.sinc((u+v)/2)*np.sinc((u-v)/2);power=np.exp(-4*np.pi**2*sigma**2*f*f)*pixel*pixel;A=airy_otf(f,lam);numerator+=power*A;denominator+=power*A*A
    return numerator/np.maximum(denominator,1e-30)
save('A3_alias_plan.json',dict(method=__doc__,nominal_prior_seeing_sigma=.97,sensitivity_prior_sigmas=[.8,1.2],formula='sum(S*A)/sum(S*A^2), S=seeing_OTF^2*pixel_OTF^2, summed aliases[-3,3]^2; latent power assumed white',fit_parameters=[],target='Unchanged full known seeing+pixel image. No regularized target substitution.',gates='Same actual21phase weighted-stack and early/late half gates asA2. Sigma variants test sensitivity; no choosing wavelength or prior by best observed halo.',limits=['White latent-power assumption may be wrong; numerical validation required','Not a unique recovery of arbitrary subpixel scene content','Real seeing and registration still require independent verification']))
code=(HERE/'a2_actual_phase_stack.py').read_text().replace('A2_','A3_')
old="filters={'observed':np.ones_like(H0),'full':1/H0,'regularized_sigma2':1+band0*(1/H0-1)}"
new="filters={'full':1/H0,'alias_nominal':alias_inverse(fu0,fv0,lam,.97),'alias_sigma08':alias_inverse(fu0,fv0,lam,.8),'alias_sigma12':alias_inverse(fu0,fv0,lam,1.2)}"
assert old in code
code=code.replace(old,new).replace("f0=np.hypot(fftfreq(N)[:,None],rfftfreq(N)[None,:])/np.sqrt(2);","fu0=rfftfreq(N)[None,:];fv0=fftfreq(N)[:,None];f0=np.hypot(fv0,fu0)/np.sqrt(2);")
exec(compile(code,str(HERE/'a2_actual_phase_stack.py')+' [alias-aware filters]','exec'))
