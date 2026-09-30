"""Read-only diagnostic hook for the frozen V108 knee. No image correction.

The original function is extracted with AST, never importing its producer.
Instrumentation only observes each reference after its target is calculated.
The four original return values, including legacy D/w bookkeeping, are retained.
"""
import ast
import copy
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

ROOT = Path('/Users/USUARI/Desktop/Eclipse 2026')
G1 = ROOT / '3-RECERCA/tools/v108_20260926/negres_v2/g1_nrgf_genoll.py'
OPS = ROOT / '3-RECERCA/tools/v86_neta_20260923/v86_operadors.py'
G1_SHA = 'd5762d9fe63b238ec82980499a0cb9bf074d8d41514c6923a8a5c7ad86167224'
OPS_SHA = '8c92d1a8d8f730607424214c29ce8975c0d0daa7893ef2a58f2dd58ebdba9d03'


@dataclass(frozen=True)
class Config:
    references: tuple = ('SEC', 'HQ')
    beta: float = 1.0
    epsilon: float = 0.03
    soft_gate_width: float = 0.01
    sec_weight_on_w: bool = True
    hq_without_soft_gate: bool = True
    piecewise_h: bool = True


def _definition(path, expected_hash, name):
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != expected_hash:
        raise RuntimeError(f'Frozen source changed: {path}')
    nodes = [n for n in ast.walk(ast.parse(source))
             if isinstance(n, ast.FunctionDef) and n.name == name]
    if len(nodes) != 1:
        raise RuntimeError(f'Ambiguous definition: {name}')
    return copy.deepcopy(nodes[0])


def literal_knee(config=Config(), observer=None):
    """Build the exact original function, optionally adding one observation hook."""
    smooth = _definition(OPS, OPS_SHA, 'smoothstep')
    h = _definition(G1, G1_SHA, 'h')
    knee = _definition(G1, G1_SHA, 'knee_punt')
    if observer is not None:
        loops = [n for n in knee.body if isinstance(n, ast.For)]
        if len(loops) != 1:
            raise RuntimeError('Unexpected knee reference loop')
        loops[0].body += ast.parse(
            '__observe(k_, S, Fcel, D, w, c_, Dp, T_, Ft)').body
    ns = dict(np=np, BETA=[config.beta], EPS=[config.epsilon],
              GC=[config.soft_gate_width], PESW=[config.sec_weight_on_w],
              HQ0=[config.hq_without_soft_gate], REFNOMS=[config.references],
              TROSSOS=[config.piecewise_h], __observe=observer)
    module = ast.fix_missing_locations(ast.Module(body=[smooth, h, knee],
                                                  type_ignores=[]))
    exec(compile(module, str(G1) + ':read_only_AST', 'exec'), ns)
    return ns['knee_punt']


def classify_model_capacity(Fp, Fo, A1, A2, target, gate, active):
    """Floor inequalities, not target equality or physical/native validation.

    At full gate, s in[0,1] gives F in[Fp,Fo]. With limb gate g, effective
    s is1-g*(1-s), so upper capacity is(1-(1-g)*A1)*(1-(1-g)*A2)*Fo.
    A requested floor below Fp is already met even if equality is impossible.
    """
    cap_after = (1 - (1 - gate) * A1) * (1 - (1 - gate) * A2) * Fo
    return dict(
        current_factor=Fp, capacity_before_gate=Fo, capacity_after_gate=cap_after,
        floor_already_met=active & (target <= Fp),
        floor_feasible_before_gate=active & (target <= Fo),
        floor_feasible_after_gate=active & (target <= cap_after),
        infeasible_before_gate=active & (target > Fo),
        infeasible_after_gate=active & (target > cap_after),
        equality_possible_before_gate=active & (target >= Fp) & (target <= Fo),
        equality_possible_after_gate=active & (target >= Fp) & (target <= cap_after),
        excess_before_gate=np.where(active, np.maximum(target - Fo, 0), 0),
        excess_after_gate=np.where(active, np.maximum(target - cap_after, 0), 0),
    )


def audit_knee(Bs, refs, A1, A2, Fo, *, active_domain, gate, model_scale,
               n=6, config=Config(), knee_function=None):
    """Return (UNCHANGED legacy tuple, diagnostic sidecar).

    active_domain, actual limb gate and a model_scale description must be supplied
    by the caller. Use scalars or bounded stripes, not a full-canvas receipt.
    Validity here supports the Multiply-only factor model, not Overlay or native
    Photoshop output. Strict comparisons are recorded without a tuned tolerance.
    The guard neither raises target values nor changes clipping/parameters.
    """
    names = config.references
    if not isinstance(model_scale, str) or not model_scale.strip():
        raise ValueError('Describe the supplied model scale explicitly')
    if len(refs) != len(names) or not names or len(set(names)) != len(names):
        raise ValueError('Reference names must identify every reference uniquely')
    if any(name not in ('SEC', 'HQ') for name in names):
        raise ValueError('Supported references are SEC and HQ')
    seen = []

    def observe(index, S, Fcel, D, w, capacity, Dp, target, maximum):
        seen.append(dict(name=names[index], S=np.array(S, copy=True),
                         Fcel=np.array(Fcel, copy=True), D=np.array(D, copy=True),
                         w=np.array(w, copy=True), capacity=np.array(capacity, copy=True),
                         Dp=np.array(Dp, copy=True), target=np.array(target, copy=True),
                         maximum=np.array(maximum, copy=True)))

    # Instrumented body is otherwise identical; no output is replaced below.
    observed = literal_knee(config, observe)(Bs, refs, A1, A2, Fo, n)
    legacy = observed if knee_function is None else knee_function(
        Bs, refs, A1, A2, Fo, n)
    if knee_function is not None:
        # Compare this invocation only, not callable identity or all dependencies.
        # Equality includes dtype, shape and every returned bit (including NaNs).
        for actual, expected in zip(legacy, observed, strict=True):
            a, b = np.asarray(actual), np.asarray(expected)
            if a.dtype != b.dtype or a.shape != b.shape or a.tobytes() != b.tobytes():
                raise RuntimeError('Provided knee differs from frozen diagnostic')
    B, a1, a2, fo, domain, gt = np.broadcast_arrays(
        Bs, A1, A2, Fo, np.asarray(active_domain, bool), gate)
    valid = (np.isfinite(B) & (B > 0) & np.isfinite(fo) & (fo >= 0)
             & (fo <= 1) & np.isfinite(a1) & (a1 >= 0) & (a1 <= 1)
             & np.isfinite(a2) & (a2 >= 0) & (a2 <= 1)
             & np.isfinite(gt) & (gt >= 0) & (gt <= 1))
    for row in seen:
        valid &= (np.isfinite(row['S']) & (row['S'] >= 0)
                  & np.isfinite(row['Fcel']) & (row['Fcel'] > 0)
                  & (row['Fcel'] <= 1) & np.isfinite(row['target']))
    target = np.broadcast_to(seen[-1]['maximum'], B.shape)
    active = domain & valid & (gt > 0)
    # All exact ties are explicit. Never select SEC merely because it came first.
    governing = {row['name']: active & (row['target'] == target) for row in seen}
    s = legacy[2]
    after_ideal = (1 - s * a1) * (1 - s * a2) * fo
    gated_s = 1 - gt * (1 - s)
    after_gate = (1 - gated_s * a1) * (1 - gated_s * a2) * fo
    capacity = classify_model_capacity(legacy[3], fo, a1, a2, target, gt, active)
    sidecar = dict(
        references=seen, active=active, invalid_in_domain=domain & ~valid,
        inactive_gate=domain & valid & (gt == 0),
        partial_gate=active & (gt < 1), governing=governing,
        target=target, capacity=capacity,
        achieved_before_limb_gate=after_ideal, achieved_after_limb_gate=after_gate,
        residual_before_limb_gate=np.where(active, target - after_ideal, 0),
        residual_after_limb_gate=np.where(active, target - after_gate, 0),
        floor_unmet_before_limb_gate=active & (after_ideal < target),
        floor_unmet_after_limb_gate=active & (after_gate < target),
        scope='Local Multiply model inequalities only; not a physical-sky or native-render guarantee',
        model_scale=model_scale,
        config=asdict(config), n=n,
        output_tuple_matches_supplied_function=(True if knee_function is not None else None),
        output_comparison_scope="Four return arrays for this invocation: dtype, shape and bytes; not function/dependency identity",
        g1_sha256=G1_SHA, ops_sha256=OPS_SHA,
    )
    return legacy, sidecar


def wrap_knee(knee_function, *, config, model_scale):
    """Diagnostic wrapper; returned numeric tuple comes from knee_function itself."""
    def wrapped(Bs, refs, A1, A2, Fo, n, *, active_domain, gate):
        return audit_knee(Bs, refs, A1, A2, Fo, active_domain=active_domain,
                          gate=gate, model_scale=model_scale, n=n, config=config,
                          knee_function=knee_function)
    return wrapped
