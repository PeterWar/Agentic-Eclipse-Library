"""Potential source dependence of the previous V31 external-judge test."""
from experiment import ROOT, save
import numpy as np

path=ROOT/'research/tools/v31_purs/cau/weight_vixen.npy'
w=np.load(path,mmap_mode='r')
rows=[]
for x,y in [(5890,2326),(5089,5294),(5965,2120),(5056,5511)]:
    row={'center_xy':[x,y],'methods':{}}
    for name,filter_radius in [('MGN',240),('NAFE',32)]:
        half=128+192+filter_radius
        patch=w[y-half:y+half,x-half:x+half]
        row['methods'][name]={'core_halfwidth':128,'analysis_radius':192,
            'filter_radius':filter_radius,'dependency_halfwidth':half,
            'positive_Vixen_weight_pixels':int(np.count_nonzero(patch>0))}
    rows.append(row)
save('previous_judge_scope',{'source':str(path),'rows':rows,
    'meaning':'potential dependency footprint, not measured contamination amplitude',
    'previous_script':str(ROOT/'research/tools/v31_purs/qa_science.py'),
    'new_study':'all candidate input is Sony-only, fixed original Vixen judge'})
print(rows)
