import json, numpy as np, subprocess, csv
d=json.load(open("sweep768.json"))
print("errors:",[x for x in d if "err" in x])
# get exposures from exiftool
import os
D="/Users/USUARI/Desktop/Eclipse 2026/Darks Canon R6III Eclipse/"
out=subprocess.run(["exiftool","-n","-T","-FileName","-ExposureTime","-CameraTemperature","-ShutterMode","-Model","-ISO","-LongExposureNoiseReduction","-Quality",D],capture_output=True,text=True).stdout
meta={}
for line in out.strip().split("\n"):
    p=line.split("\t")
    if len(p)>=4: meta[p[0]]=p[1:]
print("meta n=",len(meta))
for x in d:
    m=meta.get(x["f"],["?","?","?","?","?","?"])
    x["exp"]=m[0]; x["T"]=m[1]; x["sm"]=m[2]; x["model"]=m[3]; x["iso"]=m[4]; x["lenr"]=m[5] if len(m)>5 else "?"
print("distinct ShutterMode:",sorted(set(x["sm"] for x in d)))
print("distinct Model:",sorted(set(x["model"] for x in d)))
print("distinct ISO:",sorted(set(x["iso"] for x in d)))
print("distinct LENR:",sorted(set(x["lenr"] for x in d)))
exps=sorted(set(x["exp"] for x in d), key=float)
print("\n%-14s %4s %9s %9s %8s %8s %8s %8s %9s %9s"%("exp","n","vmean_min","vmean_max","std_min","std_max","secamp_mx","vmax_max","n1000_mx","r05_max"))
for e in exps:
    g=[x for x in d if x["exp"]==e]
    print("%-14s %4d %9.4f %9.4f %8.4f %8.4f %9.4f %8.0f %9d %9.1f"%(e,len(g),
      min(x["vmean"] for x in g),max(x["vmean"] for x in g),
      min(x["vstd"] for x in g),max(x["vstd"] for x in g),
      max(x["secamp"] for x in g),max(x["vmax"] for x in g),
      max(x["n1000"] for x in g),max(x["r05"] for x in g)))
# global outlier hunt on the VISIBLE region, robust z-score per exposure group
print("\n--- outliers in the VISIBLE region (robust z > 5 within its own exposure step) ---")
found=0
for e in exps:
    g=[x for x in d if x["exp"]==e]
    for key in ["vmean","vstd","secamp","vmax","n1000","top40","bot40","left","p999"]:
        v=np.array([float(x[key]) for x in g]); med=np.median(v); mad=np.median(np.abs(v-med))*1.4826
        if mad<=0: continue
        z=(v-med)/mad
        for i,zz in enumerate(z):
            if abs(zz)>5:
                print("  exp=%-12s %-7s %s  val=%.4f med=%.4f z=%.1f T=%s"%(e,key,g[i]["f"],v[i],med,zz,g[i]["T"]))
                found+=1
print("total flagged:",found)
# medians per exposure step
print("\ndistinct vmed values:",sorted(set(x["vmed"] for x in d)))
json.dump(d,open("sweep768_meta.json","w"))
