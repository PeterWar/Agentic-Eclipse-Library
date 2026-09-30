from pathlib import Path
p=Path('/private/tmp/v105_base_sources_20260926/register_original_bboxseed.py')
s=p.read_text().replace("p0=[6.74177789,-11.90427481,11.60544035,1/1.01946242]", "p0=json.loads((O/'SIFT_seed.json').read_text())['sampling_parameters']")
s=s.replace("[(2,11),(-17,-7),(11,12.2),(.974,.987)]", "[(p0[0]-2,p0[0]+2),(p0[1]-2,p0[1]+2),(p0[2]-.3,p0[2]+.3),(p0[3]-.003,p0[3]+.003)]")
s=s.replace('bboxseed','siftseed');exec(compile(s,str(p),'exec'))
