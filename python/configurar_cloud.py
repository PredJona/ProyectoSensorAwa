"""Introduce el Access Token desde una terminal con eco desactivado.

Uso: .venv/bin/python -m python.configurar_cloud
El token solo se guarda fuera del repositorio, nunca se acepta como argumento.
"""
import argparse
import getpass
import json
import sys
import warnings
from pathlib import Path

from .comunicacion import guardar_json_atomico
from .thingsboard import cargar_configuracion

RAIZ=Path(__file__).resolve().parents[1]
CLOUD='https://thingsboard.cloud'
CONFIG=Path.home()/'.config/proyectosensorawa/thingsboard.json'


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=CONFIG)
    parser.add_argument('--reemplazar-token',action='store_true',
                        help='Sustituir de forma oculta el token local después de regenerarlo en Cloud')
    args=parser.parse_args(argv)
    try:
        ruta=args.config.expanduser()
        if ruta.is_symlink() or ruta.parent.is_symlink() or ruta.resolve().is_relative_to(RAIZ):
            raise ValueError('Destino no privado.')
        if not sys.stdin.isatty():
            print('Ejecute este comando directamente en una terminal interactiva.',file=sys.stderr)
            return 2
        datos={'servidor':CLOUD,'token':'','dashboard_url':''}
        if ruta.exists():
            contenido=json.loads(ruta.read_text(encoding='utf-8'))
            if not isinstance(contenido,dict): raise ValueError('Configuración inválida.')
            datos.update(contenido)
        cfg=cargar_configuracion(servidor=datos['servidor'],
                                token='' if args.reemplazar_token else datos.get('token') or '')
        if cfg['servidor']!=CLOUD: raise ValueError('Servidor distinto de ThingsBoard Cloud.')
        ruta.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        ruta.parent.chmod(0o700)
        if ruta.exists(): ruta.chmod(0o600)
        if cfg['token']:
            print('Ya existe un token configurado; se conserva sin mostrarlo.')
            return 0
        # getpass no puede degradarse silenciosamente a entrada con eco.
        with warnings.catch_warnings():
            warnings.simplefilter('error',getpass.GetPassWarning)
            token=getpass.getpass('Access Token del dispositivo (entrada oculta): ')
        validada=cargar_configuracion(servidor=CLOUD,token=token)
        if not validada['token']: raise ValueError('Token vacío.')
        datos.update(servidor=CLOUD,token=validada['token'])
        guardar_json_atomico(ruta,datos)  # Temporal privado 0600 y reemplazo atómico.
        print('Token guardado en el archivo privado con permisos 0600; contenido oculto.')
        return 0
    except KeyboardInterrupt:
        print('Configuración cancelada; no se guardó el token.',file=sys.stderr)
        return 130
    except (ValueError,OSError,EOFError,getpass.GetPassWarning):
        # No incluir la excepción: podría contener datos de una dependencia.
        print('No se guardó el token. Revise la ruta privada, la configuración y la terminal.',file=sys.stderr)
        return 2


if __name__=='__main__': sys.exit(main())
