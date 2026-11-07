"""Pruebas BDD y de concurrencia para chequeos compartidos de calidad y release (T-ADV-0032)."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from adevv import release_tools
from tests import aislamiento_telegram


def _cargar(nombre, ruta):
    """Carga un módulo desde su ruta de archivo."""
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


BASE_DIR = Path(__file__).resolve().parent
chequeos = _cargar('chequeos_test', BASE_DIR / 'chequeos.py')
motor = _cargar('orquestar_test', BASE_DIR / 'orquestar.py')
gateway = _cargar('gateway_test', BASE_DIR.parent / 'telegram_gateway' / 'gateway.py')
cierre_version = _cargar('cierre_version_test', BASE_DIR.parent / 'telegram_gateway' / 'cierre_version.py')


class ChequeosCompartidosTests(unittest.TestCase):
    """Verifica los escenarios @T-ADV-0032 (CA-M-1 a CA-M-10) en repositorios Git aislados."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        self.root.mkdir(parents=True, exist_ok=True)
        self.env_patch = patch.dict(
            os.environ,
            {'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull},
        )
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        self.escribir('src/app.py', 'def suma(a, b):\n    return a + b\n')
        self.escribir('src/ui.js', 'export const x = 1;\n')
        self.escribir('tests/test_app.py', 'def test_ok():\n    assert True\n')
        self.escribir('pyproject.toml', '[project]\nname = "demo"\nversion = "1.0.0"\n')
        self.escribir('requirements.lock', 'pytest==8.0.0\n')
        self.escribir('task_config.yaml', 'project:\n  name: Demo\n  prefix: DEM\n  version: "v1.0.0"\n')
        self.commit('commit inicial')
        self.oldcwd = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.oldcwd)

    def git(self, *args, cwd=None):
        """Ejecuta Git en el repositorio temporal indicado."""
        return subprocess.run(
            ['git', *args],
            cwd=cwd or self.root,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
        ).stdout.strip()

    def escribir(self, rel_path, contenido, root=None):
        """Escribe un archivo UTF-8 en la ruta relativa indicada."""
        destino = (root or self.root) / rel_path
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(contenido, encoding='utf-8')
        return destino

    def commit(self, mensaje='cambio'):
        """Añade y confirma todos los cambios del repositorio temporal."""
        self.git('add', '.')
        self.git('commit', '-qm', mensaje)
        return self.git('rev-parse', 'HEAD')

    # ------------------------------------------------------------------
    # CA-M-1 y CA-M-2: Registro honesto, deducción con origen y plan explicable
    # ------------------------------------------------------------------
    def test_ca_m_1_y_2_registro_catalogo_plan_explicable_y_puerta_sin_cobertura_ficticia(self):
        """Escenario: Registrar comprobaciones de calidad y release mostrando el plan explicable sin cobertura ficticia."""
        self.escribir(
            'task_config.yaml',
            'project:\n  name: Demo\n  prefix: DEM\n  version: "v1.0.0"\n'
            'validation:\n'
            '  formato: "ruff format --check {ficheros}"\n'
            '  pruebas:\n'
            '    comando: "python -m unittest"\n'
            '    obligatorio: true\n'
            '  seguridad:\n'
            '    obligatorio: true\n'
            '  tipado:\n'
            '    obligatorio: false\n'
            'release:\n'
            '  puertas:\n'
            '    - formato\n'
            '    - lint\n'
            '    - pruebas\n'
            '    - seguridad\n',
        )
        self.escribir('package.json', json.dumps({'scripts': {'lint': 'eslint .'}}))
        self.commit('configurar chequeos')

        evaluacion = chequeos.evaluar_puerta(self.root, puerta='release', ejecutar=False)
        plan = evaluacion['plan']
        etapas = plan['etapas']

        self.assertIn('formato', plan['texto'])
        self.assertIn('ruff format --check', plan['texto'])
        self.assertIn('task_config.yaml (validation.formato)', plan['texto'])
        self.assertIn('deducido de package.json (scripts.lint)', plan['texto'])

        self.assertEqual(etapas['formato']['disponibilidad'], 'configurado')
        self.assertEqual(etapas['formato']['origen'], 'task_config.yaml (validation.formato)')

        self.assertEqual(etapas['lint']['disponibilidad'], 'configurado')
        self.assertEqual(etapas['lint']['origen'], 'deducido de package.json (scripts.lint)')
        self.assertIn('src/ui.js', ' '.join(etapas['lint']['comando']) if isinstance(etapas['lint']['comando'], list) else str(etapas['lint']['comando']))

        self.assertEqual(etapas['tipado']['disponibilidad'], 'ausente')
        self.assertEqual(etapas['tipado']['resultado'], 'sin_acreditar')
        self.assertEqual(etapas['tipado']['motivo'], 'análisis opcional no configurado')

        self.assertEqual(etapas['seguridad']['disponibilidad'], 'ausente')
        self.assertEqual(etapas['seguridad']['resultado'], 'sin_acreditar')
        self.assertEqual(etapas['seguridad']['motivo'], 'análisis obligatorio ausente')

        for ausente in ('secretos', 'dependencias', 'builds'):
            self.assertEqual(etapas[ausente]['disponibilidad'], 'ausente')
            self.assertEqual(etapas[ausente]['resultado'], 'sin_acreditar')
            self.assertIsNone(etapas[ausente]['comando'])

        self.assertEqual(evaluacion['estado'], 'fallido')
        self.assertIn('seguridad', evaluacion.get('motivo', ''))

    def test_ca_m_1_rechaza_configuraciones_invalidas_sin_ocultarlas_como_omision(self):
        """Esquema del escenario: Rechazar configuraciones inválidas de comprobaciones y puertas."""
        casos = [
            ('validation.tipado', 'validation:\n  tipado: 404\n'),
            ('validation.seguridad.comando', 'validation:\n  seguridad:\n    comando: ""\n'),
            ('release.puertas', 'release:\n  puertas: "no-es-lista"\n'),
            ('release.restricciones.publicar', 'release:\n  restricciones:\n    publicar: "rol-invalido-999"\n'),
        ]
        for ubicacion, yaml_invalido in casos:
            with self.subTest(ubicacion=ubicacion):
                self.escribir('task_config.yaml', 'project:\n  name: Demo\n' + yaml_invalido)
                ejecutados = []
                with self.assertRaises(ValueError) as ctx:
                    chequeos.evaluar_puerta(
                        self.root,
                        puerta='release',
                        ejecutar=True,
                        ejecutor=lambda cmd, **kw: ejecutados.append(cmd) or (0, 'ok'),
                    )
                self.assertIn(ubicacion, str(ctx.exception))
                self.assertEqual(ejecutados, [])

    # ------------------------------------------------------------------
    # CA-M-2 y CA-M-3: Evidencia aplicable, entradas relevantes y cambio en vuelo
    # ------------------------------------------------------------------
    def test_ca_m_2_y_3_reutiliza_evidencia_entre_entradas_aunque_cambie_commit_ajeno(self):
        """Escenario: Reutilizar evidencia aprobada entre entradas cuando coinciden las entradas relevantes aunque cambie el commit."""
        self.escribir(
            'task_config.yaml',
            'project:\n  name: Demo\n  version: "v1.0.0"\n'
            'validation:\n'
            '  pruebas:\n'
            '    comando: "python -m unittest"\n'
            '    entradas:\n'
            '      - src/\n'
            '      - tests/\n'
            '      - pyproject.toml\n',
        )
        self.commit('configurar entradas relevantes')

        invocaciones = []

        def ejecutor_controlado(cmd, **kwargs):
            invocaciones.append(cmd)
            return 0, '1 test OK\n'

        entorno_fijo = {
            'herramienta': 'python-3.12.10',
            'configuracion': 'cfg-v1',
            'dependencias': 'deps-v1',
            'plataforma': 'win32-py3.12',
        }

        res_cli = chequeos.ejecutar_comprobacion(
            self.root,
            'pruebas',
            ejecutor=ejecutor_controlado,
            entorno_override=entorno_fijo,
            canal='cli',
        )
        self.assertEqual(res_cli['codigo'], 0)
        self.assertEqual(res_cli['estado'], 'aprobado')
        self.assertEqual(len(invocaciones), 1)

        sha_anterior = self.git('rev-parse', 'HEAD')
        self.escribir('docs/notas.md', 'Documentación actualizada fuera de src y tests\n')
        sha_nuevo = self.commit('docs: actualizar notas')
        self.assertNotEqual(sha_anterior, sha_nuevo)

        for canal in ('gateway', 'agente', 'release'):
            plan = chequeos.planificar(self.root, etapas=['pruebas'], entorno_override=entorno_fijo)
            self.assertEqual(plan['etapas']['pruebas']['accion'], 'reutilizar')
            self.assertIn('identidad', plan['etapas']['pruebas']['motivo'])
            res = chequeos.ejecutar_comprobacion(
                self.root,
                'pruebas',
                ejecutor=ejecutor_controlado,
                entorno_override=entorno_fijo,
                canal=canal,
            )
            self.assertEqual(res['codigo'], 0)
            self.assertTrue(res['reutilizada'])
            self.assertEqual(len(invocaciones), 1)

    def test_ca_m_2_y_3_invalida_evidencia_por_contenido_entorno_o_entrada_no_acreditable(self):
        """Esquema del escenario: Invalidar la evidencia cuando cambia el contenido, el entorno relevante o una entrada no acreditable."""
        self.escribir(
            'task_config.yaml',
            'project:\n  name: Demo\n  version: "v1.0.0"\n'
            'validation:\n'
            '  pruebas:\n'
            '    comando: "python -m unittest"\n'
            '    entradas:\n'
            '      - src/\n'
            '      - tests/\n',
        )
        self.commit('base pruebas')

        entorno_base = {
            'herramienta': 'python-3.12.10',
            'plataforma': 'win32-py3.12',
        }
        res_inicial = chequeos.ejecutar_comprobacion(
            self.root,
            'pruebas',
            ejecutor=lambda cmd, **kw: (0, 'OK\n'),
            entorno_override=entorno_base,
        )
        self.assertEqual(res_inicial['codigo'], 0)
        base_head = self.git('rev-parse', 'HEAD')

        ejemplos = [
            ('pendiente_rastreado', 'cambio en contenido relevante'),
            ('nuevo_sin_rastrear', 'cambio en contenido relevante'),
            ('herramienta', 'cambio en entorno (herramienta)'),
            ('configuracion', 'cambio en entorno (configuración)'),
            ('dependencias', 'cambio en entorno (dependencias)'),
            ('plataforma', 'cambio en entorno (plataforma)'),
            ('entrada_no_acreditable', 'entrada relevante no acreditable'),
        ]

        for factor, motivo_esperado in ejemplos:
            with self.subTest(factor=factor):
                self.git('reset', '--hard', base_head)
                self.git('clean', '-fd')
                override = dict(entorno_base)
                if factor == 'pendiente_rastreado':
                    self.escribir('src/app.py', 'def suma(a, b):\n    return a + b + 1\n')
                elif factor == 'nuevo_sin_rastrear':
                    self.escribir('src/nuevo.py', 'x = 42\n')
                elif factor == 'herramienta':
                    override['herramienta'] = 'python-3.13.0'
                elif factor == 'configuracion':
                    self.escribir('pyproject.toml', '[project]\nname = "demo"\nversion = "1.0.0"\n[tool.pytest]\naddopts = "-q"\n')
                elif factor == 'dependencias':
                    self.escribir('requirements.lock', 'pytest==8.1.0\n')
                elif factor == 'plataforma':
                    override['plataforma'] = 'linux-py3.12'
                elif factor == 'entrada_no_acreditable':
                    self.escribir(
                        'task_config.yaml',
                        'project:\n  name: Demo\n  version: "v1.0.0"\n'
                        'validation:\n'
                        '  pruebas:\n'
                        '    comando: "python -m unittest"\n'
                        '    entradas:\n'
                        '      - src/\n'
                        '      - ruta_inaccesible_no_existente/\n',
                    )

                self.assertEqual(self.git('rev-parse', 'HEAD'), base_head)
                plan = chequeos.planificar(self.root, etapas=['pruebas'], entorno_override=override)
                self.assertEqual(plan['etapas']['pruebas']['accion'], 'ejecutar')
                self.assertIn(motivo_esperado, plan['etapas']['pruebas']['motivo'])

    def test_ca_m_3_cambio_durante_ejecucion_impide_acreditar_resultado(self):
        """Escenario: Impedir acreditar un resultado cuando el árbol o el entorno cambian durante la ejecución."""
        self.escribir(
            'task_config.yaml',
            'project:\n  name: Demo\n  version: "v1.0.0"\n'
            'validation:\n'
            '  pruebas: "python -m unittest"\n',
        )
        self.commit('configurar pruebas')

        def ejecutor_que_muta(cmd, **kwargs):
            self.escribir('src/app.py', 'def suma(a, b):\n    return a * b\n')
            return 0, 'Tests pasaron antes de detectar mutación\n'

        resultado = chequeos.ejecutar_comprobacion(
            self.root,
            'pruebas',
            ejecutor=ejecutor_que_muta,
        )
        self.assertFalse(resultado.get('acreditado', True))
        self.assertNotEqual(resultado.get('estado'), 'aprobado')
        self.assertTrue(resultado.get('cambio_en_vuelo'))
        self.assertNotEqual(resultado.get('identidad_inicial'), resultado.get('identidad_final'))

        plan_posterior = chequeos.planificar(self.root, etapas=['pruebas'])
        self.assertEqual(plan_posterior['etapas']['pruebas']['accion'], 'ejecutar')

    # ------------------------------------------------------------------
    # CA-M-4 y CA-M-8: Coordinación concurrente, worktrees, estado en curso y recuperación
    # ------------------------------------------------------------------
    def test_ca_m_4_y_8_coordinacion_concurrente_cli_gateway_agente_y_worktree_con_estado_en_curso(self):
        """Escenario: Compartir un único proceso de cierre y comprobación equivalente entre CLI, gateway, agente y worktrees."""
        self.escribir(
            'task_config.yaml',
            'project:\n  name: Demo\n  version: "v1.0.0"\n'
            'validation:\n'
            '  pruebas: "python -m unittest"\n',
        )
        self.commit('base concurrencia')

        worktree_dir = Path(self.tmp.name) / 'wt-agente'
        self.git('worktree', 'add', '--detach', str(worktree_dir), 'HEAD')

        invocaciones = 0
        lock_inv = threading.Lock()
        en_ejecucion = threading.Event()
        terminar = threading.Event()

        def ejecutor_lento(cmd, stream_callback=None, **kwargs):
            nonlocal invocaciones
            with lock_inv:
                invocaciones += 1
            if stream_callback:
                stream_callback('Ejecutando lote 1 de pruebas...\n')
            en_ejecucion.set()
            terminar.wait(timeout=5)
            if stream_callback:
                stream_callback('Finalizado lote completo OK.\n')
            return 0, 'Ejecutando lote 1 de pruebas...\nFinalizado lote completo OK.\n'

        resultados = {}

        def lanzar_entrada(nombre, ruta_raiz, canal):
            resultados[nombre] = chequeos.ejecutar_comprobacion(
                ruta_raiz,
                'pruebas',
                ejecutor=ejecutor_lento,
                canal=canal,
            )

        t_cli = threading.Thread(target=lanzar_entrada, args=('cli', self.root, 'cli'))
        t_cli.start()
        self.assertTrue(en_ejecucion.wait(timeout=0.4), 'El ejecutor compartido debe iniciarse')

        t_gw = threading.Thread(target=lanzar_entrada, args=('gateway', self.root, 'gateway'))
        t_ag = threading.Thread(target=lanzar_entrada, args=('agente', worktree_dir, 'agente'))
        t_gw.start()
        t_ag.start()
        time.sleep(0.15)

        estado_root = chequeos.consultar_estado(self.root)
        estado_wt = chequeos.consultar_estado(worktree_dir)
        for est in (estado_root, estado_wt):
            self.assertEqual(est['fase'], 'ejecutando')
            self.assertEqual(est['comando_activo'], 'python -m unittest')
            self.assertIn('Ejecutando lote 1 de pruebas...', est.get('salida_parcial', ''))
            self.assertIsNone(est.get('progreso'))
            self.assertTrue(est.get('siguiente_accion'))

        terminar.set()
        t_cli.join(timeout=5)
        t_gw.join(timeout=5)
        t_ag.join(timeout=5)

        self.assertEqual(invocaciones, 1)
        for nombre in ('cli', 'gateway', 'agente'):
            self.assertEqual(resultados[nombre]['codigo'], 0)
            self.assertEqual(resultados[nombre]['estado'], 'aprobado')

    def test_ca_m_4_y_8_aislamiento_de_identidad_distinta_y_recuperacion_de_proceso_interrumpido(self):
        """Escenario: Aislar solicitudes con distinto contenido o alcance y recuperar interrupciones sin falsos aprobados."""
        self.escribir(
            'task_config.yaml',
            'project:\n  name: Demo\n  version: "v1.0.0"\n'
            'validation:\n'
            '  pruebas: "python -m unittest"\n',
        )
        self.commit('base aislamiento')

        en_curso = threading.Event()
        liberar = threading.Event()

        def ejecutor_a(cmd, **kwargs):
            en_curso.set()
            liberar.wait(timeout=5)
            return 0, 'Resultado de A\n'

        hilo_a = threading.Thread(
            target=lambda: chequeos.ejecutar_comprobacion(
                self.root,
                'pruebas',
                ejecutor=ejecutor_a,
                entorno_override={'herramienta': 'identidad-A'},
            )
        )
        hilo_a.start()
        self.assertTrue(en_curso.wait(timeout=0.4), 'La ejecución con identidad A debe iniciarse')

        plan_b = chequeos.planificar(
            self.root,
            etapas=['pruebas'],
            entorno_override={'herramienta': 'identidad-B'},
        )
        self.assertEqual(plan_b['etapas']['pruebas']['accion'], 'ejecutar')
        self.assertIn('espera', plan_b['etapas']['pruebas'].get('motivo_espera', ''))
        self.assertIn('ejecutar con identidad', plan_b['etapas']['pruebas'].get('siguiente_accion', ''))

        liberar.set()
        hilo_a.join(timeout=5)

        chequeos.registrar_ejecucion_interrumpida_prueba(
            self.root,
            etapa='pruebas',
            comando='python -m unittest',
            pid=99999999,
            salida_parcial='Salida parcial antes del corte abrupto\n',
        )
        estado_interrumpido = chequeos.consultar_estado(self.root)
        self.assertEqual(estado_interrumpido['fase'], 'interrumpido')
        self.assertIn('Salida parcial antes del corte abrupto', estado_interrumpido.get('salida_parcial', ''))
        self.assertNotEqual(
            estado_interrumpido.get('evidencias', {}).get('pruebas', {}).get('resultado'),
            'aprobado',
        )

        res_recuperado = chequeos.ejecutar_comprobacion(
            self.root,
            'pruebas',
            ejecutor=lambda cmd, **kw: (0, 'Recuperación limpia OK\n'),
        )
        self.assertEqual(res_recuperado['codigo'], 0)
        self.assertEqual(res_recuperado['estado'], 'aprobado')
        self.assertFalse(res_recuperado.get('reutilizada', False))

    # ------------------------------------------------------------------
    # CA-M-5: Último resultado real e intermitencias
    # ------------------------------------------------------------------
    def test_ca_m_5_ultimo_resultado_real_invalida_verde_anterior_en_todas_las_entradas(self):
        """Escenario: Prevalecer el último resultado real e invalidar un verde anterior tras un fallo posterior en todas las entradas."""
        cmd_ok_then_fail = f'"{sys.executable}" -c "import pathlib, sys; p = pathlib.Path(\'.git/fail_flag\'); sys.exit(1 if p.exists() else 0)"'
        self.escribir(
            'task_config.yaml',
            'project:\n  name: Demo\n  version: "v1.0.0"\n'
            'validation:\n'
            f'  pruebas: {json.dumps(cmd_ok_then_fail)}\n'
            'release:\n'
            '  puertas: ["pruebas"]\n',
        )
        self.commit('configurar suite para CA-M-5')

        self.assertEqual(motor.verificar(self.root, cmd_ok_then_fail), 0)
        prompt_verde = motor.construir_prompt_agente(self.root, 'hades', 'Revisar código')
        self.assertIn(cmd_ok_then_fail, prompt_verde)

        (self.root / '.git/fail_flag').write_text('1', encoding='utf-8')
        res_forzado = chequeos.ejecutar_comprobacion(
            self.root,
            'pruebas',
            comando=cmd_ok_then_fail,
            forzar_ejecucion=True,
        )
        self.assertEqual(res_forzado['codigo'], 1)

        lineas_antes = (self.root / motor.EVIDENCIAS).read_text(encoding='utf-8').splitlines()
        self.assertEqual(len(lineas_antes), 2)
        self.assertEqual(json.loads(lineas_antes[-1])['codigo'], 1)

        prompt_rojo = motor.construir_prompt_agente(self.root, 'hades', 'Revisar código')
        self.assertNotIn(cmd_ok_then_fail, prompt_rojo)

        estado_actual = chequeos.consultar_estado(self.root)
        self.assertEqual(
            estado_actual['evidencias'].get(cmd_ok_then_fail, {}).get('resultado'),
            'fallido',
        )

        eval_release = chequeos.evaluar_puerta(self.root, puerta='release', ejecutar=False)
        self.assertEqual(eval_release['estado'], 'fallido')
        self.assertEqual(eval_release['plan']['etapas']['pruebas']['accion'], 'ejecutar')

        lineas_despues_consulta = (self.root / motor.EVIDENCIAS).read_text(encoding='utf-8').splitlines()
        self.assertEqual(len(lineas_despues_consulta), 2)
        self.assertEqual(json.loads(lineas_despues_consulta[-1])['codigo'], 1)

        with patch.object(motor.subprocess, 'run', wraps=motor.subprocess.run) as spy_run:
            self.assertEqual(motor.verificar(self.root, cmd_ok_then_fail), 1)
            self.assertTrue(any(c.kwargs.get('shell') for c in spy_run.call_args_list))

    def test_ca_m_5_historial_de_intermitencias_se_conserva_y_no_reintenta_en_fallo(self):
        """Escenario: Registrar historial de intermitencias sin borrarlo por un verde posterior ni reintentar hasta lograr verde."""
        self.escribir(
            'task_config.yaml',
            'project:\n  name: Demo\n  version: "v1.0.0"\n'
            'validation:\n'
            '  pruebas: "python -m unittest"\n',
        )
        self.commit('base intermitencia')

        secuencia = [(0, 'verde 1\n'), (1, 'fallo intermitente\n'), (0, 'verde 2\n')]
        invocaciones_Por_llamada = []

        for codigo_esperado, salida in secuencia:
            conteo = 0

            def ejecutor_secuencia(cmd, **kw):
                nonlocal conteo
                conteo += 1
                return codigo_esperado, salida

            res = chequeos.ejecutar_comprobacion(
                self.root,
                'pruebas',
                ejecutor=ejecutor_secuencia,
                forzar_ejecucion=True,
            )
            invocaciones_Por_llamada.append(conteo)
            self.assertEqual(res['codigo'], codigo_esperado)

        self.assertEqual(invocaciones_Por_llamada, [1, 1, 1])

        estado = chequeos.consultar_estado(self.root)
        ev = estado['evidencias']['pruebas']
        self.assertEqual(ev['resultado'], 'aprobado')
        self.assertTrue(ev['intermitente'])
        self.assertEqual(ev['transiciones'], ['aprobado', 'fallido', 'aprobado'])
        self.assertIn('intermitencia', ev['diagnostico'].lower())

    # ------------------------------------------------------------------
    # CA-M-6 y CA-M-7: Diagnóstico, reparación acotada y caché por comprobación
    # ------------------------------------------------------------------
    def test_ca_m_6_y_7_diagnostico_reparacion_y_cache_por_comprobacion(self):
        """Escenario: Diagnosticar un fallo, conservar en caché las etapas aprobadas independientes y ampliar la validación según impacto."""
        self.escribir('packaging/build_cfg.json', '{"target": "broken"}\n')
        self.escribir(
            'task_config.yaml',
            'project:\n  name: Demo\n  version: "v1.0.0"\n'
            'validation:\n'
            '  formato:\n'
            '    comando: "ruff format --check src"\n'
            '    entradas: ["src/"]\n'
            '  lint:\n'
            '    comando: "ruff check src"\n'
            '    entradas: ["src/"]\n'
            '  pruebas:\n'
            '    comando: "python -m unittest"\n'
            '    entradas: ["src/", "tests/"]\n'
            '  builds:\n'
            '    comando: "python -m build"\n'
            '    entradas: ["packaging/"]\n'
            'release:\n'
            '  puertas: ["formato", "lint", "pruebas", "builds"]\n',
        )
        self.commit('configurar etapas con alcances')

        ejecutadas_ronda_1 = []

        def ejecutor_ronda_1(cmd, etapa=None, **kw):
            ejecutadas_ronda_1.append(etapa)
            if etapa == 'builds':
                return 1, 'Error en packaging/build_cfg.json\n'
            return 0, f'{etapa} OK\n'

        eval_1 = chequeos.evaluar_puerta(self.root, puerta='release', ejecutar=True, ejecutor=ejecutor_ronda_1)
        self.assertEqual(eval_1['estado'], 'fallido')
        self.assertEqual(ejecutadas_ronda_1, ['formato', 'lint', 'pruebas', 'builds'])

        diag = chequeos.diagnosticar_fallo(self.root, 'builds', eval_1['etapas']['builds'])
        self.assertEqual(diag['etapa'], 'builds')
        self.assertEqual(diag['siguiente_accion'], 'reparar')

        self.escribir('packaging/build_cfg.json', '{"target": "fixed"}\n')

        plan_rep = chequeos.planificar_reparacion(self.root, cambios=['packaging/build_cfg.json'], puerta='release')
        for indep in ('formato', 'lint', 'pruebas'):
            self.assertEqual(plan_rep['etapas'][indep]['accion'], 'reutilizar')
        self.assertEqual(plan_rep['etapas']['builds']['accion'], 'ejecutar')
        self.assertIn('packaging/build_cfg.json', plan_rep['etapas']['builds']['motivo'])

        ejecutadas_ronda_2 = []
        eval_2 = chequeos.evaluar_puerta(
            self.root,
            puerta='release',
            ejecutar=True,
            ejecutor=lambda cmd, etapa=None, **kw: ejecutadas_ronda_2.append(etapa) or (0, 'build OK\n'),
        )
        self.assertEqual(eval_2['estado'], 'aprobado')
        self.assertEqual(ejecutadas_ronda_2, ['builds'])

        diag_humano = chequeos.diagnosticar_fallo(
            self.root,
            'builds',
            {'codigo': 1, 'salida': 'Falta certificado de firma de código de producción'},
            intentos_agotados=True,
            motivo_humano='Se requiere el certificado de firma de producción que no está disponible en el entorno local.',
        )
        self.assertEqual(diag_humano['siguiente_accion'], 'intervencion_humana')
        self.assertIn('certificado de firma', diag_humano['motivo_intervencion_humana'])

    # ------------------------------------------------------------------
    # CA-M-9: Separación validar / cerrar_local / etiquetar / publicar y worktree preparado
    # ------------------------------------------------------------------
    def test_ca_m_9_separacion_validar_cerrar_local_etiquetar_publicar_y_evidencia_en_worktree_preparado(self):
        """Escenario: Separar validar, cerrar localmente, etiquetar y publicar respetando las restricciones del proyecto y el árbol preparado."""
        remote_dir = Path(self.tmp.name) / 'remote.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(remote_dir)], check=True)
        self.git('remote', 'add', 'origin', str(remote_dir))

        contador_preflight = self.root / '.git/preflight_runs.txt'
        cmd_preflight = (
            f'"{Path(sys.executable).as_posix()}" -c '
            f'"import pathlib; p = pathlib.Path(r\'{contador_preflight.as_posix()}\'); '
            f'n = int(p.read_text()) if p.exists() else 0; p.write_text(str(n + 1))"'
        )

        self.escribir('CHANGELOG.md', '## [v1.0.0]\n- Entrega inicial\n')
        for doc in ('requirements', 'req_analysis', 'platform_plan', 'platform_review', 'work_plan'):
            self.escribir(f'docs/requirements/{doc}.md', 'APROBADO\n')
        self.escribir(
            'docs/plan/tasks/T-DEM-0001.md',
            '---\nid: T-DEM-0001\nversion: v1.0.0\nstatus: completed\ndepende_de: []\n---\n',
        )
        self.escribir('docs/review/code_reviews/T-DEM-0001-code-review.md', 'APROBADO\n')
        self.escribir('docs/review/versions/v1.0-arquitectura.md', 'APROBADO\n')
        self.escribir('docs/review/versions/v1.0-revision.md', '## T-DEM-0001\n- Bloqueos: ninguno\n- Validación funcional: OK\n')
        self.escribir(
            'task_config.yaml',
            'project:\n  name: Demo\n  prefix: DEM\n  version: "v1.0.0"\n'
            'validation:\n'
            f'  command: {json.dumps(cmd_preflight)}\n'
            'release:\n'
            '  manifests:\n'
            '    - path: pyproject.toml\n'
            '      type: toml\n'
            '      key: project.version\n'
            '  preflight:\n'
            f'    - {json.dumps(cmd_preflight)}\n'
            '  restricciones:\n'
            '    gateway:\n'
            '      validar: true\n'
            '      cerrar_local: true\n'
            '      etiquetar: false\n'
            '      publicar: false\n',
        )
        self.commit('preparar repo para release')
        self.git('push', '-q', 'origin', 'main')
        self.git('checkout', '-qb', 'release/v1.0')
        self.escribir('src/release_feature.py', 'FEATURE = True\n')
        self.commit('feat: cambio de release')

        self.assertEqual(motor.verificar(self.root, cmd_preflight), 0)
        self.assertEqual(int(contador_preflight.read_text(encoding='utf-8')), 1)
        self.assertEqual(self.git('tag'), '')

        respuesta_gw = cierre_version.cerrar(self.root, 'v1.0 confirmo', motor)
        self.assertIn('restricción', respuesta_gw.lower())
        self.assertEqual(self.git('tag', cwd=remote_dir), '')

        self.escribir(
            'task_config.yaml',
            (self.root / 'task_config.yaml').read_text(encoding='utf-8').replace('publicar: false', 'publicar: true').replace('etiquetar: false', 'etiquetar: true'),
        )
        self.commit('autorizar publicación')
        contador_preflight.write_text('0', encoding='utf-8')
        self.assertEqual(motor.verificar(self.root, cmd_preflight), 0)
        self.assertEqual(int(contador_preflight.read_text(encoding='utf-8')), 1)

        release_tools.publicar_version(self.root, 'v1.0.0', rama='release/v1.0')
        self.assertEqual(
            int(contador_preflight.read_text(encoding='utf-8')),
            1,
            'El worktree de release con idéntico árbol integrado debe reutilizar la evidencia sin reejecutar preflight',
        )
        self.assertEqual(self.git('tag', cwd=remote_dir), 'v1.0.0')

        self.git('checkout', '-qb', 'release/v1.1', 'main')
        self.escribir('pyproject.toml', '[project]\nname = "demo"\nversion = "1.1.0"\n')
        self.escribir('CHANGELOG.md', '## [v1.1.0]\n- Nueva versión\n\n## [v1.0.0]\n- Entrega inicial\n')
        self.escribir(
            'task_config.yaml',
            (self.root / 'task_config.yaml').read_text(encoding='utf-8').replace('v1.0.0', 'v1.1.0'),
        )
        self.escribir('src/release_v11.py', 'V11 = True\n')
        self.commit('feat: preparar release v1.1')

        contador_preflight.write_text('0', encoding='utf-8')
        self.assertEqual(motor.verificar(self.root, cmd_preflight), 0)
        self.assertEqual(int(contador_preflight.read_text(encoding='utf-8')), 1)

        self.git('checkout', 'main')
        self.escribir('src/main_hotfix.py', 'HOTFIX = True\n')
        self.commit('fix: cambio relevante en main antes de integrar release')
        self.git('push', '-q', 'origin', 'main')
        self.git('checkout', 'release/v1.1')

        release_tools.publicar_version(self.root, 'v1.1.0', rama='release/v1.1')
        self.assertEqual(
            int(contador_preflight.read_text(encoding='utf-8')),
            2,
            'Si el merge con main modifica entradas relevantes en el worktree integrado, debe invalidar y reejecutar preflight',
        )

    # ------------------------------------------------------------------
    # CA-M-10: Compatibilidad, transición de evidencia histórica y adopción Afinn
    # ------------------------------------------------------------------
    def test_ca_m_10_compatibilidad_transicion_evidencia_historica_y_migracion_lanzador_afinn(self):
        """Escenario: Conservar compatibilidad con configuraciones actuales, tratar evidencia histórica y adoptar el flujo común sin doble suite."""
        contador_suite = self.root / '.git/afinn_suite_runs.txt'
        cmd_suite = (
            f'"{Path(sys.executable).as_posix()}" -c '
            f'"import pathlib; p = pathlib.Path(r\'{contador_suite.as_posix()}\'); '
            f'n = int(p.read_text()) if p.exists() else 0; p.write_text(str(n + 1))"'
        )
        self.escribir(
            'task_config.yaml',
            'project:\n  name: AfinnSim\n  prefix: AFN\n  version: "v1.0.0"\n'
            'validation:\n'
            f'  command: {json.dumps(cmd_suite)}\n'
            '  formato: "ruff format --check {ficheros}"\n'
            '  lint: "ruff check {ficheros}"\n'
            'release:\n'
            '  preflight:\n'
            f'    - {json.dumps(cmd_suite)}\n'
            '  restricciones:\n'
            '    gateway:\n'
            '      publicar: false\n',
        )
        self.escribir(
            'scripts/cerrar_version.py',
            f'import subprocess\nsubprocess.run({cmd_suite!r}, shell=True, check=True)\n',
        )
        self.commit('configuración heredada con lanzador redundante')

        arbol_actual = motor.arbol(self.root)
        registro_historico_incompleto = {
            'fecha': '2026-10-01T10:00:00',
            'comando': 'comando-historico',
            'arbol': arbol_actual,
            'codigo': 0,
        }
        (self.root / motor.EVIDENCIAS).write_text(
            json.dumps(registro_historico_incompleto) + '\n',
            encoding='utf-8',
        )
        self.assertEqual(motor.verificar(self.root, cmd_suite), 0)
        self.assertEqual(int(contador_suite.read_text(encoding='utf-8')), 1)

        ruta_externa_inaccesible = Path(self.tmp.name) / 'fuera_del_workspace' / 'Afinn'
        reporte = chequeos.adoptar_flujo_comun(
            self.root,
            ruta_externa_afinn=ruta_externa_inaccesible,
        )

        transicion = reporte.get('transicion_evidencia', {})
        self.assertEqual(
            transicion.get('comando-historico', {}).get('clasificacion'),
            'historial_sin_acreditar',
        )
        self.assertEqual(
            transicion.get(cmd_suite, {}).get('clasificacion'),
            'vigente_reutilizable',
        )
        self.assertTrue(reporte.get('lanzadores_migrados'))
        self.assertEqual(
            reporte.get('restricciones_conservadas', {}).get('gateway', {}).get('publicar'),
            False,
        )

        res_cierre = chequeos.ejecutar_cierre_comun(self.root)
        self.assertEqual(res_cierre['codigo'], 0)
        self.assertEqual(
            int(contador_suite.read_text(encoding='utf-8')),
            1,
            'Tras adoptar el flujo común, la suite de cierre no se duplica sobre el mismo árbol',
        )

        self.assertEqual(reporte['migracion_afinn_externo']['estado'], 'bloqueado')
        self.assertFalse(reporte['migracion_afinn_externo']['migracion_in_situ_realizada'])
        self.assertTrue(reporte['migracion_afinn_externo']['motivo'])


if __name__ == '__main__':
    unittest.main()
