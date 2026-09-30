import sys, numpy as np, cv2, tifffile
sys.path.insert(0,"/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
cy = 4638/2.0 - M.RETALL[0]; cx = 6958/2.0 - M.RETALL[2]; R = M.R_SOL_PX
Z=[("corona interior", int(cx-500), int(cy-1.75*R), 1000, 900)]
F=cv2.FONT_HERSHEY_SIMPLEX; t=[]
for n in sys.argv[1:]:
    a=tifffile.imread(M.OUT/n)
    a=a.astype(np.float32)/65535.0 if a.dtype==np.uint16 else a.astype(np.float32)
    for et,x0,y0,w,h in Z:
        c=np.ascontiguousarray((np.clip(a[y0:y0+h,x0:x0+w],0,1)*255).astype(np.uint8)[...,::-1])
        cv2.rectangle(c,(0,0),(w,42),(0,0,0),-1)
        cv2.putText(c,n.replace("corona_vixen_FOTO","").replace(".tif","")or"actual",(12,30),F,0.8,(255,255,255),2)
        t.append(c)
    del a
p="/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad/interior.png"
cv2.imwrite(p,np.concatenate(t,axis=1)); print(p)
