import math
leak=0.03001           # d(eps) per 1e-6 fractional scale error, 2-15 Rsun (verified)
sfix=0.0227            # Design4's own scale-FIXED sigma(eps)
sfree=0.0357           # Design4's own scale-FREE sigma(eps)
sdata=math.sqrt(sfree**2-sfix**2)/leak
print("scale precision the ECLIPSE FRAME ITSELF delivers: %.3f ppm"%sdata)
print("Design4's own quoted break-even: 0.90 ppm  <-- same number")
for scal,tag in [(3.34,"Bruns 2017 calibration fields"),(1.0,"decent calib"),(0.143,"Design1 bracketed in-totality"),(0.05,"ideal")]:
    spost=1/math.sqrt(1/sdata**2+1/scal**2)
    stot=math.sqrt(sfix**2+(leak*spost)**2)
    print(f"  prior {scal:5.3f} ppm -> posterior {spost:5.3f} ppm -> sigma(eps)={stot:.4f}   ({100*(1-stot/sfree):+.0f}% vs free-scale {sfree})")
print()
print("Design4 CLAIM: import -> 0.103, i.e. 2.9x WORSE than 0.036 free.")
print("Correct     : import as prior -> 0.0231 with bracketed fields, i.e. 35% BETTER.")
