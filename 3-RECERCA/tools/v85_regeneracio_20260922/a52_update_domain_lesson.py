from a4_sources import *
from datetime import datetime,timezone

def main():
 lock=R/'.coordination/claim.lock/owner.json';claim=json.loads(lock.read_text());assert claim['claim_id']==CID
 for scope in ['.claude/skills/corregeix-artefactes/references/lunar_boundary_and_display.md','.codex/skills/corregeix-artefactes/references/lunar_boundary_and_display.md','IA/Skills/README.md','explicitly authorized memory correction note']:
  if scope not in claim['scope']:claim['scope'].append(scope)
 save(lock,claim);out=O/'R02_lessons';out.mkdir();rel=Path('corregeix-artefactes/references/lunar_boundary_and_display.md');p=R/'.claude/skills'/rel;globalp=Path('/Users/USUARI/.codex/skills')/rel;s=p.read_text();before=[]
 for name,q in [('project',p),('codex',globalp)]:
  dst=out/(name+'_lunar_boundary_before.md');dst.write_bytes(q.read_bytes());before.append({'scope':name,'sha256':sha(dst)})
 old='''2. **Domini de càlcul del filtre de presentació:** ha d'excloure tota la
   foto lunar que finalment cobreix el compost, abans de perfils, farciment
   i convolució. Una màscara aplicada només a la sortida no evita que el
   filtre utilitzi píxels ocults sota aquesta lluna. Conservar separats els
   suports físics originals. Repetir l'exclusió en tots els suports
   auxiliars: un OR posterior amb S4 pot readmetre el disc.'''
 new='''2. **Domini de càlcul del filtre:** definir-lo a partir de la validesa de
   la font i del senyal que es vol filtrar. No confondre la fotografia lunar
   de presentació amb el suport físic temporal. En la V85, excloure aquesta
   fotografia abans de filtrar també retirava 36.581 píxels acceptats pel
   productor físic. Això era una variant experimental, no una correcció
   causal demostrada. Tampoc conservar tot suport històric prova que sigui
   corona neta: cal distingir mesures coronalment vàlides, llum fotosfèrica,
   protuberàncies i mostres afectades pel limbe. Diagnosticar-ho abans de
   decidir el domini; aplicar coherentment la decisió a tots els suports
   auxiliars, perquè un OR amb S4 pot readmetre dades excloses.'''
 assert old in s;s=s.replace(old,new).replace('3. **Validesa de la sortida del filtre:** registrar també pèrdues per','3. **Validesa de la sortida del filtre:** excloure tota la Lluna segons la\n   màscara de presentació autoritzada. Registrar també pèrdues per')
 s+='''
## Rectificació del domini i límits de R02

La prescripció inicial d’excloure sempre tota la foto lunar de l’entrada era
massa forta: R02 la rectifica explícitament. Eliminar-la del resultat del
filtre i evitar una entrada contaminada són dues obligacions diferents.
La variant que reté tot suport físic tampoc no s’ha acceptat automàticament:
el biharmònic sense tensió produeix sobreoscil·lacions importants i canvis
amples de llum. Un suport més justificat no valida la continuació numèrica.

Separar també domini, farciment i normalització. MGN usa extrems de la font:
el seu màxim pot canviar molt quan es readmeten píxels sota la fotografia
lunar, alterant el terme global a tot el llenç. Per a una prova causal del
farciment cal normalització comuna o separar explícitament els termes.
L’oracle i el candidat han d’usar els mateixos límits per cada escena.

Una diferència radiomètrica entre èpoques no justifica per si sola corregir
una exposició. Comparar parelles fixes i el seu pes real dins de l’apilat.
A les marques 246, la banda tardana D<0 amb dèficit tenia una fracció màxima
de pes CFA-G de 9,19·10⁻⁷. Un dèficit hipotètic del 36% tindria un efecte
lineal màxim de 3,31·10⁻⁷ relatiu, condicionat a radiància comuna; això no
és una cota del compost filtrat ni valida els valors de cada fotograma.
No s’ha aplicat una correcció uniforme d’exposició.

Els controls que injecten també en zona físicament desconeguda combinen
retenció del senyal observat i hipòtesi de continuació. Cal conservar les
fallades mesurades; un control addicional només visible o d’interior ocult
pot separar hipòtesis, però no converteix la prova anterior en PASS.
'''
 p.write_text(s);globalp.write_bytes(p.read_bytes());save(out/'REFERENCE_CORRECTION.json',{'utc':datetime.now(timezone.utc).isoformat(),'before':before,'after_sha256':sha(p),'global_copy_exact':sha(p)==sha(globalp),'reason':'correct unsupported universal input-domain prescription; no new candidate accepted','evidence':['marks246_R02/METRICS.json','weight_bound_R02/RECEIPT.json','filters_physical_E2/NOT_PROMOTED.json']})
 print('DOMAIN_LESSON_RECTIFIED')
if __name__=='__main__':guard();main()
