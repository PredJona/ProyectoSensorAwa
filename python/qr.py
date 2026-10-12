"""Utilidad opcional. El usuario debe indicar el contenido confirmado del QR."""
from pathlib import Path


def generar(contenido,ruta):
    if not isinstance(contenido,str) or not contenido.strip():
        raise ValueError('Indique el contenido confirmado del QR; no existe destino predeterminado.')
    ruta=Path(ruta)
    texto=ruta.with_suffix('.contenido.txt')
    for destino in (ruta,texto):
        if destino.exists(): raise FileExistsError(f'El destino ya existe: {destino}')
    import qrcode
    ruta.parent.mkdir(parents=True,exist_ok=True)
    with ruta.open('xb') as f:
        qrcode.make(contenido).save(f,format='PNG')
    # Texto de referencia para comparar con una lectura independiente.
    with texto.open('x',encoding='utf-8') as f: f.write(contenido)
    return ruta


def leer(ruta):
    import cv2
    imagen=cv2.imread(str(ruta))
    if imagen is None: raise ValueError('No se pudo abrir la imagen QR.')
    contenido,_,_=cv2.QRCodeDetector().detectAndDecode(imagen)
    if not contenido: raise ValueError('No se pudo decodificar el QR.')
    return contenido
