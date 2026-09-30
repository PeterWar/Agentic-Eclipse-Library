from pathlib import Path
import re,json,csv,hashlib
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image
from report_data import R,O,pages,sources
F=Path('/Users/USUARI/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype')
pdfmetrics.registerFont(TTFont('DV',str(F/'DejaVuSans.ttf')));pdfmetrics.registerFont(TTFont('DV-Bold',str(F/'DejaVuSans-Bold.ttf')));pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold')
def clean(s):
 s=s.replace('−','-').replace('–','-').replace('—','-')
 s=re.sub(r'(?<=[a-zà-ú])(?=\d)', ' ',s);s=re.sub(r'(?<=\d)(?=[a-zà-ú])',' ',s);s=re.sub(r'(?<=\d)(?=DN16)',' ',s)
 s=re.sub(r'(?<=[a-zà-ú])(?=[A-Z])',' ',s);s=re.sub(r'(?<=\w)(?=[σφ])',' ',s)
 s=re.sub(r'(?<=\d)(?=[A-Z][A-Z])',' ',s)
 s=s.replace('→',' → ').replace('entre-','entre -').replace('mediana-','mediana -').replace('r<','r < ').replace('DHS400','DHS 400').replace('DHS530','DHS 530')
 s=s.replace('lroc_color_poles_4 k.tif','lroc_color_poles_4k.tif').replace('eines-ia-py 312','eines-ia-py312')
 s=s.replace('Num Py','NumPy').replace('Sci Py','SciPy')
 for a,b in [('dePere','de Pere'),('deLROC','de LROC'),('ambDHS','amb DHS'),('deV68','de V68'),('laV53','la V53'),('aCamera','a Camera'),('aSony','a Sony'),('deSony','de Sony'),('iVixen','i Vixen'),('elPSB','el PSB'),('deS8','de S8'),('totS8','tot S8'),('capV69','cap V69'),('LROC62','LROC 62'),('lunar30','lunar 30'),('capa62','capa 62'),('portaPhotoshop','porta Photoshop')]:s=s.replace(a,b)
 return s
styles={'body':ParagraphStyle('body',fontName='DV',fontSize=10.4,leading=15,textColor=colors.HexColor('#202020')),'small':ParagraphStyle('small',fontName='DV',fontSize=8.2,leading=11.3,textColor=colors.HexColor('#555555')),'title':ParagraphStyle('title',fontName='DV-Bold',fontSize=21,leading=26),'table':ParagraphStyle('table',fontName='DV',fontSize=9,leading=12)}
pdf=O/'ESTUDI_TACA_EARTHSHINE.pdf';assert not pdf.exists();c=canvas.Canvas(str(pdf),pagesize=(595.28,841.89));c.setTitle('La taca fosca de l’earthshine');c.setAuthor('');margin=44;w=507.28;log=[];md=[]
for n,page in enumerate(pages,1):
 y=797.89;md.append(('# ' if n==1 else '## ')+clean(page['title'])+'\n')
 def paragraph(txt,style='body',after=11):
  global y
  p=Paragraph(clean(txt),styles[style]);pw,ph=p.wrap(w,750);assert y-ph>38,(n,y,ph,txt[:80]);p.drawOn(c,margin,y-ph);y-=ph+after
 paragraph(page['title'],'title',19)
 for p in page['paras']:
  paragraph(p);md.append(clean(p).replace('<b>','**').replace('</b>','**')+'\n')
 if 'table' in page:
  data=[[Paragraph(escape(clean(v)),styles['table']) for v in row] for row in page['table']];nc=len(data[0]);ww=[w/nc]*nc
  if nc==2:ww=[w*.35,w*.65]
  tb=Table(data,colWidths=ww,hAlign='LEFT');tb.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eeeeee')),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#999999')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#dddddd')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));tw,th=tb.wrap(w,700);assert y-th>38,(n,'table',y,th);tb.drawOn(c,margin,y-th);y-=th+15
  table=page['table'];md.append('| '+' | '.join(map(clean,table[0]))+' |');md.append('| '+' | '.join(['---']*nc)+' |');md.extend('| '+' | '.join(map(clean,row))+' |' for row in table[1:]);md.append('')
 if 'image' in page:
  im=Image.open(page['image'])
  if n==3:im=im.crop((0,0,im.width,588))
  ih=w*im.height/im.width;assert y-ih>70,(n,'image',y,ih);c.drawImage(ImageReader(im),margin,y-ih,width=w,height=ih);y-=ih+7
  cap=page['caption']
  if n==3:cap='Bandaσ16-64: V68, DHS400 i DHS530, d’esquerra a dreta. Guany i offset ajustats fora de la marca; cap píxel de les referències entra a la fotografia.'
  paragraph(cap,'small',12);md.append('!['+clean(page['caption'])+']('+page['image']+')\n')
 if page.get('sources'):
  for i,(label,url) in enumerate(sources,1):
   label=clean(label);link=escape(url,{'"':'&quot;'})
   if url.startswith('http'):txt=f'{i}. <link href="{link}" color="#333333">{escape(label)}</link>'
   else:txt=f'{i}. {escape(label)}'
   paragraph(txt,'small',10);md.append(f'{i}. [{label}]({url})')
 if page.get('refs'):
  labels=[]
  for i in page['refs']:
   label,url=sources[i-1];short=['NASA SVS','LROC WAC Hapke','Qiu et al.2003','DHS400','DHS530','DHS200','Rebuts locals','Diagnòstic V68'][i-1]
   labels.append(f'{i}. '+(f'<link href="{escape(url)}">{short}</link>' if url.startswith('http') else short))
  paragraph('Fonts: '+' · '.join(labels),'small',0)
 c.setFont('DV',8);c.setFillColor(colors.HexColor('#666666'));c.drawRightString(551,24,str(n));log.append(dict(page=n,bottom=y));c.showPage()
c.save();(O/'RESULTAT.md').write_text('\n'.join(md)+'\n');(O/'C1_layout.json').write_text(json.dumps(log,indent=2)+'\n')
rows=json.loads((O/'A6_DHS.json').read_text())['rows']
with (O/'COMPARACIONS_NUMERIQUES.csv').open('w') as f:
 wr=csv.DictWriter(f,fieldnames=rows[0].keys());wr.writeheader();wr.writerows(rows)
print(pdf);print('PAGES',len(pages),'minimum content bottom',min(q['bottom'] for q in log),flush=True)
