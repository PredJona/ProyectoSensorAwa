"""Pruebas de telemetría ThingsBoard y validación de URL QR con servidor HTTP simulado."""
import csv
import http.server
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
import time
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from pathlib import Path

from python import qr, thingsboard

RAIZ = Path(__file__).resolve().parents[1]


class _ServidorSimulado:
    def __init__(self):
        self.recibidos = []
        self.rutas = []
        self.codigos_respuesta = []
        self.retardos_respuesta = []
        self.intentos = []
        self.redireccion = None
        parent = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                parent.intentos.append((self.path,None))
                self.send_response(200)
                self.end_headers()

            def do_POST(self):
                n = int(self.headers.get('Content-Length', '0'))
                cuerpo = self.rfile.read(n).decode('utf-8')
                codigo = parent.codigos_respuesta.pop(0) if parent.codigos_respuesta else 200
                parent.intentos.append((self.path,json.loads(cuerpo)))
                if parent.retardos_respuesta:
                    time.sleep(parent.retardos_respuesta.pop(0))
                if 200 <= codigo < 300:
                    parent.rutas.append(self.path)
                    parent.recibidos.append(json.loads(cuerpo))
                self.send_response(codigo)
                self.send_header('Content-Type', 'application/json')
                if parent.redireccion:
                    self.send_header('Location',parent.redireccion)
                self.end_headers()
                try: self.wfile.write(b'{"ok":true}')
                except (BrokenPipeError,ConnectionResetError): pass

            def log_message(self, format, *args):
                return

        self.httpd = http.server.HTTPServer(('127.0.0.1', 0), Handler)
        self.url = f'http://127.0.0.1:{self.httpd.server_port}'
        self.hilo = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.hilo.start()

    def cerrar(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.hilo.join(timeout=1)


class ThingsBoardTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.carpeta = Path(self.tmp.name)

    def _crear_csv(self, nombre='SINTETICO_ensayo.csv', filas=3, origen='experimental'):
        ruta = self.carpeta / nombre
        with ruta.open('w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['timestamp_utc', 't_ms', 'adc1', 'adc2', 'adc3', 'origen'])
            valores = [(0, 49, 50), (149, 150, 299), (300, 1023, 10)]
            for i in range(filas):
                a1, a2, a3 = valores[i % len(valores)]
                w.writerow([f'2026-10-16T07:00:{i:02d}+00:00', (i + 1) * 500, a1, a2, a3, origen])
        return ruta

    def test_publica_adc_sin_calibrar_y_separa_historico_de_en_vivo(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        csv_path = self._crear_csv(filas=3)
        res_hist = thingsboard.publicar_csv(
            csv_path, srv.url, 'tok_privado_99', modo='historico', tamano_lote=2)
        self.assertEqual(res_hist['filas_enviadas'], 3)
        self.assertEqual(res_hist['lotes_enviados'], 2)
        self.assertFalse(res_hist['calibracion_valida'])
        self.assertNotIn('tok_privado_99', res_hist['endpoint_redactado'])
        self.assertEqual(srv.rutas[0], '/api/v1/tok_privado_99/telemetry')
        primera = srv.recibidos[0][0]['values']
        self.assertEqual((primera['adc1'], primera['adc2'], primera['adc3']), (0, 49, 50))
        self.assertEqual((primera['color_adc1'], primera['color_adc2'], primera['color_adc3']),
                         ('verde', 'verde', 'azul'))
        self.assertFalse(primera['calibracion_valida'])
        self.assertNotIn('altura1', primera)
        self.assertNotIn('altura2', primera)
        self.assertNotIn('altura3', primera)
        self.assertTrue(all(v is not None for v in primera.values()))
        self.assertEqual(primera['modo_transmision'], 'historico')
        self.assertFalse(primera['es_tiempo_real'])

        with self.assertRaisesRegex(ValueError, 'seguir'):
            thingsboard.publicar_csv(csv_path, srv.url, 'tok_privado_99', modo='en_vivo')

    def test_cursor_no_se_reutiliza_para_otro_dispositivo_o_modo(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        ruta = self._crear_csv()
        cursor = self.carpeta/'cursor.json'
        thingsboard.publicar_csv(ruta,srv.url,'dispositivo_A',ruta_cursor=cursor)
        with self.assertRaisesRegex(ValueError, 'destino|configuración'):
            thingsboard.publicar_csv(ruta,srv.url,'dispositivo_B',ruta_cursor=cursor)
        self.assertNotIn('dispositivo_A',cursor.read_text())

    def test_calibracion_invalida_y_colisiones_ts_no_publican_nada(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        ruta = self._crear_csv()
        with self.assertRaises(ValueError):
            thingsboard.publicar_csv(ruta,srv.url,'token_test_1',calibracion={'unidad':'cm','sensores':{}})
        texto = ruta.read_text().replace('07:00:01','07:00:00')
        ruta.write_text(texto)
        with self.assertRaisesRegex(ValueError, 'milisegundo'):
            thingsboard.publicar_csv(ruta,srv.url,'token_test_1')
        self.assertEqual(srv.recibidos,[])

    def test_seguimiento_publica_solo_filas_completas_y_recupera_red(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        ruta = self._crear_csv(filas=1)
        # Fecha actual SINTÉTICA: prueba clasificación de envío, no edad física.
        fecha = datetime.now(timezone.utc)
        ruta.write_text(ruta.read_text().replace('2026-10-16T07:00:00+00:00',fecha.isoformat()))
        ruta.with_suffix('.sesion.json').write_text(json.dumps({
            'version':1,'sincronizacion_requerida':True,'inicio_efectivo_utc':fecha.isoformat(),
            'origen':'experimental','estado':'capturando'}))
        cursor = self.carpeta/'seguimiento.cursor.json'
        srv.codigos_respuesta=[503,200,200]
        # Un productor agrega primero una fila parcial y luego su terminador.
        def agregar():
            import time
            time.sleep(.08)
            with ruta.open('a') as f:
                f.write((fecha+timedelta(seconds=.5)).isoformat()+',1000,1,2,3,experimental')
            time.sleep(.08)
            with ruta.open('a') as f: f.write('\n')
        hilo=threading.Thread(target=agregar)
        hilo.start()
        try:
            res=thingsboard.publicar_csv(ruta,srv.url,'token_test_2',modo='en_vivo',seguir=True,
                duracion=.35,intervalo_s=.02,ruta_cursor=cursor,reintentos=1)
        finally:
            hilo.join()
        self.assertEqual(res['filas_enviadas'],2)
        self.assertEqual([r['values']['t_ms'] for lote in srv.recibidos for r in lote],[500,1000])
        self.assertEqual(srv.recibidos[0][0]['values']['modo_transmision'],'en_vivo')
        self.assertEqual(json.loads(cursor.read_text())['filas_enviadas'],2)

    def test_en_seguimiento_las_filas_antiguas_son_historicas(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        ruta = self._crear_csv(filas=1)
        thingsboard.publicar_csv(ruta,srv.url,'token_test_3',modo='en_vivo',seguir=True,
                                duracion=.03,intervalo_s=.01)
        self.assertFalse(srv.recibidos[0][0]['values']['es_tiempo_real'])

    def test_rechazos_http_redirect_y_limite_de_reintentos(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        destino = _ServidorSimulado()
        self.addCleanup(destino.cerrar)
        fila={'ts':1700000000000,'values':{'adc1':1,'adc2':2,'adc3':3}}
        for codigo in (400,401,403,404,405,413,302,303,307):
            with self.subTest(codigo=codigo):
                srv.codigos_respuesta=[codigo]
                srv.redireccion=destino.url+'/api/v1/token_no_debe_llegar/telemetry'
                antes=len(srv.intentos)
                with self.assertRaises(RuntimeError) as ctx:
                    thingsboard.publicar_lote(srv.url,'secreto_http_1',[fila],reintentos=3,espera_inicial_s=0)
                self.assertNotIn('secreto_http_1',str(ctx.exception))
                self.assertEqual(len(srv.intentos)-antes,1)
        self.assertEqual(destino.intentos,[])
        srv.redireccion=None
        srv.codigos_respuesta=[429,503,200]
        self.assertEqual(thingsboard.publicar_lote(srv.url,'test_http_2',[fila],espera_inicial_s=0),3)

    def test_timeout_http_no_avanza_cursor_y_reintento_recupera(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        ruta=self._crear_csv(filas=1)
        cursor=self.carpeta/'timeout.cursor.json'
        srv.retardos_respuesta=[.08]
        with self.assertRaises(ConnectionError):
            thingsboard.publicar_csv(ruta,srv.url,'test_timeout',ruta_cursor=cursor,timeout=.01,reintentos=1)
        self.assertFalse(cursor.exists())
        time.sleep(.09)
        thingsboard.publicar_csv(ruta,srv.url,'test_timeout',ruta_cursor=cursor,timeout=.5,reintentos=1)
        self.assertEqual(json.loads(cursor.read_text())['filas_enviadas'],1)
        self.assertEqual(len(srv.intentos),2)  # ACK perdido: entrega al menos una vez.

    def test_cursor_corrupto_cambio_de_prefijo_y_modo_no_ocultan_filas(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        ruta=self._crear_csv(filas=1)
        cursor=self.carpeta/'integridad.cursor.json'
        thingsboard.publicar_csv(ruta,srv.url,'test_integridad',ruta_cursor=cursor)
        with self.assertRaisesRegex(ValueError,'configuración'):
            thingsboard.publicar_csv(ruta,srv.url,'test_integridad',ruta_cursor=cursor,
                                    modo='en_vivo',seguir=True,duracion=.01)
        ruta.write_text(ruta.read_text().replace(',0,49,50,',',1,49,50,'))
        with self.assertRaisesRegex(ValueError,'cambiaron'):
            thingsboard.publicar_csv(ruta,srv.url,'test_integridad',ruta_cursor=cursor)
        cursor.write_text('{')
        with self.assertRaises(ValueError):
            thingsboard.publicar_csv(ruta,srv.url,'test_integridad',ruta_cursor=cursor)

    def test_no_permite_cursor_sobre_evidencia_y_no_hay_falso_exito_sin_datos(self):
        ruta=self._crear_csv(filas=0)
        original=ruta.read_bytes()
        with self.assertRaises(ValueError):
            thingsboard.publicar_csv(ruta,'http://127.0.0.1:1','test_cursor',ruta_cursor=ruta)
        with self.assertRaisesRegex(ValueError,'filas completas'):
            thingsboard.publicar_csv(ruta,'http://127.0.0.1:1','test_cursor',seguir=True,duracion=.01)
        self.assertEqual(ruta.read_bytes(),original)

    def test_publicacion_calibrada_exige_validacion_y_rango_tres_canales(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        ruta=self._crear_csv(filas=1)
        # Puntos SINTÉTICOS exclusivos de esta prueba.
        cal={'unidad':'cm','sensores':{f'adc{i}':[[0,0],[100,10]] for i in range(1,4)}}
        with self.assertRaisesRegex(ValueError,'validada'):
            thingsboard.publicar_csv(ruta,srv.url,'test_cal',calibracion=cal)
        cal['validada']=True
        thingsboard.publicar_csv(ruta,srv.url,'test_cal',calibracion=cal)
        valores=srv.recibidos[0][0]['values']
        self.assertEqual((valores['altura1'],valores['altura2'],valores['altura3']),(0,4.9,5))
        cal['sensores']['adc3']=[[0,0],[10,1]]
        with self.assertRaisesRegex(ValueError,'fuera'):
            thingsboard.publicar_csv(ruta,srv.url,'test_cal',calibracion=cal,
                                    ruta_cursor=self.carpeta/'rango.cursor.json')
        self.assertEqual(len(srv.recibidos),1)

    def test_reintento_reclasifica_lote_que_ya_no_es_reciente(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        srv.codigos_respuesta=[503,200]
        fecha=datetime(2026,1,1,tzinfo=timezone.utc)
        lote=[{'ts':1767225600000,'values':{'adc1':1,'modo_transmision':'en_vivo','es_tiempo_real':True}}]
        with patch('python.thingsboard.datetime') as reloj:
            reloj.now.side_effect=[fecha,fecha+timedelta(seconds=4)]
            thingsboard.publicar_lote(srv.url,'test_edad',lote,reintentos=2,espera_inicial_s=0)
        self.assertFalse(srv.recibidos[0][0]['values']['es_tiempo_real'])
        self.assertEqual(srv.recibidos[0][0]['ts'],1767225600000)

    def test_credenciales_servidor_y_qr_y_token_codificado_se_rechazan(self):
        for servidor in ('https://usuario:secreto@host.invalid','http://host.invalid',
                         'https://host.invalid/ruta'):
            with self.subTest(servidor=servidor), self.assertRaises(ValueError):
                thingsboard.url_endpoint(servidor,'test_seguridad')
        for token in ('tok%2Fprivado','tok@privado','tok:privado'):
            with self.subTest(token=token), self.assertRaises(ValueError):
                thingsboard.url_endpoint('https://host.invalid',token)
        for url in ('https://usuario:clave@host.invalid/dashboard/1',
                    'https://host.invalid/dashboard/1?access_token=privado',
                    'https://host.invalid/dashboard/1?device=%70rivado',
                    'http://127.0.0.2/dashboard/1'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                thingsboard.validar_url_dashboard(url,token='privado')

    def test_reintentos_y_reanudacion_con_cursor_sin_duplicar_lotes(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        csv_path = self._crear_csv(filas=4)
        cursor = self.carpeta / 'cursor.json'
        # Primer lote tiene un fallo 503 y luego pasa (200); segundo lote falla dos veces (503, 503).
        srv.codigos_respuesta = [503, 200, 503, 503]
        with self.assertRaises(ConnectionError):
            thingsboard.publicar_csv(
                csv_path, srv.url, 'secreto123', ruta_cursor=cursor,
                tamano_lote=2, reintentos=2, espera_inicial_s=0.005)
        self.assertEqual(len(srv.recibidos), 1)
        estado = json.loads(cursor.read_text(encoding='utf-8'))
        self.assertEqual(estado['filas_enviadas'], 2)
        self.assertNotIn('secreto123', cursor.read_text(encoding='utf-8'))

        # Al reintentar con el mismo cursor, solo envía las 2 filas faltantes.
        res = thingsboard.publicar_csv(
            csv_path, srv.url, 'secreto123', ruta_cursor=cursor,
            tamano_lote=2, reintentos=2, espera_inicial_s=0.005)
        self.assertEqual(res['filas_enviadas'], 4)
        self.assertEqual(res['lotes_enviados'], 1)
        self.assertEqual(len(srv.recibidos), 2)
        self.assertEqual(srv.recibidos[1][0]['values']['t_ms'], 1500)

    def test_error_autenticacion_no_filtra_token_y_rechaza_prueba_controlada(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        srv.codigos_respuesta = [401]
        csv_path = self._crear_csv(filas=1)
        with self.assertRaises(RuntimeError) as ctx:
            thingsboard.publicar_csv(
                csv_path, srv.url, 'TOKEN_ULTRA_SECRETO_XYZ',
                reintentos=3, espera_inicial_s=0.001)
        self.assertNotIn('TOKEN_ULTRA_SECRETO_XYZ', str(ctx.exception))
        self.assertIn('401', str(ctx.exception))

        ctrl_csv = self._crear_csv(nombre='ctrl.csv', filas=1, origen='prueba_controlada')
        with self.assertRaisesRegex(ValueError, 'prueba_controlada'):
            thingsboard.publicar_csv(ctrl_csv, srv.url, 'tok_valido')

    def test_captura_local_se_conserva_aunque_falle_internet(self):
        flujo = io.BytesIO(b'tiempo_ms,sensor1,sensor2,sensor3\r\n'
                           b'500,12,34,56\r\n1000,15,35,55\r\n')
        destino = self.carpeta / 'local_seguro.csv'
        res = thingsboard.capturar_y_publicar(
            flujo, destino, 'http://127.0.0.1:1', 'tok_offline',
            max_muestras=2, duracion=1.0, origen='prueba_controlada',
            timeout=0.05, reintentos=1, espera_inicial_s=0.001)
        self.assertEqual(res['muestras_locales'], 2)
        self.assertFalse(res['publicado'])
        self.assertIsNotNone(res['error_red'])
        self.assertNotIn('tok_offline', res['error_red'])
        with destino.open(encoding='utf-8') as f:
            filas = list(csv.DictReader(f))
        self.assertEqual(len(filas), 2)
        self.assertEqual(filas[0]['adc1'], '12')

    def test_validacion_url_dashboard_para_qr(self):
        url_ok = 'https://tb.universidad.edu.pa/dashboard/fe801230-aaaa-11ee'
        self.assertEqual(
            thingsboard.validar_url_dashboard(url_ok, token='tok_secreto_1'),
            url_ok)
        for invalida in (
            '',
            'CONTENIDO_CONFIRMADO',
            'https://SERVIDOR/dashboard/1',
            'http://localhost:8080/dashboard/1',
            'https://tb.universidad.edu.pa/api/v1/tok_secreto_1/telemetry',
            'https://tb.universidad.edu.pa/dashboard?device=tok_secreto_1',
            'ftp://tb.universidad.edu.pa/dashboard',
        ):
            with self.subTest(invalida=invalida):
                with self.assertRaises(ValueError):
                    thingsboard.validar_url_dashboard(invalida, token='tok_secreto_1')

    def test_cli_thingsboard_con_config_local_y_servidor_simulado(self):
        srv = _ServidorSimulado()
        self.addCleanup(srv.cerrar)
        csv_path = self._crear_csv(filas=2)
        cfg_path = self.carpeta / 'tb.local.json'
        cfg_path.write_text(json.dumps({
            'servidor': srv.url,
            'token': 'cli_token_777',
            'dashboard_url': 'https://tb.utp.ac.pa/dashboards/agua'
        }), encoding='utf-8')
        cursor_path = self.carpeta / 'cli_cursor.json'
        r = subprocess.run(
            [sys.executable, '-m', 'python.main', 'thingsboard',
             '--csv', str(csv_path), '--config', str(cfg_path),
             '--modo', 'historico', '--cursor', str(cursor_path)],
            cwd=RAIZ, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('cli_token_777', r.stdout)
        self.assertIn('/api/v1/***/telemetry', r.stdout)
        self.assertEqual(len(srv.recibidos), 1)
        self.assertEqual(len(srv.recibidos[0]), 2)

    @unittest.skipUnless(os.name=='posix','Requiere pseudoterminal POSIX')
    def test_flujo_serial_csv_http_lento_no_pierde_muestras(self):
        """Integración SINTÉTICA completa: no usa Arduino ni ThingsBoard reales."""
        import pty
        from python.comunicacion import capturar,verificar_cadencia
        master,slave=pty.openpty()
        parar=threading.Event()
        srv=_ServidorSimulado()
        self.addCleanup(srv.cerrar)
        srv.codigos_respuesta=[503,200,200]
        srv.retardos_respuesta=[.8]
        ruta=self.carpeta/'INTEGRACION_SINTETICA.csv'
        resultados=[]
        errores=[]
        def emitir():
            if parar.wait(.1): return
            os.write(master,b'parcial\n'+b'500,9,9,9\n'*20)
            if parar.wait(.3): return
            for i in range(10):
                os.write(master,f'{10000+i*500},1,2,3\n'.encode())
                if parar.wait(.5): return
        def publicar():
            try:
                resultados.append(thingsboard.publicar_csv(ruta,srv.url,'test_integracion',modo='en_vivo',
                    seguir=True,duracion=4.2,intervalo_s=.02,timeout=1.5,reintentos=1))
            except Exception as e: errores.append(e)
        emisor=threading.Thread(target=emitir)
        publicador=threading.Thread(target=publicar)
        try:
            emisor.start()
            publicador.start()
            self.assertEqual(capturar(os.ttyname(slave),ruta,max_muestras=3,duracion=5),(3,0))
            publicador.join(timeout=5)
            self.assertFalse(publicador.is_alive())
            self.assertEqual(errores,[])
            self.assertEqual(resultados[0]['filas_enviadas'],3)
            recibidos=[r for lote in srv.recibidos for r in lote]
            self.assertEqual([r['values']['t_ms'] for r in recibidos],[12000,12500,13000])
            self.assertTrue(all(r['values']['es_tiempo_real'] for r in recibidos))
            self.assertTrue(verificar_cadencia(ruta)['cadencia_compatible'])
        finally:
            parar.set()
            emisor.join(timeout=1)
            publicador.join(timeout=5)
            os.close(master)
            os.close(slave)


if __name__ == '__main__':
    unittest.main()
