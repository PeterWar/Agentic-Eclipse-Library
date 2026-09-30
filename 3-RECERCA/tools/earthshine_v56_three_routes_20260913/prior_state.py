"""Read-only old calibrated state with this campaign's claim; no old writes."""
from common import *
import ast,sys
def load_state(channel='R'):
 path=ROOT/'research/tools/earthshine_max_detail_20260913/b3_fpn_full.py';tree=ast.parse(path.read_text());body=[]
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
  def visit_Name(self,node):
   if node.id=='OUT':return ast.copy_location(ast.Name(id='OLD',ctx=node.ctx),node)
   return node
 tree=ReadOnly().visit(ast.Module(body=body,type_ignores=[]));ast.fix_missing_locations(tree);st={'__file__':str(path),'__name__':'read_only_prior_state'};argv=sys.argv[:]
 try:
  sys.argv=[str(path),channel,'--all67','--robust','--hetero','--full-error-safe'];exec(compile(tree,str(path),'exec'),st)
 finally:sys.argv=argv
 return st
