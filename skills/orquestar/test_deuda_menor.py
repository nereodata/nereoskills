"""Regresiones para las utilidades comunes de orquestación (T-ADV-0025)."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skills.orquestar import metricas, orquestar
from skills.telegram_gateway import gateway


class DeudaMenorTests(unittest.TestCase):
    """Comprueba contratos compartidos entre el bucle y Telegram."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_version_de_respaldo_lee_manifiesto_del_proyecto(self):
        script = self.root / 'skills/orquestar/orquestar.py'
        script.parent.mkdir(parents=True)
        script.touch()
        (self.root / 'pyproject.toml').write_text('[project]\nversion = "1.7.3"\n', encoding='utf-8')
        with patch.dict('sys.modules', {'adevv': None}):
            self.assertEqual(orquestar.version_adevv(script), '1.7.3')

    def test_version_sin_fuentes_es_explicita(self):
        script = self.root / 'orquestar.py'
        script.touch()
        with patch.dict('sys.modules', {'adevv': None}):
            self.assertEqual(orquestar.version_adevv(script), 'desconocida')

    def test_version_de_respaldo_lee_task_config_si_falta_pyproject(self):
        script = self.root / 'skills/orquestar/orquestar.py'
        script.parent.mkdir(parents=True)
        script.touch()
        (self.root / 'task_config.yaml').write_text(
            'project:\n  version: "v2.3.4"\n', encoding='utf-8')
        with patch.dict('sys.modules', {'adevv': None}):
            self.assertEqual(orquestar.version_adevv(script), '2.3.4')

    def test_version_usa_yaml_si_pyproject_no_se_puede_leer(self):
        script = self.root / 'skills/orquestar/orquestar.py'
        script.parent.mkdir(parents=True)
        script.touch()
        (self.root / 'pyproject.toml').write_text('[project\nversion = "1.0.0"', encoding='utf-8')
        (self.root / 'task_config.yaml').write_text(
            'project:\n  version: "v2.3.4"\n', encoding='utf-8')
        with patch.dict('sys.modules', {'adevv': None}):
            self.assertEqual(orquestar.version_adevv(script), '2.3.4')

    def test_resolver_de_version_unico_alimenta_firma_y_recarga(self):
        almacen = self.root / 'versions'
        script = almacen / '1.2.3/skills/orquestar/orquestar.py'
        destino = almacen / '1.2.4/skills/orquestar/orquestar.py'
        script.parent.mkdir(parents=True)
        destino.parent.mkdir(parents=True)
        script.touch()
        destino.touch()
        (self.root / 'active.json').write_text('{"version":"1.2.4"}', encoding='utf-8')
        with patch.dict(os.environ, {'ADEVV_HOME': str(self.root)}):
            esperado = (self.root.resolve(), script.parents[2].resolve(), '1.2.3')
            self.assertEqual(orquestar.directorio_version_almacen(script), esperado)
            with patch.object(orquestar, 'directorio_version_almacen',
                              wraps=orquestar.directorio_version_almacen) as resolver:
                self.assertEqual(orquestar.version_adevv(script), '1.2.3')
                self.assertEqual(orquestar.version_activa_distinta(script), (destino.resolve(), '1.2.4'))
                self.assertEqual(resolver.call_count, 2)

    def test_pid_vivo_y_propiedad_son_comunes_a_bucle_y_gateway(self):
        for nombre in (orquestar.PID, gateway.PID):
            with self.subTest(nombre=nombre):
                archivo = self.root / nombre
                self.assertIsNone(orquestar.pid_vivo(self.root, nombre))
                self.assertIsNone(gateway.pid_vivo(self.root, nombre))
                archivo.write_text('no-es-un-pid', encoding='utf-8')
                self.assertIsNone(orquestar.pid_vivo(self.root, nombre))
                self.assertIsNone(gateway.pid_vivo(self.root, nombre))
                self.assertFalse(orquestar.es_propietario_pid(self.root, nombre))
                self.assertFalse(gateway.es_propietario_pid(self.root, nombre))

                pid_ajeno = os.getpid() + 1
                archivo.write_text(str(pid_ajeno), encoding='utf-8')
                with patch.object(orquestar, '_proceso_vivo', return_value=False), \
                     patch.object(gateway.motor, '_proceso_vivo', return_value=False):
                    self.assertIsNone(orquestar.pid_vivo(self.root, nombre))
                    self.assertIsNone(gateway.pid_vivo(self.root, nombre))
                with patch.object(orquestar, '_proceso_vivo', return_value=True) as comprobar, \
                     patch.object(gateway.motor, '_proceso_vivo', return_value=True) as comprobar_gateway:
                    self.assertEqual(orquestar.pid_vivo(self.root, nombre), pid_ajeno)
                    self.assertEqual(gateway.pid_vivo(self.root, nombre), pid_ajeno)
                    comprobar.assert_called_once_with(pid_ajeno)
                    comprobar_gateway.assert_called_once_with(pid_ajeno)
                self.assertFalse(orquestar.es_propietario_pid(self.root, nombre))
                self.assertFalse(gateway.es_propietario_pid(self.root, nombre))

                archivo.write_text(str(os.getpid()), encoding='utf-8')
                with patch.object(gateway.motor, 'es_propietario_pid',
                                  wraps=gateway.motor.es_propietario_pid) as propietario:
                    self.assertTrue(gateway.es_propietario_pid(self.root, nombre))
                    propietario.assert_called_once_with(self.root, nombre)
                self.assertTrue(orquestar.es_propietario_pid(self.root, nombre))
                with patch.object(gateway.motor, 'pid_vivo',
                                  wraps=gateway.motor.pid_vivo) as comprobar:
                    self.assertEqual(gateway.pid_vivo(self.root, nombre), os.getpid())
                    comprobar.assert_called_once_with(self.root, nombre)

    def test_version_numerica_y_lectura_jsonl_tienen_implementacion_comun(self):
        self.assertEqual(orquestar.vkey('v1.20.4'), (1, 20))
        self.assertIs(orquestar.vkey, metricas.clave_version_numerica)
        archivo = self.root / orquestar.METRICAS
        archivo.write_text('{"comando":"uno\u2028dos"}\n', encoding='utf-8')
        self.assertEqual(orquestar.leer_metricas(self.root), [{'comando': 'uno\u2028dos'}])
        self.assertEqual(metricas.leer_registros(self.root), [{'comando': 'uno\u2028dos'}])
        self.assertEqual(len(metricas.consultar(self.root, [], 'todas')), 1)
        archivo.write_text('{"tipo":"paso"}\n{"incompleto":', encoding='utf-8')
        with patch.object(metricas, 'leer_registros', wraps=metricas.leer_registros) as leer:
            self.assertEqual(orquestar.leer_metricas(self.root), [{'tipo': 'paso'}])
            leer.assert_called_once_with(self.root, tolerar_ultima=True)
            with self.assertRaisesRegex(ValueError, 'línea 2'):
                metricas.consultar(self.root, [], 'todas')
            leer.assert_called_with(self.root, tolerar_ultima=False)

    def test_detalle_estado_heredado_se_elimina(self):
        self.assertFalse(hasattr(orquestar, 'detalle_estado'))


if __name__ == '__main__':
    unittest.main()
