from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from tempfile import NamedTemporaryFile
import xml.etree.ElementTree as ET, shutil, sys
P='http://schemas.openxmlformats.org/presentationml/2006/main'; A='http://schemas.openxmlformats.org/drawingml/2006/main'; N={'p':P,'a':A}; U=9525
for k,v in [('p',P),('a',A)]: ET.register_namespace(k,v)
def q(n,t): return '{%s}%s'%(n,t)
def S(p,n,t,**a): return ET.SubElement(p,q(n,t),a)
def text(sp,s):
 a=sp.findall('.//a:t',N)
 if a: a[0].text=s
 for x in a[1:]: x.text=''
def geom(sp,x,y,w,h):
 z=sp.find('./p:spPr/a:xfrm',N)
 if z is None:return
 o=z.find('a:off',N); e=z.find('a:ext',N)
 for n,v in [('x',x),('y',y)]: o.set(n,str(int(v*U)))
 for n,v in [('cx',w),('cy',h)]: e.set(n,str(int(v*U)))
def shapes(r): return r.findall('.//p:sp',N)
def layout(r,n):
 ss=shapes(r)
 if n==54:
  for i,s in enumerate(ss[5:10]): geom(s,58+i*232,140,210 if i<4 else 268,128)
 if n==55:
  vals=['Baseline  0.3585','Tuned ByteTrack  0.3850','Adaptive Threshold/NMS  0.4095','Adaptive Resolution  0.4737']
  for i,s in enumerate(ss[5:9]): geom(s,100+i*275,250,210,250); text(s,vals[i])
 if n==56:
  vals=['A0  Baseline  0.3585  2508  -','A1  Tuned ByteTrack  0.3850  2148  -360','A2  Adaptive threshold/NMS  0.4095  2136  -12','A3  Adaptive resolution  0.4737  2695  +559','A4  Grayscale ReID  0.4735  2737  +42']
  for i,s in enumerate(ss[5:10]): geom(s,70,150+i*65,1120,48); text(s,vals[i])
 if n==58:
  vals=['A0  30.8 FPS','A1  30.1 FPS','A2  29.8 FPS','A3  28.9 FPS']
  for i,s in enumerate(ss[5:9]): geom(s,100+i*170,250,145,250); text(s,vals[i])
 if n==59:
  vals=['MOTA  |  19.718  |  22.999  |  +3.281','HOTA  |  28.418  |  33.017  |  +4.599','IDF1  |  32.716  |  40.021  |  +7.305','IDS  |  1238  |  994  |  -244','Processing FPS  |  44.181  |  37.686  |  real-time']
  for i,s in enumerate(ss[5:10]): geom(s,70,150+i*65,630,48); text(s,vals[i])
  for p in r.findall('.//p:pic',N): geom(p,760,210,420,236)
def main(p):
 with ZipFile(p) as z: infos=z.infolist(); data={i.filename:z.read(i.filename) for i in infos}
 for n in (54,55,56,58,59):
  r=ET.fromstring(data[f'ppt/slides/slide{n}.xml']); layout(r,n); data[f'ppt/slides/slide{n}.xml']=ET.tostring(r,encoding='utf-8',xml_declaration=True)
 with NamedTemporaryFile(dir=Path(p).parent,suffix='.pptx',delete=False) as f: tmp=Path(f.name)
 with ZipFile(tmp,'w',ZIP_DEFLATED) as z:
  for i in infos: z.writestr(i,data[i.filename])
 shutil.copystat(p,tmp); tmp.replace(p)
if __name__=='__main__': main(Path(sys.argv[1]).resolve())
