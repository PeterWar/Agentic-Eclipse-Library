"""Read-only reconstruction of the exact current self-calibration state.
Execute the preparation AST only, strip every save/print, and stop before
solver/output calls. Current campaign only; old executable modules not loaded.
"""
from pathlib import Path
import ast,sys
def load_state(arguments):
    path=Path(__file__).with_name('b3_fpn_full.py');tree=ast.parse(path.read_text());body=[]
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name=='solve':break
        body.append(node)
    class ReadOnly(ast.NodeTransformer):
        def visit_Expr(self,node):
            if isinstance(node.value,ast.Call):
                f=node.value.func
                if isinstance(f,ast.Name) and f.id in ['save','print']:return None
                if isinstance(f,ast.Attribute) and isinstance(f.value,ast.Name) and f.value.id=='np' and f.attr.startswith('save'):return None
            return self.generic_visit(node)
    tree=ReadOnly().visit(ast.Module(body=body,type_ignores=[]));ast.fix_missing_locations(tree);old=sys.argv[:]
    ns={'__file__':str(path),'__name__':'frozen_model_state'}
    try:
        sys.argv=[str(path)]+list(arguments);exec(compile(tree,str(path),'exec'),ns)
    finally:sys.argv=old
    return ns
