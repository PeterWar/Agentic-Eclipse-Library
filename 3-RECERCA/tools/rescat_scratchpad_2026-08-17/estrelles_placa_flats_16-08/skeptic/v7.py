import rawpy, numpy as np, os
V="/Users/USUARI/Desktop/Eclipse 2026/Vixen Unfiltered/"
# lights: which are 0.5 s?
import subprocess
o=subprocess.run(["exiftool","-n","-T","-FileName","-ExposureTime","-CameraTemperature",V],capture_output=True,text=True).stdout
L=[l.split("\t") for l in o.strip().split("\n") if l.count("\t")>=2]
half=[x for x in L if x[1]=="0.5"]; one=[x for x in L if x[1] in ("1","2","10")]
print("0.5s lights:",[(x[0],x[2]) for x in half])
for x in half+one:
    with rawpy.imread(V+x[0]) as r:
        f=r.raw_image.astype(np.float64); rp=f.mean(axis=1)
    print("%s exp=%-5s T=%s  rows0-7 %s  r05mean %.1f"%(x[0],x[1],x[2],np.round(rp[:8],1),rp[:6].mean()))
