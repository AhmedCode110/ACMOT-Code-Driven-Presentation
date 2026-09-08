from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import shutil, tempfile
import xml.etree.ElementTree as ET
PPTX=Path('output/ACMOT_Final_Paper_Realtime_v6.pptx').resolve()
VIDEO=Path('assets/videos/uav0000249_00001_v_ACMOT_PRESENTATION_COMPACT.mp4').resolve()
P='http://schemas.openxmlformats.org/presentationml/2006/main'
A='http://schemas.openxmlformats.org/drawingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PR='http://schemas.openxmlformats.org/package/2006/relationships'
CT='http://schemas.openxmlformats.org/package/2006/content-types'
for k,v in [('p',P),('a',A),('r',R)]: ET.register_namespace(k,v)
slide_name='ppt/slides/slide59.xml'
rels_name='ppt/slides/_rels/slide59.xml.rels'
media_name='ppt/media/acmot_v5_evidence.mp4'
video_rid='rIdACMOTVideo59'
with ZipFile(PPTX) as src: entries={i.filename:src.read(i.filename) for i in src.infolist()}
rels=ET.fromstring(entries[rels_name])
image_rid=None
for rel in rels.findall('{%s}Relationship'%PR):
    t=rel.get('Target','')
    if '/media/' in t and t.lower().endswith(('.png','.jpeg','.jpg')): image_rid=rel.get('Id'); break
if not image_rid: raise SystemExit('No poster image relationship on slide 59')
ET.SubElement(rels,'{%s}Relationship'%PR,{'Id':video_rid,'Type':'http://schemas.openxmlformats.org/officeDocument/2006/relationships/video','Target':'../media/acmot_v5_evidence.mp4'})
entries[rels_name]=ET.tostring(rels,encoding='utf-8',xml_declaration=True)
slide=ET.fromstring(entries[slide_name])
sp=slide.find('p:cSld/p:spTree',{'p':P})
if sp is None: raise SystemExit('Slide 59 shape tree missing')
ids=[]
for c in sp.findall('.//p:cNvPr',{'p':P}):
    try: ids.append(int(c.get('id','0')))
    except ValueError: pass
pic=ET.Element('{%s}pic'%P)
nv=ET.SubElement(pic,'{%s}nvPicPr'%P)
ET.SubElement(nv,'{%s}cNvPr'%P,{'id':str(max(ids+[1])+1),'name':'AC-MOT embedded video evidence'})
ET.SubElement(nv,'{%s}cNvPicPr'%P)
nvpr=ET.SubElement(nv,'{%s}nvPr'%P)
ET.SubElement(nvpr,'{%s}videoFile'%A,{'{%s}link'%R:video_rid})
bf=ET.SubElement(pic,'{%s}blipFill'%P)
ET.SubElement(bf,'{%s}blip'%A,{'{%s}embed'%R:image_rid})
st=ET.SubElement(bf,'{%s}stretch'%A); ET.SubElement(st,'{%s}fillRect'%A)
sppr=ET.SubElement(pic,'{%s}spPr'%P)
x=ET.SubElement(sppr,'{%s}xfrm'%A)
ET.SubElement(x,'{%s}off'%A,{'x':'7130000','y':'3260000'})
ET.SubElement(x,'{%s}ext'%A,{'cx':'4200000','cy':'2362500'})
pg=ET.SubElement(sppr,'{%s}prstGeom'%A,{'prst':'rect'}); ET.SubElement(pg,'{%s}avLst'%A)
sp.append(pic); entries[slide_name]=ET.tostring(slide,encoding='utf-8',xml_declaration=True)
ct=ET.fromstring(entries['[Content_Types].xml'])
if not any(e.get('Extension')=='mp4' for e in ct.findall('{%s}Default'%CT)):
    ET.SubElement(ct,'{%s}Default'%CT,{'Extension':'mp4','ContentType':'video/mp4'})
entries['[Content_Types].xml']=ET.tostring(ct,encoding='utf-8',xml_declaration=True)
with tempfile.NamedTemporaryFile(prefix='acmot_v5_',suffix='.pptx',dir=PPTX.parent,delete=False) as f: tmp=Path(f.name)
with ZipFile(tmp,'w',ZIP_DEFLATED) as dst:
    for n,b in entries.items(): dst.writestr(n,b)
    dst.write(VIDEO,media_name)
shutil.copystat(PPTX,tmp); tmp.replace(PPTX)
print('embedded',VIDEO.name,'as',media_name,'relationship',video_rid)
