"""Promotion gate: good file/method cannot override failed science or provenance."""
from pathlib import Path
import json, hashlib, sys

ROOT = Path(__file__).resolve().parents[3]
O = ROOT/'4-RESULTATS/v110_torre_20260928'


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    failures = []
    q = json.loads((O/'QA_CIENTIFICA.json').read_text())
    if q['scientific_status'] != 'PASS':
        failures.append('scientific_status is not PASS')
    if q['threshold_absolute_and_relative'] != [0.90, 1.10]:
        failures.append('predeclared scientific threshold changed')
    for key in ('absolute_slope_range', 'relative_log_sky_slope_range', 'relative_log_corona_slope_range'):
        low, high = q['Fourier_2to128_fixed8tiles'][key]
        if not (0.90 <= low <= high <= 1.10):
            failures.append(key+' outside [0.90,1.10]')
    if q['manual_status'] != 'RESOLVED':
        failures.append('flattened manual base remains unresolved')
    method_path = O/'PORTA_FINAL.json'
    method = json.loads(method_path.read_text()) if method_path.exists() else {}
    if method.get('status') != 'METHOD_AND_NATIVE_PASS':
        failures.append('final method/native gate is not PASS')
    else:
        current = sha(method['file'])
        if current != method['sha256']:
            failures.append('delivered PSB changed after method gate')
        if method['gate_sha256'] != sha(ROOT/'3-RECERCA/tools/guardrails_postprocessat/porta_torre_pisa.py'):
            failures.append('method receipt is from an older gate')
        if q.get('delivered_sha256') != current:
            failures.append('QA does not bind current PSB')
        if q.get('contract_sha256') != method['contract_sha256'] or method['contract_sha256'] != sha(O/'CONTRACTE_TORRE.json'):
            failures.append('QA/method contract binding mismatch')
        evidence=json.loads((O/'EVIDENCIA_NATIVA.json').read_text())
        for key in ('control_render','candidate_render','final_render'):
            spec=evidence['files'][key]
            if q.get('native_render_hashes',{}).get(key) != spec['sha256'] or sha(spec['path']) != spec['sha256']:
                failures.append('QA native pixels mismatch: '+key)
        ip=O/'INTEGRITAT.json'
        integrity=json.loads(ip.read_text()) if ip.exists() else {}
        if integrity.get('sha256') != current or integrity.get('status') != 'PASS':
            failures.append('integrity receipt is missing or belongs to another PSB')
        for name in ('p6.log','porta_photoshop.log'):
            lp=O/name
            if not lp.exists() or integrity.get('logs',{}).get(name) != sha(lp):
                failures.append('integrity log binding mismatch: '+name)
    negative = json.loads((O/'PORTA_NEGATIVA_V109.json').read_text())
    if negative.get('status') != 'FAIL':
        failures.append('known bad V109 is not rejected')
    for name, literal in [('p6.log', 'PASSA'), ('porta_photoshop.log', 'OBRE')]:
        p = O/name
        if not p.exists() or literal not in p.read_text():
            failures.append('missing '+name+' success')
    report = dict(status='BLOCKED' if failures else 'ELIGIBLE_FOR_REVIEW',
                  failures=failures, quality=q['scientific_status'],
                  method=method.get('status'), no_files_promoted=True)
    (O/'PORTA_LLIURAMENT.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    return 2 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
