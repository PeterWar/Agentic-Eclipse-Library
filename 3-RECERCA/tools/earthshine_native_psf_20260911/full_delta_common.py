from native_common import *
PARENT=OUT
OUT=OUT/'full_sampler_delta'
def save(name,a):(OUT/name).write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
