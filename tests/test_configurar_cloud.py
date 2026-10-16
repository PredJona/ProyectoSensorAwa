"""Credenciales SINTÉTICAS en temporales; nunca se usa una cuenta Cloud real."""
import io
import json
import stat
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from python import configurar_cloud as c


class ConfigurarCloudTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ruta=Path(self.tmp.name)/'privado'/'thingsboard.json'
        self.secreto='SINTETICO_no_es_credencial_real_987'

    def ejecutar(self,tty=True):
        salida=io.StringIO()
        with patch('sys.stdin.isatty',return_value=tty), \
             patch('getpass.getpass',return_value=self.secreto) as entrada, \
             redirect_stdout(salida),redirect_stderr(salida):
            codigo=c.main(['--config',str(self.ruta)])
        self.assertNotIn(self.secreto,salida.getvalue())
        return codigo,entrada,salida.getvalue()

    def test_guarda_en_archivo_protegido_sin_filtrar_secreto(self):
        codigo,entrada,_=self.ejecutar()
        self.assertEqual(codigo,0)
        entrada.assert_called_once()
        datos=json.loads(self.ruta.read_text())
        self.assertEqual(datos['token'],self.secreto)
        self.assertEqual(datos['servidor'],'https://thingsboard.cloud')
        self.assertEqual(stat.S_IMODE(self.ruta.stat().st_mode),0o600)
        self.assertEqual(stat.S_IMODE(self.ruta.parent.stat().st_mode),0o700)

    def test_no_usa_entrada_sin_terminal(self):
        codigo,entrada,_=self.ejecutar(tty=False)
        self.assertEqual(codigo,2)
        entrada.assert_not_called()
        self.assertFalse(self.ruta.exists())

    def test_no_reemplaza_token_ya_configurado(self):
        self.ruta.parent.mkdir()
        anterior=json.dumps({'servidor':'https://thingsboard.cloud','token':self.secreto,'dashboard_url':''})
        self.ruta.write_text(anterior)
        codigo,entrada,_=self.ejecutar()
        self.assertEqual(codigo,0)
        entrada.assert_not_called()
        self.assertEqual(self.ruta.read_text(),anterior)

    def test_reemplazo_explicito_es_privado_y_conserva_dashboard(self):
        self.ruta.parent.mkdir()
        self.ruta.write_text(json.dumps({'servidor':'https://thingsboard.cloud',
            'token':self.secreto,'dashboard_url':'https://thingsboard.cloud/dashboard/SINTETICO',
            'dashboard':'Proyecto Sensor de Agua'}))
        nuevo='SINTETICO_token_rotado_654'
        salida=io.StringIO()
        with patch('sys.stdin.isatty',return_value=True), \
             patch('getpass.getpass',return_value=nuevo) as entrada, \
             redirect_stdout(salida),redirect_stderr(salida):
            codigo=c.main(['--config',str(self.ruta),'--reemplazar-token'])
        self.assertEqual(codigo,0)
        entrada.assert_called_once()
        datos=json.loads(self.ruta.read_text())
        self.assertEqual(datos['token'],nuevo)
        self.assertEqual(datos['dashboard'],'Proyecto Sensor de Agua')
        self.assertEqual(datos['dashboard_url'],'https://thingsboard.cloud/dashboard/SINTETICO')
        self.assertEqual(stat.S_IMODE(self.ruta.stat().st_mode),0o600)
        self.assertNotIn(self.secreto,salida.getvalue())
        self.assertNotIn(nuevo,salida.getvalue())

    def test_rechaza_destino_dentro_del_repo_antes_de_pedir_token(self):
        self.ruta=Path(c.RAIZ)/'config'/'NO_CREAR.local.json'
        codigo,entrada,_=self.ejecutar()
        self.assertEqual(codigo,2)
        entrada.assert_not_called()
        self.assertFalse(self.ruta.exists())

    def test_no_sigue_enlaces_ni_modifica_destino(self):
        self.ruta.parent.mkdir()
        destino=self.ruta.parent/'original.json'
        destino.write_text('contenido que debe conservarse')
        self.ruta.symlink_to(destino)
        codigo,entrada,_=self.ejecutar()
        self.assertEqual(codigo,2)
        entrada.assert_not_called()
        self.assertEqual(destino.read_text(),'contenido que debe conservarse')

    def test_conserva_dashboard_y_metadatos_al_agregar_token(self):
        self.ruta.parent.mkdir()
        self.ruta.write_text(json.dumps({'servidor':'https://thingsboard.cloud','token':'',
            'dashboard_url':'https://thingsboard.cloud/dashboard/SINTETICO',
            'dashboard':'Proyecto Sensor de Agua'}))
        self.assertEqual(self.ejecutar()[0],0)
        datos=json.loads(self.ruta.read_text())
        self.assertEqual(datos['dashboard'],'Proyecto Sensor de Agua')
        self.assertEqual(datos['dashboard_url'],'https://thingsboard.cloud/dashboard/SINTETICO')

    def test_warning_getpass_no_provoca_entrada_con_eco(self):
        import getpass,warnings
        salida=io.StringIO()
        def fallo_eco(*args):
            warnings.warn('SINTETICO: sin control de eco',getpass.GetPassWarning)
        with patch('sys.stdin.isatty',return_value=True), \
             patch('getpass.getpass',side_effect=fallo_eco), \
             redirect_stderr(salida),redirect_stdout(salida):
            self.assertEqual(c.main(['--config',str(self.ruta)]),2)
        self.assertFalse(self.ruta.exists())


if __name__=='__main__': unittest.main()
