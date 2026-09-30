import numpy as np
L=1.7516
# Bruns 2017 Table 5a: pixel x,y and distance in Rsun. Reconstruct radial geometry from distance only,
# using the actual pixel positions to get the position angle around the Sun.
px=np.array([[120.905,330.576],[425.492,1120.897],[788.888,646.437],[527.111,17.981],[3051.848,78.155],
[841.929,213.205],[2815.052,510.911],[602.019,746.530],[651.884,313.647],[2014.265,112.192],
[828.821,299.299],[2553.122,351.481],[2709.304,2037.461],[2824.313,1452.939],[1610.946,245.588],
[3063.587,2332.805],[1077.274,793.764],[1374.400,153.860],[2102.271,1241.101],[1178.726,2313.957]])
dist=np.array([4.566,3.000,3.058,4.522,4.817,3.802,3.760,3.168,3.828,3.694,3.649,3.676,2.446,2.694,
3.306,3.395,2.433,3.555,1.513,1.603])
scale=2.087  # arcsec/px
Rsun_as=945.0
# find Sun centre in pixels by least squares on |p-c| = dist*Rsun/scale
from scipy.optimize import least_squares
res=least_squares(lambda c: np.hypot(px[:,0]-c[0],px[:,1]-c[1])-dist*Rsun_as/scale,[1650,1250])
c=res.x
x=(px[:,0]-c[0])*scale/Rsun_as; y=(px[:,1]-c[1])*scale/Rsun_as
r=np.hypot(x,y)
print("recovered Sun centre px:",c.round(1),"  r range:",r.min().round(2),r.max().round(2))
def sig_eps(x,y,sig,mode="free"):
    n=len(x); rr=np.hypot(x,y); dxi=L*(x/rr)/rr; deta=L*(y/rr)/rr
    if mode=="free": base=[(np.ones(n),0),(x,0),(y,0),(np.ones(n),1),(x,1),(y,1)]
    else:            base=[(np.ones(n),0),(np.ones(n),1),(y,0),(-x,1)]
    A=np.zeros((2*n,1+len(base))); A[:n,0]=dxi; A[n:,0]=deta
    for j,(v,ax) in enumerate(base):
        if ax==0: A[:n,1+j]=v
        else: A[n:,1+j]=v
    return sig*np.sqrt(np.linalg.pinv(A.T@A)[0,0])
for s,lab in [(0.065,"MaxIm 0.065\""),(0.086,"Astrometrica 0.086\""),(0.075,"mean 0.075\"")]:
    print(f"  {lab}: plate scale EXTERNAL -> sigma(eps)={sig_eps(x,y,s,'fixed'):.4f}"
          f"   ({sig_eps(x,y,s,'fixed')*100:.1f}%)   |  plate scale FREE -> {sig_eps(x,y,s,'free')*100:.1f}%")
print("  Bruns reported: 3.1% (star fit) + 1.23% (plate scale) = 3.4% total;  eclipse-only method ~4-8%")
