from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from tempfile import NamedTemporaryFile
from copy import deepcopy
import xml.etree.ElementTree as ET, shutil, sys
P='http://schemas.openxmlformats.org/presentationml/2006/main'; A='http://schemas.openxmlformats.org/drawingml/2006/main'; R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'; N={'p':P,'a':A,'r':R};U=9525
for k,v in [('p',P),('a',A),('r',R)]:ET.register_namespace(k,v)
def q(n,t):return '{%s}%s'%(n,t)
def S(p,n,t,**a):return ET.SubElement(p,q(n,t),a)
def geom(sp,x,y,w,h):
 z=sp.find('./p:spPr/a:xfrm',N);o=z.find('a:off',N);e=z.find('a:ext',N)
 o.set('x',str(int(x*U)));o.set('y',str(int(y*U)));e.set('cx',str(int(w*U)));e.set('cy',str(int(h*U)))
def text(sp,s):
 a=sp.findall('.//a:t',N)
 if a:a[0].text=s
 for x in a[1:]:x.text=''
def style(sp,size=16,color='172B4D',bold=False):
 for r in sp.findall('.//a:rPr',N)+sp.findall('.//a:defRPr',N)+sp.findall('.//a:endParaRPr',N):
  r.set('sz',str(size*100));r.set('b','1' if bold else '0');lat=r.find('a:latin',N)
  if lat is None:lat=S(r,A,'latin')
  lat.set('typeface','Helvetica Neue');sf=r.find('a:solidFill',N)
  if sf is None:sf=S(r,A,'solidFill')
  for c in list(sf):sf.remove(c)
  S(sf,A,'srgbClr',val=color)
def clear(root):
 tree=root.find('p:cSld/p:spTree',N); old=list(tree)[2:]; template=next((deepcopy(x) for x in old if x.find('.//a:t',N) is not None), deepcopy(old[0]) if old else None)
 pics=[deepcopy(x) for x in old if x.tag==q('p','pic')]
 for x in old:tree.remove(x)
 return tree,template,pics
def add(tree,tpl,x,y,w,h,s,size=16,color='172B4D',bold=False):
 sp=deepcopy(tpl);geom(sp,x,y,w,h);text(sp,s);style(sp,size,color,bold);tree.append(sp);return sp
def layout(root,n):
 tree,tpl,pics=clear(root)
 if tpl is None:return
 if n==54:
  vals=[('System','MOTA','IDF1','HOTA','IDS','FPS'),('A0 Baseline','0.3585','0.4737','0.5818','2508','30.8'),('A1 Tuned ByteTrack','0.3850','0.5118','0.6055','2148','30.1'),('A2 Adaptive Threshold/NMS','0.4095','0.5297','0.6249','2136','29.8'),('A3 Adaptive Resolution','0.4737','0.5740','0.6744','2695','28.9')]
  xs=[70,350,520,680,840,1000];ws=[260,140,140,140,140,180]
  for i,row in enumerate(vals):
   for j,v in enumerate(row):add(tree,tpl,xs[j],145+i*52,ws[j],40,v,14,'FFFFFF' if i==0 else ('2563EB' if i==4 else '172B4D'),i in (0,4))
  for j,v in enumerate(['+32.1% MOTA','+21.2% IDF1','+15.9% HOTA','-17.0% false negatives']):add(tree,tpl,70+j*280,460,250,58,v,15,'2E7D5B',True)
 elif n==55:
  add(tree,tpl,70,140,1140,34,'MOTA progression',18,'172B4D',True)
  vals=[('A0 Baseline','0.3585'),('A1 Tuned ByteTrack','0.3850'),('A2 Adaptive Threshold/NMS','0.4095'),('A3 Adaptive Resolution / adopted','0.4737')]
  for i,(lab,v) in enumerate(vals):
   x=80+i*290;add(tree,tpl,x,215,250,34,lab,13,'172B4D',True);add(tree,tpl,x,260,250,44,'BAR  '+v,18,'2563EB' if i==3 else '0B4F8A',True)
  add(tree,tpl,70,390,1140,34,'IDS progression: 2508  |  2148  |  2136  |  2695',15,'172B4D',True);add(tree,tpl,70,450,1140,34,'FPS: 30.8  |  30.1  |  29.8  |  28.9',15,'172B4D',True);add(tree,tpl,70,540,1140,44,'25 FPS and above means it can run live',14,'C26A00',True)
 elif n==56:
  heads=['Step','What was added','MOTA','IDS','Delta IDS'];xs=[70,190,650,850,1010];ws=[100,440,160,140,170]
  rows=[heads,['A0','Baseline','0.3585','2508','-'],['A1','Tuned ByteTrack','0.3850','2148','-360'],['A2','Adaptive threshold/NMS','0.4095','2136','-12'],['A3','Adaptive resolution','0.4737','2695','+559'],['A4','Grayscale ReID','0.4735','2737','+42']]
  for i,row in enumerate(rows):
   for j,v in enumerate(row):add(tree,tpl,xs[j],140+i*50,ws[j],38,v,13,'FFFFFF' if i==0 else ('2563EB' if i==4 else '172B4D'),i in (0,4))
  for j,v in enumerate(['A1 -> A2  +0.0245 MOTA / -12 IDS','A2 -> A3  +0.0642 MOTA / +559 IDS','A3 -> A4  no meaningful benefit']):add(tree,tpl,70+j*380,490,350,72,v,13,'C26A00' if j==2 else '0B4F8A',True)
 elif n==58:
  add(tree,tpl,70,140,700,34,'Accuracy-speed operating points',18,'172B4D',True);pts=['A0 - 30.8 FPS / MOTA 0.3585','A1 - 30.1 FPS / MOTA 0.3850','A2 - 29.8 FPS / MOTA 0.4095','A3 - 28.9 FPS / MOTA 0.4737']
  for i,v in enumerate(pts):add(tree,tpl,90+i*165,280,150,72,v,13,'2563EB' if i==3 else '0B4F8A',True)
  add(tree,tpl,90,410,650,32,'25 FPS real-time threshold',14,'C26A00',True);add(tree,tpl,820,180,350,100,'A3 adopted',22,'2563EB',True);add(tree,tpl,820,320,350,120,'Evaluator-dependent IDS\nLegacy: 2695 vs 2508\nIoU >= 0.50: 1092 vs 1237',14,'5B6B7A',False)
 elif n==59:
  heads=['Metric','Baseline','AC-MOT','Change'];xs=[70,290,450,600];ws=[210,150,150,120];rows=[heads,['MOTA','19.718','22.999','+3.281'],['HOTA','28.418','33.017','+4.599'],['IDF1','32.716','40.021','+7.305'],['IDS','1238','994','-244'],['Processing FPS','44.181','37.686','real-time']]
  for i,row in enumerate(rows):
   for j,v in enumerate(row):add(tree,tpl,xs[j],140+i*58,ws[j],42,v,15,'FFFFFF' if i==0 else ('2563EB' if j==2 else '172B4D'),i in (0,5))
  add(tree,tpl,760,170,420,32,'SAME PROTOCOL',14,'0B4F8A',True);add(tree,tpl,760,215,420,236,'Baseline vs AC-MOT - qualitative evidence',14,'5B6B7A',False);add(tree,tpl,760,480,420,70,'Full AC-MOT + tuned ByteTrack\nnew_track_thresh 0.24 | match_thresh 0.88\nlive FP16 | official comparison',13,'172B4D',True)
def main(path):
 with ZipFile(path) as z:infos=z.infolist();data={i.filename:z.read(i.filename) for i in infos}
 for n in (54,55,56,58,59):
  r=ET.fromstring(data[f'ppt/slides/slide{n}.xml']);layout(r,n);data[f'ppt/slides/slide{n}.xml']=ET.tostring(r,encoding='utf-8',xml_declaration=True)
 with NamedTemporaryFile(dir=Path(path).parent,suffix='.pptx',delete=False) as f:tmp=Path(f.name)
 with ZipFile(tmp,'w',ZIP_DEFLATED) as z:
  for i in infos:z.writestr(i,data[i.filename])
 shutil.copystat(path,tmp);tmp.replace(path)
if __name__=='__main__':main(Path(sys.argv[1]).resolve())
