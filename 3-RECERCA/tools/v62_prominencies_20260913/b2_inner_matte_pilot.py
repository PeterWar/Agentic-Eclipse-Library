exec(open('research/tools/v62_prominencies_20260913/a3_masks.py').read().split('rows=[]')[0])
# Isolate the measured black occultor of the interior photograph, not a geometric circle.
# Diagnostic pilots only. R preserves red emission; no source channel is changed.
out=[]
for hi in [.05,.1,.2,.3]:
 t=np.clip((s.max(-1)-.005)/(hi-.005),0,1);t=t*t*(3-2*t);an=soalpha*t
 inner2=s*an[...,None]+cor*(1-an[...,None]);photo=moon*lm[...,None]+inner2*(1-lm[...,None]);out.append((str(hi),photo));np.save(A/f'B2_mask_{hi:g}.npy',sm*t)
bb=(5250,3303,5305,3350);x0,y0,x1,y1=bb;w=x1-x0;h=y1-y0;k=6;pan=Image.new('RGB',(w*k*5,h*k+25))
for j,(nm,img) in enumerate([('V61',native)]+out):
 pan.paste(cv(img[y0-2777:y1-2777,x0-4377:x1-4377]).resize((w*k,h*k),Image.Resampling.NEAREST),(j*w*k,25));ImageDraw.Draw(pan).text((j*w*k+2,5),nm,fill='white')
pan.save(O/'vistes/B2_matte_top.png')
