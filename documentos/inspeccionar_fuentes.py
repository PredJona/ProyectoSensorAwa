"""Inventario y extracción OOXML reproducibles, sin ejecutar código de clase."""
import csv
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

RAIZ=Path(__file__).resolve().parents[2]
DESTINO=Path(__file__).resolve().parent/'fuentes_extraidas'


def main():
    DESTINO.mkdir(exist_ok=True)
    originales=[]
    for p in sorted(RAIZ.rglob('*')):
        relativo=p.relative_to(RAIZ)
        if any(parte.startswith('.') or parte in ('Proyecto1','__pycache__') for parte in relativo.parts): continue
        if not p.is_file(): continue
        originales.append(p)
    with (DESTINO/'inventario.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(['ruta','extension','bytes'])
        for p in originales: w.writerow([p.relative_to(RAIZ),p.suffix.lower(),p.stat().st_size])
    for p in originales:
        if p.suffix.lower() not in ('.docx','.pptx','.zip'): continue
        with ZipFile(p) as z:
            if p.suffix.lower()=='.zip':
                texto='\n'.join(z.namelist())
            else:
                nombres=['word/document.xml'] if p.suffix.lower()=='.docx' else sorted(
                    (n for n in z.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml')),
                    key=lambda n:int(n.rsplit('slide',1)[1].split('.')[0]))
                lineas=[f'FUENTE: {p.relative_to(RAIZ)}']
                for nombre in nombres:
                    lineas.append('\nSECCIÓN: '+nombre)
                    for el in ET.fromstring(z.read(nombre)).iter():
                        if el.tag.endswith('}p'):
                            texto=''.join(t.text or '' for t in el.iter() if t.tag.endswith('}t'))
                            if texto: lineas.append(texto)
                for n in ('docProps/core.xml',):
                    if n in z.namelist(): lineas.extend(['\nMETADATOS:',z.read(n).decode()])
                media=[n for n in z.namelist() if '/media/' in n]
                lineas.extend(['\nRECURSOS EMBEBIDOS:',*media])
                texto='\n'.join(lineas)
            (DESTINO/(p.stem+'.txt')).write_text(texto,encoding='utf-8')
    print(f'{len(originales)} archivos originales; extensiones: {dict(Counter(p.suffix.lower() for p in originales))}')


if __name__=='__main__': main()
