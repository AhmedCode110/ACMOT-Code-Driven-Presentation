from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import shutil
import tempfile
import xml.etree.ElementTree as ET

P = 'http://schemas.openxmlformats.org/presentationml/2006/main'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
N = {'p': P, 'a': A}
ET.register_namespace('p', P)
ET.register_namespace('a', A)
PPTX = Path('output/ACMOT_Final_Paper_Realtime_v7.pptx').resolve()

def shape_text(shape):
    return ' / '.join((t.text or '') for t in shape.findall('.//a:t', N))

def set_text(shape, value):
    runs = shape.findall('.//a:t', N)
    if not runs:
        return
    runs[0].text = value
    for run in runs[1:]:
        run.text = ''

def set_geom(shape, x, y, cx=None, cy=None):
    off = shape.find('.//a:xfrm/a:off', N)
    ext = shape.find('.//a:xfrm/a:ext', N)
    off.set('x', str(x))
    off.set('y', str(y))
    if cx is not None:
        ext.set('cx', str(cx))
    if cy is not None:
        ext.set('cy', str(cy))

def normalize_fonts(root):
    for el in root.findall('.//a:rPr', N) + root.findall('.//a:defRPr', N):
        el.set('typeface', 'Helvetica Neue')
        el.set('latin', 'Helvetica Neue')
        el.set('ea', 'Helvetica Neue')
        el.set('cs', 'Helvetica Neue')

def fix_slide55(root):
    tree = root.find('p:cSld/p:spTree', N)
    shapes = tree.findall('p:sp', N)
    category = next((s for s in shapes if shape_text(s).strip() == 'A2'), None)
    value = next((s for s in shapes if shape_text(s).strip() == '29.8 FPS'), None)
    if category is None or value is None:
        raise RuntimeError('Slide 55 FPS source labels not found')
    new_category = deepcopy(category)
    set_text(new_category, 'A1')
    set_geom(new_category, 609479, 4279859)
    tree.append(new_category)
    new_value = deepcopy(value)
    set_text(new_value, '30.1 FPS')
    set_geom(new_value, 2077873, 4293535)
    tree.append(new_value)

def fix_slide59(root):
    for picture in root.findall('.//p:pic', N):
        if picture.find('.//a:videoFile', N) is not None:
            set_geom(picture, 609600, 1320800, 8128000, 4572000)
            return
    raise RuntimeError('Slide 59 video object not found')

with ZipFile(PPTX) as source:
    infos = source.infolist()
    data = {item.filename: source.read(item.filename) for item in infos}

for number in (54, 55, 56, 58, 59):
    name = f'ppt/slides/slide{number}.xml'
    root = ET.fromstring(data[name])
    normalize_fonts(root)
    if number == 55:
        fix_slide55(root)
    if number == 59:
        fix_slide59(root)
    data[name] = ET.tostring(root, encoding='utf-8', xml_declaration=True)

with tempfile.NamedTemporaryFile(prefix='acmot_v7_fix_', suffix='.pptx', dir=PPTX.parent, delete=False) as handle:
    temporary = Path(handle.name)
with ZipFile(temporary, 'w', ZIP_DEFLATED) as destination:
    for item in infos:
        destination.writestr(item, data[item.filename])
shutil.copystat(PPTX, temporary)
temporary.replace(PPTX)
print('Applied targeted V7 fixes: Slide 55 A1 FPS label; Slide 59 video frame; Helvetica Neue on Results slides.')
