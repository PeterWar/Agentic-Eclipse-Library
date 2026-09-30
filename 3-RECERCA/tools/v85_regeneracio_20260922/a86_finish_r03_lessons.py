"""Finish a85 after detecting a pre-existing stale global historical reference.

The four scientific edits were already applied. Preserve their backups, sync
this single relevant historical reference to project authority, then execute
only the unexecuted receipt/index/memory tail. Never rerun a85's edits.
"""
from a4_sources import *

def main():
 out=O/'R03_lessons';assert out.exists() and not (O/'SKILL_R03_QA.json').exists()
 rel=Path('corregeix-artefactes/references/limbe_lunar_earthshine.md');newrel=Path('corregeix-artefactes/references/lunar_boundary_and_display.md');targets=[R/'.claude/skills'/rel,Path('/Users/USUARI/.codex/skills')/rel,R/'.claude/skills'/newrel,Path('/Users/USUARI/.codex/skills')/newrel]
 save(out/'PARTIAL_UPDATE_RECOVERY.json',{'failed_assertion':'historical reference canonical/global byte equality after targeted edits','cause':'Global historical reference already lacked canonical V70/V71 section and retained old research/output paths; before and after diff confirmed same pre-existing drift','partial_edits':'all four intended scientific edits applied before assertion; index/memory not yet written','recovery':'sync only this relevant historical consumer reference from canonical project; keep both originals and all prior receipts','not_a_filter_or_PSB_failure':True})
 targets[1].write_bytes(targets[0].read_bytes());changes=[]
 for i,path in enumerate(targets):changes.append({'path':str(path),'before':sha(out/(str(i)+'_'+path.name)),'after':sha(path)})
 source=Path(__file__).with_name('a85_r03_evidence.py').read_text();start=source.index(" assert targets[0].read_bytes()");end=source.index("\nif __name__=='__main__':")
 tail='\n'.join(line[1:] if line.startswith(' ') else line for line in source[start:end].splitlines());ns=dict(globals(),out=out,targets=targets,changes=changes);exec(compile(tail,'a85 unexecuted receipt tail','exec'),ns)

if __name__=='__main__':guard();main()
