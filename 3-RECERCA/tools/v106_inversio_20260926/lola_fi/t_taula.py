import json, sys, collections, numpy as np
ds=[0.5,1.0,1.5,2.0,2.5,3.0,4.0,5.0,6.0]
for f in sys.argv[1:]:
    m=json.load(open(f)); t=collections.defaultdict(dict)
    for r in m['files']: t[r['sector']][r['d']]=r['fraccio_lluna']
    print(f, np.round(m['desplacament'],2))
    print('sector   '+' '.join(f'{d:5.1f}' for d in ds))
    for s in ['60-100','100-140','140-180','200-240','240-280','280-320']: print(f'{s:8s} '+' '.join(f'{t[s].get(d,float("nan")):+5.2f}' for d in ds))
