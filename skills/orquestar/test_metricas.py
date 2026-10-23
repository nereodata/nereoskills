"""Contrato de consulta de métricas: fixtures locales y CLI real sin bucle."""
import csv
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name('orquestar.py').resolve()
CAMPOS = ('id version tipo dificultad tiempo_estimado_min tiempo_real_min modelos_dev '
          'dev_tokens_originales dev_tokens_cache dev_tokens_salida dev_tokens_razonamiento '
          'modelos_hades hades_llamadas hades_rechazos hades_tokens_originales '
          'hades_tokens_cache hades_tokens_salida verificaciones_totales '
          'verificaciones_reutilizadas coste_estimado_usd').split()


class MetricasTests(unittest.TestCase):
    """Valida filtros, atribución, consumo y formatos del contrato CA-M-1..4."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'orquestar.pid').write_text('12345', encoding='utf-8')
        self.item('T-ADV-0001', 'v0.2.0', 'sencilla')
        self.item('B-ADV-0001', 'v0.3.0', 'dificil', bug=True)
        self.item('T-ADV-0002', 'v0.10.0', 'media')
        self.registros = [
            dict(tipo='paso', id='T-ADV-0001', rama='release/v0.2', duracion_s=120,
                 modelos={'claude-sonnet-4': dict(entrada=1000000, cache_leida=2000000,
                                                salida=100000, razonamiento=10)}),
            dict(tipo='paso', id='T-ADV-0001', duracion_s=60, coste_usd=2,
                 modelos={'gpt-codex': dict(entrada=100, salida=20)}),
            dict(tipo='agente', rol='hades', id='T-ADV-0001', duracion_s=60,
                 veredicto='RECHAZADO', modelos={'gemini-4-argon-medium':
                    dict(entrada=1000000, cache_leida=1000000, salida=100000)}),
            dict(tipo='agente', rol='hades', id='T-ADV-0001', veredicto='APROBADO',
                 coste_usd=1, modelos={'claude-opus': dict(entrada=20)}),
            dict(tipo='verificacion', id='T-ADV-0001', reutilizada=False),
            dict(tipo='verificacion', id='T-ADV-0001', reutilizada=True),
            dict(tipo='espera', id='T-ADV-0001', duracion_s=900),
            dict(tipo='paso', id='v0.3', paso='revisar-version', duracion_s=30),
        ]
        self.guardar()

    def item(self, iid, version, dificultad=None, bug=False):
        carpeta = self.root / 'docs/plan' / ('bugs' if bug else 'tasks')
        carpeta.mkdir(parents=True, exist_ok=True)
        texto = f'---\nid: {iid}\nversion: "{version}"\nstatus: planned\n'
        if dificultad:
            texto += f'dificultad: {dificultad}\n'
        (carpeta / f'{iid}.md').write_text(texto + '---\n', encoding='utf-8')

    def guardar(self):
        (self.root / 'orquestar_metricas.jsonl').write_text(
            ''.join(json.dumps(r) + '\n' for r in self.registros), encoding='utf-8')

    def cli(self, *args, ok=True):
        resultado = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.root,
                                   env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},
                                   capture_output=True, text=True, encoding='utf-8')
        if ok:
            self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertEqual((self.root / 'orquestar.pid').read_text(), '12345')
        self.assertFalse((self.root / 'orquestar_evidencias.jsonl').exists())
        return resultado

    def filas(self, *args):
        return list(csv.DictReader(io.StringIO(self.cli('--metricas', *args, '--csv').stdout)))

    def test_agregacion_separa_dev_hades_y_no_duplica_duraciones(self):
        fila = next(f for f in self.filas() if f['id'] == 'T-ADV-0001')
        esperados = dict(version='v0.2', tipo='funcional', dificultad='sencilla',
                         tiempo_estimado_min=7, tiempo_real_min=3, dev_tokens_originales=1000100,
                         dev_tokens_cache=2000000, dev_tokens_salida=100020,
                         dev_tokens_razonamiento=10, hades_llamadas=2, hades_rechazos=1,
                         hades_tokens_originales=1000020, hades_tokens_cache=1000000,
                         hades_tokens_salida=100000, verificaciones_totales=2,
                         verificaciones_reutilizadas=1, coste_estimado_usd=11.5)
        for campo, valor in esperados.items():
            with self.subTest(campo=campo):
                if isinstance(valor, (int, float)):
                    self.assertAlmostEqual(float(fila[campo]), valor)
                else:
                    self.assertEqual(fila[campo], valor)
        self.assertEqual(fila['modelos_dev'], 'claude-sonnet-4;gpt-codex')
        self.assertEqual(fila['modelos_hades'], 'claude-opus;gemini-4-argon-medium')
        self.assertEqual(list(fila), CAMPOS)

    def test_filtros_alias_y_orden_numerico(self):
        for filtro in ('ultima', 'last'):
            self.assertEqual({f['version'] for f in self.filas(filtro)}, {'v0.10'})
        for filtro in ('ultimas:2', 'last:2'):
            self.assertEqual({f['version'] for f in self.filas(filtro)}, {'v0.3', 'v0.10'})
        self.assertEqual(self.filas('all'), self.filas('todas'))
        self.assertEqual(self.filas('v0.2,v0.3'), self.filas('v0.2.0,v0.3.0'))
        salida = self.cli('--metrics', '--version-filtro', 'v0.2', '--csv', '-').stdout
        self.assertEqual(len(list(csv.DictReader(io.StringIO(salida)))), 1)

    def test_filtros_invalidos_no_escriben_csv(self):
        for filtro in ('ultimas:0', 'last:-1', 'ultimas:no', 'vXYZ', 'v0.2,,v0.3'):
            with self.subTest(filtro=filtro):
                resultado = self.cli('--metricas', filtro, '--csv', 'invalido.csv', ok=False)
                self.assertNotEqual(resultado.returncode, 0)
                self.assertTrue(resultado.stderr.strip())
                self.assertFalse((self.root / 'invalido.csv').exists())

    def test_bug_version_y_defaults_del_backlog(self):
        filas = self.filas()
        bug = next(f for f in filas if f['id'] == 'B-ADV-0001')
        self.assertEqual(bug['tipo'], 'bug')
        self.assertEqual(float(bug['tiempo_estimado_min']), 25)
        version = next(f for f in filas if f['tipo'] == 'version')
        self.assertEqual(version['version'], 'v0.3')
        self.assertEqual(float(version['tiempo_real_min']), 0.5)
        self.item('T-ADV-0003', 'v0.3')
        fila = next(f for f in self.filas() if f['id'] == 'T-ADV-0003')
        self.assertEqual(fila['dificultad'], 'media')
        self.assertEqual(float(fila['tiempo_estimado_min']), 12)

    def test_versiones_solo_metricas_y_registros_huerfanos(self):
        self.registros = [dict(tipo='paso', id='T-BORRADO-1', rama='release/v0.11',
                               duracion_s=60), dict(tipo='verificacion', reutilizada=True),
                          dict(tipo='paso', paso='release', version='v0.12.0', duracion_s=12)]
        self.guardar()
        self.assertEqual({f['version'] for f in self.filas('last')}, {'v0.12'})
        filas = self.filas('all')
        self.assertTrue(any(f['id'] == 'T-BORRADO-1' and f['version'] == 'v0.11' for f in filas))
        huerfana = next(f for f in filas if f['version'] == 'sin-version')
        self.assertEqual(int(huerfana['verificaciones_reutilizadas']), 1)

    def test_tarifas_por_familia_coste_reportado_y_modelos_nulos(self):
        tarifas = {'claude-opus-4': 30.5, 'claude-sonnet': 18.3, 'claude-haiku': 6.1,
                   'gemini-4-argon': 14.2, 'gemini-pro': 14.2,
                   'gemini-3.8-flash': 3.55, 'gemini-flash': 3.55,
                   'gpt-6': 12.75, 'codex': 12.75, 'desconocido': 12.75}
        for modelo, esperado in tarifas.items():
            with self.subTest(modelo=modelo):
                self.registros = [dict(tipo='paso', id='T-ADV-0001', coste_usd=0,
                    modelos={modelo: dict(entrada=1000000, cache_leida=1000000,
                                          salida=1000000, razonamiento=999)})]
                self.guardar()
                self.assertAlmostEqual(float(self.filas('v0.2')[0]['coste_estimado_usd']), esperado)
        self.registros = [dict(tipo='paso', id='T-ADV-0001', coste_usd=4,
                               modelos={'gpt': dict(entrada=1000000, coste_usd=9)}),
                          dict(tipo='paso', id='T-ADV-0001', modelos=None),
                          dict(tipo='paso', id='T-ADV-0001', modelos={'gpt':
                               dict(entrada=None, salida=None, coste_usd=2)})]
        self.guardar()
        self.assertEqual(float(self.filas('v0.2')[0]['coste_estimado_usd']), 6)

    def test_csv_fichero_utf8_y_quoting(self):
        self.registros.append(dict(tipo='paso', id='T-ADV-0001', modelos={'modelo,á': dict(entrada=1)}))
        self.guardar()
        resultado = self.cli('--metricas', '--csv', 'export.csv')
        self.assertEqual(resultado.stdout, '')
        with (self.root / 'export.csv').open(encoding='utf-8', newline='') as archivo:
            filas = list(csv.DictReader(archivo))
        self.assertIn('modelo,á', next(f['modelos_dev'] for f in filas if f['id'] == 'T-ADV-0001'))
        self.assertEqual(filas, self.filas())

    def test_tabla_totales_por_version(self):
        salida = self.cli('--metricas', 'v0.2').stdout
        for texto in ('T-ADV-0001', 'v0.2', 'TOTAL', '11.500000', '3.00'):
            self.assertIn(texto, salida)
        self.assertNotIn('B-ADV-0001', salida)

    def test_sin_datos_cabecera_y_sin_metricas_version_ultima(self):
        self.registros = []
        self.guardar()
        self.assertEqual({f['version'] for f in self.filas('last')}, {'v0.10'})
        for carpeta in (self.root / 'docs/plan').iterdir():
            for archivo in carpeta.glob('*.md'):
                archivo.unlink()
        (self.root / 'orquestar_metricas.jsonl').unlink()
        self.assertEqual(self.filas(), [])
        self.assertEqual(self.filas('last'), [])
        self.assertIn('Sin métricas', self.cli('--metricas').stdout)

    def test_jsonl_corrupto_no_ofrece_resultados_parciales(self):
        with (self.root / 'orquestar_metricas.jsonl').open('a', encoding='utf-8') as archivo:
            archivo.write('no-json\n')
        resultado = self.cli('--metricas', '--csv', ok=False)
        self.assertNotEqual(resultado.returncode, 0)
        self.assertEqual(resultado.stdout, '')
        self.assertIn('línea 9', resultado.stderr)


if __name__ == '__main__':
    unittest.main()
