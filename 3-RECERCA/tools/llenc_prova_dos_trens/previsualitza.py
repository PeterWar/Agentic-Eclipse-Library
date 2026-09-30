import os, json, math, numpy as np, cv2, tifffile
OUT=os.path.expanduser("~/Downloads/Eclipse 2026/output/llenc_prova_dos_trens_20260823")
PREV=os.path.expanduser("~/Desktop/Eclipse 2026/IA/output/llenc_prova_dos_trens_20260823")
os.makedirs(PREV,exist_ok=True)
m=json.load(open(os.path.join(OUT,"MANIFEST.json")))
W,H=m["llenc"]; ESC=m["escala_arcsec_px"]; RS=m["rsol_arcsec_del_dia"]
PC={d["fitxer"]:d for d in m["corba"]["per_capa"]}; K=300.0
S=4.2
w2,h2=int(W/S),int(H/S)
acc=np.zeros((h2,w2,3),np.float32); wsum=np.zeros((h2,w2),np.float32)
COL={"572A2982":(90,220,255),"572A2983":(90,220,255),"572A2984":(90,220,255),
     "DSC06993":(120,255,120),"DSC06987":(255,150,80)}
outl=[]
for c in m["capes"]:
    f=os.path.join(OUT,f"{c['fitxer']}_llencComu_BBsol_float32.tif")
    a=tifffile.imread(f).astype(np.float32)
    x0,y0,x1,y1=c["bbox"]
    d=PC[c["fitxer"]]
    for i in range(3): a[:,:,i]-=np.float32(d["cel_BBsol_RGB"][i])
    a[:,:,0]/=np.float32(d["neutralitzacio_RG"]); a[:,:,2]/=np.float32(d["neutralitzacio_BG"])
    u=np.clip(a/max(d["blanc_BBsol"],1e-30),0,1)
    g=np.log1p(u*K)/math.log1p(K)
    al=(a.sum(2)>0).astype(np.float32)
    gs=cv2.resize(g,(int((x1-x0)/S),int((y1-y0)/S)),interpolation=cv2.INTER_AREA)
    as_=cv2.resize(al,(int((x1-x0)/S),int((y1-y0)/S)),interpolation=cv2.INTER_AREA)
    X0,Y0=int(x0/S),int(y0/S); Xe,Ye=min(w2,X0+gs.shape[1]),min(h2,Y0+gs.shape[0])
    acc[Y0:Ye,X0:Xe]+=gs[:Ye-Y0,:Xe-X0]*as_[:Ye-Y0,:Xe-X0,None]
    wsum[Y0:Ye,X0:Xe]+=as_[:Ye-Y0,:Xe-X0]
    outl.append((c["fitxer"],(X0,Y0,Xe,Ye),COL[c["fitxer"]],c["tren"]))
    del a,g,gs,as_
img=np.clip(acc/np.maximum(wsum,1e-6)[:,:,None],0,1)
bgr=(img[:,:,::-1]*255).astype(np.uint8)
cx,cy=int(m["sol"][0]/S),int(m["sol"][1]/S)
for R in (1,3,6,10,15,20):
    cv2.circle(bgr,(cx,cy),int(R*RS/ESC/S),(70,70,70),1,cv2.LINE_AA)
for nom,(X0,Y0,Xe,Ye),col,tren in outl:
    cv2.rectangle(bgr,(X0,Y0),(Xe-1,Ye-1),col,2 if tren=="sony" else 1,cv2.LINE_AA)
    cv2.putText(bgr,nom,(X0+10,Y0+26),cv2.FONT_HERSHEY_SIMPLEX,0.55,col,2,cv2.LINE_AA)
cv2.arrowedLine(bgr,(90,220),(90,90),(255,255,255),2,cv2.LINE_AA,tipLength=.25)
cv2.putText(bgr,"N",(80,80),cv2.FONT_HERSHEY_SIMPLEX,0.7,(255,255,255),2,cv2.LINE_AA)
for i,t in enumerate([f"Llenc comu {W} x {H} px, nord amunt, Sol al centre, {ESC} \"/px",
                      f"= {W*ESC/RS:.2f} x {H*ESC/RS:.2f} R(sol) del dia (R = {RS:.1f}\")",
                      "VERD = Sony 8 s apuntament nominal   TARONJA = Sony 8 s apuntament desplacat",
                      "CIAN = els tres 10,3 s de la Vixen"]):
    cv2.putText(bgr,t,(20,h2-90+22*i),cv2.FONT_HERSHEY_SIMPLEX,0.5,(230,230,230),1,cv2.LINE_AA)
p=os.path.join(PREV,"00_PREVIEW_llenc_prova.jpg")
cv2.imwrite(p,bgr,[int(cv2.IMWRITE_JPEG_QUALITY),92])
print(p,bgr.shape)
