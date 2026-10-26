"""Contrato de calidad por delta: resolución, ejecución y evidencia aisladas."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def cargar(nombre, archivo):
    """Carga un motor distribuible sin instalarlo ni modificar sys.path."""
    spec = importlib.util.spec_from_file_location(nombre, Path(__file__).with_name(archivo))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


calidad = cargar('calidad_pruebas', 'calidad.py')
motor = cargar('motor_calidad_pruebas', 'orquestar.py')


class CalidadTests(unittest.TestCase):
    """Fixtures locales sin herramientas externas ni servicios."""

    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.git('init', '-q')
        self.git('config', 'user.email', 'pruebas@example.invalid')
        self.git('config', 'user.name', 'Pruebas')
        self.escribir('uno.py', 'original\n')
        self.escribir('borrado.py', 'original\n')
        self.escribir('sin_cambios.py', 'original\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.base = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        """Ejecuta Git solo en el repositorio temporal de la prueba."""
        return subprocess.run(['git', *args], cwd=self.root, check=True,
                              capture_output=True, text=True).stdout

    def escribir(self, nombre, texto):
        """Crea un fichero de la fixture conservando su nombre literal."""
        ruta = self.root / nombre
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding='utf-8')

    def npm(self, scripts):
        """Declara scripts sin instalar paquetes."""
        self.escribir('package.json', json.dumps({'scripts': scripts}))

    def config(self, **validation):
        """Declara comandos con comillas YAML válidas."""
        self.escribir('task_config.yaml', 'validation:\n' + ''.join(
            f'  {clave}: {json.dumps(valor)}\n' for clave, valor in validation.items()))

    def test_delta_confirmados_preparados_pendientes_nuevos_y_eliminados(self):
        self.escribir('uno.py', 'confirmado\n')
        self.git('add', 'uno.py')
        self.git('commit', '-qm', 'tarea')
        self.escribir('dos.py', 'preparado\n')
        self.git('add', 'dos.py')
        self.escribir('dos.py', 'pendiente\n')
        self.escribir('tres.py', 'nuevo\n')
        self.escribir('.gitignore', 'ignorado.py\n')
        self.escribir('ignorado.py', 'ignorado\n')
        (self.root / 'borrado.py').unlink()
        sha, ficheros = calidad.delta(self.root, self.base)
        self.assertEqual(sha, self.base)
        self.assertEqual(ficheros, ['.gitignore', 'dos.py', 'tres.py', 'uno.py'])

    def test_base_inexistente_es_error_no_delta_vacio(self):
        with self.assertRaisesRegex(ValueError, 'base'):
            calidad.delta(self.root, 'no-existe')

    def test_marcador_preserva_argumentos_y_descarta_eliminado(self):
        nombres = ['src/con espacio.py', 'src/a;eco.py', 'src/á.py']
        for nombre in nombres:
            self.escribir(nombre, 'x')
        plan = calidad.resolver(self.root, {'lint': 'herramienta {ficheros}'}, nombres)
        self.assertEqual(plan['lint']['comando'], ['herramienta', *nombres])

    def test_explicito_prevalece_independientemente_por_etapa(self):
        self.npm({'format:check': 'prettier --check .', 'lint': 'eslint .'})
        plan = calidad.resolver(self.root, {'formato': 'mi-formato --check {ficheros}',
                                           'lint': 'mi-lint {ficheros}'}, ['src/a.js'])
        self.assertEqual(plan['formato']['comando'], ['mi-formato', '--check', 'src/a.js'])
        self.assertEqual(plan['lint']['comando'], ['mi-lint', 'src/a.js'])
        self.assertIsNone(plan['formato']['escritura'])

    def test_npm_reconocido_y_escritura_acotados(self):
        self.npm({'format:check': 'prettier --check .', 'lint': 'eslint .'})
        plan = calidad.resolver(self.root, {}, ['a.js', 'notas.md', 'a.py'])
        self.assertEqual(plan['formato']['comando'], ['prettier', '--check', 'a.js', 'notas.md'])
        self.assertEqual(plan['formato']['escritura'], ['prettier', '--write', 'a.js', 'notas.md'])
        self.assertEqual(plan['lint']['comando'], ['eslint', 'a.js'])

    def test_ruff_fallback_por_etapa_y_filtrado(self):
        self.npm({'format:check': 'prettier --check .', 'lint': 'node scripts/calidad.js'})
        self.escribir('pyproject.toml', '[tool.ruff]\nline-length = 88\n')
        plan = calidad.resolver(self.root, {}, ['a.py', 'b.pyi', 'notas.md'])
        self.assertEqual(plan['lint']['comando'], ['ruff', 'check', 'a.py', 'b.pyi'])
        self.assertEqual(plan['formato']['comando'], ['prettier', '--check', 'notas.md'])
        (self.root / 'package.json').unlink()
        plan = calidad.resolver(self.root, {}, ['a.py', 'b.pyi', 'notas.md'])
        self.assertEqual(plan['formato']['comando'], ['ruff', 'format', '--check', 'a.py', 'b.pyi'])
        self.assertEqual(plan['formato']['escritura'], ['ruff', 'format', 'a.py', 'b.pyi'])

    def test_sin_herramientas_y_scripts_desconocidos_se_omiten(self):
        for script in (None, 'node scripts/calidad.js', 'eslint . && echo ok', 'npx eslint .'):
            with self.subTest(script=script):
                if script:
                    self.npm({'lint': script})
                plan = calidad.resolver(self.root, {}, ['a.js'])
                for etapa in plan.values():
                    self.assertIsNone(etapa['comando'])
                    self.assertTrue(etapa['motivo'])

    def test_explicito_sin_marcador_conserva_texto_y_avisa(self):
        plan = calidad.resolver(self.root, {'lint': 'mi-lint --proyecto'}, ['uno.py'])
        self.assertEqual(plan['lint']['comando'], 'mi-lint --proyecto')
        self.assertIn('alcance', plan['lint']['aviso'])

    def test_config_invalida_falla_aunque_delta_vacio_o_haya_deduccion(self):
        self.npm({'lint': 'eslint .'})
        for clave in ('formato', 'lint', 'formato_escritura'):
            for valor in (123, '', '  ', None, [], False):
                with self.subTest(clave=clave, valor=valor):
                    with self.assertRaisesRegex(ValueError, 'validation.' + clave):
                        calidad.resolver(self.root, {clave: valor}, [])

    def test_sin_objetivos_omite_incluso_explicito_global(self):
        for cfg, ficheros in (({'lint': 'global'}, []), ({'lint': 'x {ficheros}'}, [])):
            plan = calidad.resolver(self.root, cfg, ficheros)
            self.assertIsNone(plan['lint']['comando'])
            self.assertIn('objetivos', plan['lint']['motivo'])
        self.escribir('pyproject.toml', '[tool.ruff]\n')
        plan = calidad.resolver(self.root, {}, ['notas.md'])
        self.assertIsNone(plan['formato']['comando'])
        self.assertIn('objetivos', plan['formato']['motivo'])

    def test_escritura_explicita_no_se_inventa(self):
        plan = calidad.resolver(self.root, {'formato': 'check {ficheros}',
                                           'formato_escritura': 'write {ficheros}'}, ['uno.py'])
        self.assertEqual(plan['formato']['escritura'], ['write', 'uno.py'])

    def herramienta(self, fallo='ninguno'):
        """Escribe un formateador/comprobador real y determinista en la fixture."""
        self.escribir('herramienta.py', '''import json
import pathlib
import sys
modo, fallo, *nombres = sys.argv[1:]
with pathlib.Path('.git/llamadas.jsonl').open('a', encoding='utf-8') as salida:
    salida.write(json.dumps([modo, nombres], ensure_ascii=False) + '\\n')
if modo == 'write':
    pathlib.Path('uno.py').write_text('corregido\\n', encoding='utf-8')
if modo == 'formato' and pathlib.Path('uno.py').read_text(encoding='utf-8') != 'corregido\\n':
    sys.exit(1)
sys.exit(1 if modo == fallo else 0)
''')
        prefijo = f'"{Path(sys.executable).as_posix()}" herramienta.py'
        self.config(formato=f'{prefijo} formato {fallo} {{ficheros}}',
                    formato_escritura=f'{prefijo} write {fallo} {{ficheros}}',
                    lint=f'{prefijo} lint {fallo} {{ficheros}}')

    def llamadas(self):
        """Lee la traza del ejecutable de prueba."""
        return [json.loads(l) for l in (self.root / '.git/llamadas.jsonl').read_text(encoding='utf-8').splitlines()]

    def test_aplica_escritura_antes_de_verificar_y_preserva_nombres_reales(self):
        self.herramienta()
        self.escribir('con espacio;eco.py', 'nuevo\n')
        self.assertEqual(calidad.ejecutar(self.root, self.base, True, motor.verificar), 0)
        llamadas = self.llamadas()
        self.assertEqual([l[0] for l in llamadas], ['write', 'formato', 'lint'])
        self.assertTrue(all('con espacio;eco.py' in l[1] for l in llamadas))
        self.assertEqual((self.root / 'uno.py').read_text(encoding='utf-8'), 'corregido\n')

    def test_hades_no_escribe_y_fallo_de_cada_etapa_es_rojo(self):
        for fallo in ('formato', 'lint'):
            with self.subTest(fallo=fallo):
                self.herramienta(fallo)
                self.escribir('uno.py', 'corregido\n')
                registro = self.root / '.git/llamadas.jsonl'
                registro.unlink(missing_ok=True)
                self.assertNotEqual(calidad.ejecutar(self.root, self.base, False, motor.verificar), 0)
                self.assertEqual([l[0] for l in self.llamadas()], ['formato', 'lint'])

    def test_evidencia_reutiliza_e_invalida_contenido_base_y_comando(self):
        self.git('commit', '--allow-empty', '-qm', 'otra base con el mismo árbol')
        nueva_base = self.git('rev-parse', 'HEAD').strip()
        self.herramienta()
        self.escribir('uno.py', 'corregido\n')
        self.assertEqual(calidad.ejecutar(self.root, self.base, False, motor.verificar), 0)
        self.assertEqual([l[0] for l in self.llamadas()], ['formato', 'lint'])
        self.assertEqual(calidad.ejecutar(self.root, self.base, False, motor.verificar), 0)
        self.assertEqual(len(self.llamadas()), 2, 'El mismo árbol no ejecuta ningún comprobador')
        arbol_antes = motor.arbol(self.root)
        self.assertEqual(calidad.ejecutar(self.root, nueva_base, False, motor.verificar), 0)
        self.assertEqual(motor.arbol(self.root), arbol_antes, 'Solo cambió la base, no el contenido')
        self.assertEqual(len(self.llamadas()), 4)
        self.escribir('sin_cambios.py', 'otro\n')
        self.assertEqual(calidad.ejecutar(self.root, self.base, False, motor.verificar), 0)
        self.assertEqual(len(self.llamadas()), 6, 'Cambiar contenido ejecuta ambas etapas')
        prefijo = f'"{Path(sys.executable).as_posix()}" herramienta.py'
        self.config(formato=f'{prefijo} formato ninguno {{ficheros}}',
                    lint=f'{prefijo} lint distinto {{ficheros}}')
        self.assertEqual(calidad.ejecutar(self.root, self.base, False, motor.verificar), 0)
        self.assertEqual(len(self.llamadas()), 8, 'Cambiar comando exige nueva ejecución')
        filas = [json.loads(l) for l in (self.root / motor.EVIDENCIAS).read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(filas), 8)
        self.assertEqual(filas[0]['arbol'], filas[2]['arbol'])
        self.assertNotEqual(filas[0]['comando'], filas[2]['comando'])

    def test_sin_escritura_conocida_solo_ejecuta_comprobadores(self):
        self.herramienta()
        prefijo = f'"{Path(sys.executable).as_posix()}" herramienta.py'
        self.config(formato=f'{prefijo} formato ninguno {{ficheros}}',
                    lint=f'{prefijo} lint ninguno {{ficheros}}')
        self.escribir('uno.py', 'corregido\n')
        self.assertEqual(calidad.ejecutar(self.root, self.base, True, motor.verificar), 0)
        self.assertEqual([l[0] for l in self.llamadas()], ['formato', 'lint'])

    def test_escritura_invalida_verde_anterior_sobre_arbol_resultante(self):
        self.herramienta()
        ruta = self.root / 'herramienta.py'
        texto = ruta.read_text(encoding='utf-8')
        texto = texto.replace("if modo == 'formato' and", "if False and")
        ruta.write_text(texto, encoding='utf-8')
        self.assertEqual(calidad.ejecutar(self.root, self.base, False, motor.verificar), 0)
        anterior = motor.arbol(self.root)
        self.assertEqual(calidad.ejecutar(self.root, self.base, True, motor.verificar), 0)
        self.assertNotEqual(motor.arbol(self.root), anterior)
        self.assertEqual([l[0] for l in self.llamadas()], ['formato', 'lint', 'write', 'formato', 'lint'])
        self.assertEqual(calidad.ejecutar(self.root, self.base, False, motor.verificar), 0)
        self.assertEqual(len(self.llamadas()), 5)

    def test_ejecutable_ausente_no_acredita_calidad(self):
        self.config(lint='herramienta-inexistente-adv-0022 {ficheros}')
        self.assertNotEqual(calidad.ejecutar(self.root, self.base, False, motor.verificar), 0)

    def test_regresion_hades_delta_largo(self):
        self.herramienta()
        self.escribir('uno.py', 'corregido\n')
        nombres = [f'src/{i:03d}_nombre_de_archivo_con_espacios y acentos_á.py' for i in range(100)]
        for nombre in nombres:
            self.escribir(nombre, 'nuevo\n')
        comandos = []

        def verificar(root, comando):
            """Exige una orden corta y la ejecuta mediante el verificador real."""
            comandos.append(comando)
            self.assertLess(len(comando), 8191)
            return motor.verificar(root, comando)

        self.assertEqual(calidad.ejecutar(self.root, self.base, False, verificar), 0)
        self.assertEqual([l[0] for l in self.llamadas()], ['formato', 'lint'])
        for _, argumentos in self.llamadas():
            self.assertTrue(set(nombres).issubset(argumentos))
        self.assertEqual(calidad.ejecutar(self.root, self.base, False, verificar), 0)
        self.assertEqual(len(self.llamadas()), 2)
        self.assertEqual(comandos[:2], comandos[2:])

    def test_regresion_hades_validation_vacio(self):
        self.escribir('task_config.yaml', 'validation:\n')
        self.assertEqual(calidad.ejecutar(self.root, self.base, False, motor.verificar), 0)
        self.escribir('pyproject.toml', '[tool.ruff]\n')
        plan = calidad.resolver(self.root, calidad._config(self.root), ['uno.py'])
        self.assertEqual(plan['formato']['comando'], ['ruff', 'format', '--check', 'uno.py'])
        self.assertEqual(plan['lint']['comando'], ['ruff', 'check', 'uno.py'])

    def test_cli_calidad_no_arranca_bucle_y_valida_base(self):
        with patch.object(sys, 'argv', ['adevv', '--calidad', '--base', self.base]), \
                patch.object(Path, 'cwd', return_value=self.root), \
                patch.object(motor, 'iniciar_gateway') as gateway:
            self.assertEqual(motor.main(), 0)
            gateway.assert_not_called()

    def test_instrucciones_de_ambos_flujos_y_hades_exigen_calidad(self):
        raiz = Path(__file__).resolve().parents[2]
        for flujo in ('task-dev', 'bug-fix'):
            texto = (raiz / 'skills' / flujo / 'SKILL.md').read_text(encoding='utf-8')
            with self.subTest(flujo=flujo):
                self.assertIn('--calidad --base', texto)
                self.assertIn('--aplicar', texto)
                self.assertIn('base_calidad', texto)
                self.assertIn('mediante el verificador', texto)
                cierre = texto.split('### Subfase F: Cierre [EXEC]')[1]
                self.assertLess(cierre.index('--calidad --base'), cierre.index('status: completed'))
                self.assertIn('Solo en verde', cierre)
                self.assertIn('cualquier fallo devuelve el estado a `in_progress`', cierre)
                self.assertIn('escritura', cierre)
                self.assertIn('--verificar', cierre)
        texto = (raiz / 'skills/review-code/SKILL.md').read_text(encoding='utf-8')
        self.assertIn('--calidad --base', texto)
        self.assertIn('sin escritura', texto)
        self.assertIn('desarrollador', texto)
        self.assertIn('destino `resolver`', texto)
        self.assertIn('sin aprobación hasta corregirlo', texto)
        self.assertIn('No uses `--aplicar`', texto)
        self.assertIn('ambas etapas mediante `--verificar`', texto)


if __name__ == '__main__':
    unittest.main()
