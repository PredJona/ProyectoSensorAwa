"""Ejecutar desde Proyecto1: python -m python.main resolver."""
import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

from .metodos import (A_VALIDACION, B_VALIDACION, exportar_tabla,
                      jacobi, gauss_seidel, gauss_jordan)

RAIZ=Path(__file__).resolve().parents[1]


def resolver(args):
    A,b=A_VALIDACION,B_VALIDACION
    resultados=[jacobi(A,b,args.x0,args.tol,args.max_iter),
                gauss_seidel(A,b,args.x0,args.tol,args.max_iter),gauss_jordan(A,b)]
    referencia=np.linalg.solve(A,b)
    carpeta=Path(args.salida)/'datos/resultados'
    carpeta.mkdir(parents=True,exist_ok=True)
    for r,nombre in zip(resultados[:2],('jacobi','gauss_seidel')):
        exportar_tabla(r,carpeta/f'{nombre}.csv')
    with (carpeta/'gauss_jordan_operaciones.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['paso','operacion','fila','a1','a2','a3','b'])
        for k,op in enumerate(resultados[2].operaciones):
            for i,fila in enumerate(op['matriz']):
                w.writerow([k,op['operacion'],i+1,*fila])
    resumen={'origen':'academico','A':A.tolist(),'b':b.tolist(),
             'parametros':{'x0':args.x0,'tol':args.tol,'max_iter':args.max_iter,
                           'criterio':'||h(k)-h(k-1)||inf < tol'},
             'dominancia_estricta':bool(np.all(np.abs(np.diag(A)) >
                                np.sum(np.abs(A),axis=1)-np.abs(np.diag(A)))),
             'referencia_numpy':referencia.tolist(),'metodos':[]}
    for r in resultados:
        fila={'metodo':r.metodo,'solucion':r.x.tolist(),'iteraciones':r.iteraciones if r.historial else None,
              'converge':r.converge,'motivo':r.motivo,'residuo':r.residuo.tolist(),
              'residuo_inf':float(np.linalg.norm(r.residuo,np.inf)),
              'diferencia_numpy_inf':float(np.linalg.norm(r.x-referencia,np.inf)),
              'error_final':r.historial[-1]['error_abs_inf'] if r.historial else None}
        resumen['metodos'].append(fila)
        print(f"{r.metodo}: h={np.array2string(r.x,precision=9)}, "
              f"iteraciones={fila['iteraciones']}, converge={r.converge}, "
              f"||r||inf={fila['residuo_inf']:.9g}")
    with (carpeta/'comparacion.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['metodo','h1','h2','h3','iteraciones','converge','error_final',
                    'residuo_inf','diferencia_numpy_inf'])
        for fila in resumen['metodos']:
            w.writerow([fila['metodo'],*fila['solucion'],fila['iteraciones'],fila['converge'],
                        fila['error_final'],fila['residuo_inf'],fila['diferencia_numpy_inf']])
    resumen['graficas']=[]
    if not args.sin_graficas:
        from .graficas import academicas
        resumen['graficas']=[p.relative_to(args.salida).as_posix()
                            for p in academicas(resultados,Path(args.salida)/'graficas')]
    (carpeta/'resumen.json').write_text(json.dumps(resumen,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
    print(f'Resultados académicos guardados en {carpeta}')
    return 0 if all(r.converge for r in resultados) else 2


def parser():
    p=argparse.ArgumentParser(description='Proyecto 1 — nivel de agua, Problema 11')
    sub=p.add_subparsers(dest='comando',required=True)
    r=sub.add_parser('resolver',help='Resolver el sistema académico sin Arduino')
    r.add_argument('--tol',type=float,default=.001)
    r.add_argument('--max-iter',type=int,default=100)
    r.add_argument('--x0',type=float,nargs=3,default=[0.,0.,0.])
    r.add_argument('--salida',type=Path,default=RAIZ)
    r.add_argument('--sin-graficas',action='store_true')
    sub.add_parser('puertos',help='Listar puertos seriales')
    c=sub.add_parser('capturar',help='Capturar ADC reales por USB')
    c.add_argument('--puerto',help='Ej.: /dev/ttyACM0 o COM3; autodetecta si existe solo uno')
    c.add_argument('--muestras',type=int,default=100)
    c.add_argument('--duracion',type=float,default=60.)
    c.add_argument('--baudios',type=int,default=115200,
                   help='USB UNO R4: 115200 (sketch anterior: 9600)')
    c.add_argument('--salida',type=Path,required=True,help='CSV nuevo; nunca sobrescribe capturas')
    c.add_argument('--timeout-sincronizacion',type=float,default=12.)
    c.add_argument('--timeout-inactivo',type=float,default=3.)
    v=sub.add_parser('cadencia',help='Comprobar intervalos UTC y millis sin modificar el CSV')
    v.add_argument('--csv',type=Path,required=True)
    g=sub.add_parser('graficar',help='Graficar CSV de adquisición')
    g.add_argument('--csv',type=Path,required=True)
    g.add_argument('--calibracion',type=Path)
    g.add_argument('--salida',type=Path,required=True)
    t=sub.add_parser('thingsboard',help='Publicar CSV adquirido a ThingsBoard por HTTP')
    t.add_argument('--csv',type=Path,required=True,help='CSV de adquisición ya guardado en disco')
    t.add_argument('--modo',choices=('historico','en_vivo'),default='historico',
                   help='Separa reproducción histórica de telemetría en vivo')
    t.add_argument('--config',type=Path,help='JSON local privado (fuera de Git)')
    t.add_argument('--servidor',help='URL base ThingsBoard (o THINGSBOARD_URL)')
    t.add_argument('--token',help='Token del dispositivo (o THINGSBOARD_TOKEN)')
    t.add_argument('--cursor',type=Path,help='Archivo JSON para reanudar envíos por lotes')
    t.add_argument('--calibracion',type=Path,help='Calibración validada de 3 sensores (opcional)')
    t.add_argument('--lote',type=int,default=20)
    t.add_argument('--timeout',type=float,default=5.)
    t.add_argument('--reintentos',type=int,default=3)
    t.add_argument('--seguir',action='store_true',help='Seguir filas completas de un CSV que crece')
    t.add_argument('--duracion',type=float,default=60.,help='Segundos de seguimiento; reiniciar con el mismo cursor para continuar')
    t.add_argument('--intervalo',type=float,default=.25,
                   help='Segundos entre revisiones del CSV al usar --seguir (predeterminado: 0.25)')
    q=sub.add_parser('qr',help='Generar QR solo con contenido o URL configurada explícitamente')
    q.add_argument('--contenido',help='Texto o URL explícita del QR')
    q.add_argument('--config',type=Path,help='Configuración local con dashboard_url')
    q.add_argument('--salida',type=Path,required=True)
    q.add_argument('--verificar',action='store_true',help='Decodificar y comparar; requiere OpenCV')
    return p


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        if args.comando=='resolver': return resolver(args)
        if args.comando=='puertos':
            from .comunicacion import puertos_disponibles
            for puerto,descripcion in puertos_disponibles(): print(f'{puerto}: {descripcion}')
        elif args.comando=='capturar':
            from .comunicacion import capturar
            n,invalidos=capturar(args.puerto,args.salida,args.muestras,args.duracion,
                                baudios=args.baudios,timeout_sincronizacion=args.timeout_sincronizacion,
                                timeout_inactivo=args.timeout_inactivo)
            print(f'Muestras: {n}; líneas inválidas: {invalidos}; CSV: {args.salida}')
            if n==0: return 2
        elif args.comando=='cadencia':
            from .comunicacion import verificar_cadencia
            resultado=verificar_cadencia(args.csv)
            print(json.dumps(resultado,indent=2,ensure_ascii=False))
            if not resultado['cadencia_compatible']: return 2
        elif args.comando=='graficar':
            from .graficas import mediciones
            print(mediciones(args.csv,args.salida,args.calibracion))
        elif args.comando=='thingsboard':
            from .thingsboard import cargar_configuracion,publicar_csv
            cfg=cargar_configuracion(args.config,args.servidor,args.token)
            if not cfg['servidor'] or not cfg['token']:
                raise ValueError('Configure servidor y token mediante --config, variables de entorno o argumentos.')
            res=publicar_csv(args.csv,cfg['servidor'],cfg['token'],modo=args.modo,
                             ruta_cursor=args.cursor,calibracion=args.calibracion,
                             tamano_lote=args.lote,timeout=args.timeout,reintentos=args.reintentos,
                             seguir=args.seguir,duracion=args.duracion,intervalo_s=args.intervalo)
            print(f"Publicado ({res['modo_transmision']}): {res['filas_enviadas']}/{res['filas_totales']} "
                  f"filas en {res['lotes_enviados']} lotes hacia {res['endpoint_redactado']}")
        elif args.comando=='qr':
            from .qr import generar,generar_dashboard,leer
            if args.config is not None:
                from .thingsboard import cargar_configuracion
                cfg=cargar_configuracion(args.config)
                contenido=cfg['dashboard_url']
                if not contenido:
                    raise ValueError('El archivo --config no define dashboard_url.')
                ruta=generar_dashboard(contenido,args.salida,token=cfg['token'])
            else:
                if args.contenido is None:
                    raise ValueError('Indique --contenido o --config con dashboard_url.')
                contenido=args.contenido
                if contenido.strip().lower().startswith(('http://','https://')):
                    contenido=contenido.strip()
                    from .thingsboard import cargar_configuracion
                    ruta=generar_dashboard(contenido,args.salida,token=cargar_configuracion()['token'])
                else:
                    ruta=generar(contenido,args.salida)
            if args.verificar and leer(ruta)!=contenido:
                raise ValueError('El contenido decodificado no coincide con el indicado.')
            print(f'QR guardado en {ruta}'+(' y verificado.' if args.verificar else '; decodificación pendiente.'))
        return 0
    except (ValueError,OSError,ImportError,RuntimeError) as e:
        print(f'Error: {e}',file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print('Captura interrumpida; se conserva el CSV parcial.',file=sys.stderr)
        return 130


if __name__=='__main__': sys.exit(main())
