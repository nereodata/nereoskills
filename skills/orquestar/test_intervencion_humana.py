"""Pruebas de B-ADV-0026: intervención humana por Telegram sin detener tareas independientes."""

import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs

from tests import aislamiento_telegram  # noqa: F401


def _cargar_modulo(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


ROOT_REPO = Path(__file__).resolve().parents[2]
motor = _cargar_modulo('orquestar_b0026', ROOT_REPO / 'skills' / 'orquestar' / 'orquestar.py')
gateway = _cargar_modulo('gateway_b0026', ROOT_REPO / 'skills' / 'telegram_gateway' / 'gateway.py')
gateway.motor = motor


class IntervencionHumanaBase(unittest.TestCase):
    """Fixture con repositorio Git real, proyecto configurado y transporte Telegram controlado."""

    def setUp(self):
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / 'ProyectoUno'
        self.root.mkdir(parents=True, exist_ok=True)
        self.inicializar_repo(self.root, prefijo='ADV', version='v1.1.0', rama='release/v1.1')
        self.enterContext(patch.object(motor, 'git', side_effect=lambda *args, **kw: self.git(*args)))

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args, root=None):
        destino = root or self.root
        r = subprocess.run(
            ['git', *args],
            cwd=destino,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True,
        )
        return r.stdout.strip()

    def inicializar_repo(self, root, prefijo='ADV', version='v1.1.0', rama='release/v1.1'):
        self.git('init', '-q', root=root)
        self.git('config', 'user.name', 'Test User', root=root)
        self.git('config', 'user.email', 'test@example.com', root=root)
        archivos = {
            'task_config.yaml': (
                f'project:\n  name: {root.name}\n  prefix: {prefijo}\n  version: "{version}"\n'
                'levels:\n  master:\n    id_prefix: ' + prefijo + '\n    path: docs/plan/\n'
                '    folders:\n      tasks: tasks/\n      bugs: bugs/\n'
            ),
            'docs/requirements/requirements.md': '# Idea\n',
            'docs/requirements/req_analysis.md': '**Estado:** APROBADO\n',
            'docs/requirements/platform_plan.md': '# Plan\n',
            'docs/requirements/platform_review.md': '**Veredicto:** APROBADO\n',
            'docs/requirements/work_plan.md': '# Work plan\n',
            'docs/review/versions/v1.1-revision.md': '# Revisión de versión v1.1\n',
        }
        for rel, contenido in archivos.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(contenido, encoding='utf-8')
        self.git('add', '.', root=root)
        self.git('commit', '-qm', 'chore: init', root=root)
        self.git('branch', '-M', 'main', root=root)
        if rama != 'main':
            self.git('checkout', '-qb', rama, root=root)

    def configurar_telegram(self, root=None, token='tok-local', usuarios='111,222', cfg_telegram=None):
        destino = root or self.root
        if token is not None:
            (destino / '.env').write_text(
                f'TELEGRAM_BOT_TOKEN={token}\nTELEGRAM_ALLOWED_USER_IDS={usuarios}\n',
                encoding='utf-8',
            )
        elif (destino / '.env').exists():
            (destino / '.env').unlink()
        if cfg_telegram is not None:
            (destino / 'orchestration.json').write_text(
                json.dumps({'telegram': cfg_telegram}, ensure_ascii=False),
                encoding='utf-8',
            )
        motor.excluir(destino)

    def crear_tarea(self, iid, status='planned', depende_de=None, weight=10, version='v1.1.0', root=None):
        destino = root or self.root
        deps = json.dumps(depende_de or [])
        ruta = destino / f'docs/plan/tasks/{iid}.md'
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            f'---\nid: {iid}\ntitle: "Tarea {iid}"\ntype: funcional\nweight: {weight}\n'
            f'dificultad: media\nversion: "{version}"\nstatus: {status}\ndepende_de: {deps}\n---\n\n'
            f'# {iid}: Tarea {iid}\n\nDescripción base de {iid}.\n',
            encoding='utf-8',
        )
        return ruta

    def args_bucle(self, max_pasos=8, espera_max=0):
        return motor.argparse.Namespace(
            idea=None,
            docs='docs/requirements',
            test=None,
            harness='claude',
            estado=False,
            max_pasos=max_pasos,
            reintentos=2,
            reintentos_arnes=0,
            espera_max=espera_max,
            cmd=None,
            presupuesto=None,
            recarga=None,
        )


class IntervencionHumanaTests(IntervencionHumanaBase):
    """Verifica CA-1..CA-9 del circuito de intervención humana por Telegram."""

    def test_ca1_stdin_cerrado_en_lanzar_y_decisiones_por_defecto_en_prompt(self):
        """CA-1: lanzar() cierra stdin cuando no hay entrada y el prompt mantiene decisiones con valor por defecto."""
        prompt = motor.construir_prompt_paso(self.root, 'task-dev', 'T-ADV-0101')
        self.assertIn('No hagas preguntas: aplica las reglas del modo orquestado.', prompt)
        self.assertIn('--preguntar', prompt)

        llamadas_run = []

        def fake_run(cmd, **kwargs):
            llamadas_run.append(kwargs)
            salida = json.dumps({'result': 'ok', 'status': 'SUCCESS', 'num_turns': 1})
            return subprocess.CompletedProcess(cmd, 0, stdout=salida, stderr='')

        with patch.object(motor.subprocess, 'run', side_effect=fake_run):
            motor.lanzar(['claude', '--output-format', 'json'], self.root, 'claude', entrada=None)
            motor.lanzar(['agy', '--output-format', 'json'], self.root, 'agy', entrada=None)

        self.assertEqual(len(llamadas_run), 2)
        for kwargs in llamadas_run:
            self.assertEqual(kwargs.get('stdin'), subprocess.DEVNULL)

    def test_ca1_ca2_ca3_ca4_bloqueo_local_wip_aviso_y_continuidad_abc(self):
        """CA-1, CA-2, CA-3, CA-4: A se bloquea y aísla su trabajo en wip/A, avisa por Telegram y B continúa mientras C espera."""
        self.configurar_telegram()
        self.crear_tarea('T-ADV-0101', weight=10, depende_de=[])
        self.crear_tarea('T-ADV-0102', weight=20, depende_de=[])
        self.crear_tarea('T-ADV-0103', weight=30, depende_de=['T-ADV-0101'])
        self.git('add', '.')
        self.git('commit', '-qm', 'tareas A, B y C')

        enviados = []

        def fake_urlopen(url, datos=None, timeout=15):
            campos = parse_qs(datos.decode('utf-8')) if datos else {}
            enviados.append((campos.get('chat_id', [''])[0], campos.get('text', [''])[0]))
            return MagicMock(**{'__enter__.return_value.status': 200})

        orden_ejecucion = []
        arbol_al_entrar_b = []

        def fake_ejecutar(a, root, prompt, **kwargs):
            iid = kwargs['env']['ORQUESTAR_ID']
            orden_ejecucion.append(iid)
            if iid == 'T-ADV-0101':
                modulo_a = root / 'src' / 'modulo_a.py'
                modulo_a.parent.mkdir(parents=True, exist_ok=True)
                modulo_a.write_text('OAUTH_MODE = "wip_a"\n', encoding='utf-8')
                motor.solicitar_intervencion(
                    root,
                    'T-ADV-0101',
                    '¿Usar proveedor OAuth interno o externo?',
                    contexto='Falta decidir proveedor sin valor por defecto seguro',
                    paso='task-dev',
                )
                return 0, {}, 'Bloqueada esperando decisión humana Q-ADV-0001'
            if iid == 'T-ADV-0102':
                self.assertNotIn('src/modulo_a.py', self.git('ls-tree', '-r', '--name-only', 'HEAD'))
                arbol_al_entrar_b.append((
                    self.git('status', '--porcelain'),
                    (root / 'src' / 'modulo_a.py').exists(),
                ))
                modulo_b = root / 'src' / 'modulo_b.py'
                modulo_b.parent.mkdir(parents=True, exist_ok=True)
                modulo_b.write_text('MODULO_B = True\n', encoding='utf-8')
                f_b = motor.fichero_de(root, 'T-ADV-0102')
                f_b.write_text(
                    f_b.read_text(encoding='utf-8').replace('status: planned', 'status: completed'),
                    encoding='utf-8',
                )
                rev = root / 'docs/review/code_reviews/T-ADV-0102-code-review.md'
                rev.parent.mkdir(parents=True, exist_ok=True)
                rev.write_text('**Veredicto:** APROBADO\n', encoding='utf-8')
                self.git('add', '.')
                self.git('commit', '-qm', 'feat(T-ADV-0102): completar B')
                return 0, {}, 'B completada'
            self.fail(f'No debía ejecutarse {iid} mientras T-ADV-0101 sigue bloqueada')

        with (
            patch.object(motor, 'ejecutar', side_effect=fake_ejecutar),
            patch('urllib.request.urlopen', side_effect=fake_urlopen),
            redirect_stdout(io.StringIO()),
        ):
            codigo = motor.bucle(self.args_bucle(max_pasos=5, espera_max=0), self.root)

        self.assertEqual(codigo, 2)
        self.assertEqual(orden_ejecucion, ['T-ADV-0101', 'T-ADV-0102'])
        self.assertEqual(arbol_al_entrar_b, [('', False)])

        preguntas = motor.listar_preguntas(self.root)
        self.assertEqual(len(preguntas), 1)
        q = preguntas[0]
        self.assertEqual(q['id'], 'Q-ADV-0001')
        self.assertEqual(q['tarea_id'], 'T-ADV-0101')
        self.assertEqual(q['estado'], 'pendiente')
        self.assertIn('¿Usar proveedor OAuth interno o externo?', q['pregunta'])
        self.assertIn('Falta decidir proveedor sin valor por defecto seguro', q['contexto'])
        self.assertTrue(q['notificada'])

        self.assertFalse((self.root / 'src' / 'modulo_a.py').exists())
        self.assertTrue((self.root / 'src' / 'modulo_b.py').exists())
        contenido_wip = self.git('show', 'wip/T-ADV-0101:src/modulo_a.py')
        self.assertEqual(contenido_wip, 'OAUTH_MODE = "wip_a"')
        self.assertEqual(self.git('status', '--porcelain'), '')

        fm_a = motor.frontmatter(motor.fichero_de(self.root, 'T-ADV-0101'))
        fm_b = motor.frontmatter(motor.fichero_de(self.root, 'T-ADV-0102'))
        fm_c = motor.frontmatter(motor.fichero_de(self.root, 'T-ADV-0103'))
        self.assertEqual((fm_a['status'], fm_a['pendiente_de']), ('blocked', 'humano'))
        self.assertEqual(fm_b['status'], 'completed')
        self.assertEqual(fm_c['status'], 'planned')
        revision = (self.root / 'docs/review/versions/v1.1-revision.md').read_text(encoding='utf-8')
        self.assertIn('Q-ADV-0001', revision)
        self.assertIn('¿Usar proveedor OAuth interno o externo?', revision)

        avisos_pregunta = [(chat, txt) for chat, txt in enviados if 'Q-ADV-0001' in txt]
        self.assertEqual([chat for chat, _ in avisos_pregunta], ['111', '222'])
        for _, txt in avisos_pregunta:
            self.assertIn('T-ADV-0101', txt)
            self.assertIn('Q-ADV-0001', txt)
            self.assertIn('¿Usar proveedor OAuth interno o externo?', txt)
            self.assertIn('/responder Q-ADV-0001', txt)

    def test_ca1_ca3_fallo_o_ausencia_de_canal_conserva_bloqueo_sin_duplicar_avisos(self):
        """CA-1, CA-3: Sin canal, evento desactivado o fallo HTTP el bloqueo y diagnóstico persisten sin avisos duplicados."""
        casos = [
            ('sin_credenciales', None, None, 'canal no disponible', 0),
            ('evento_desactivado', 'tok-local', {'eventos': ['version', 'cuota']}, 'evento desactivado', 0),
            ('fallo_http', 'tok-local', None, 'fallo de envío', 2),
        ]
        for nombre, token, cfg_tg, diag_esperado, llamadas_http_esperadas in casos:
            with self.subTest(caso=nombre):
                sub_root = Path(self.tmp.name) / f'Proj_{nombre}'
                sub_root.mkdir(parents=True, exist_ok=True)
                self.inicializar_repo(sub_root, prefijo='ADV', version='v1.1.0', rama='release/v1.1')
                self.configurar_telegram(root=sub_root, token=token, usuarios='111,222', cfg_telegram=cfg_tg)
                self.crear_tarea('T-ADV-0101', root=sub_root)
                self.crear_tarea('T-ADV-0102', root=sub_root, weight=20)
                self.git('add', '.', root=sub_root)
                self.git('commit', '-qm', 'init tarea', root=sub_root)

                intentos_http = []

                def fake_urlopen(url, datos=None, timeout=15):
                    intentos_http.append(url)
                    raise OSError('red caída simulada')

                with patch('urllib.request.urlopen', side_effect=fake_urlopen), redirect_stdout(io.StringIO()):
                    q = motor.solicitar_intervencion(
                        sub_root,
                        'T-ADV-0101',
                        '¿Puerto de escucha de producción?',
                        contexto='Configuración de red',
                        paso='task-dev',
                    )
                    self.assertEqual(q['id'], 'Q-ADV-0001')
                    self.assertEqual(q['estado'], 'pendiente')
                    self.assertEqual(q['diagnostico_aviso'], diag_esperado)
                    self.assertEqual(len(intentos_http), llamadas_http_esperadas)

                    texto_parte = motor.parte(sub_root)
                    texto_preguntas = gateway.responder(sub_root, '111', '/preguntas', {'111'})
                    self.assertIn(diag_esperado, gateway.responder(sub_root, '111', '/estado', {'111'}))
                    motor.solicitar_intervencion(
                        sub_root,
                        'T-ADV-0101',
                        '¿Puerto de escucha de producción?',
                        contexto='Configuración de red',
                        paso='task-dev',
                    )
                    self.assertEqual(len(intentos_http), llamadas_http_esperadas)
                    self.assertIn('Q-ADV-0001', texto_parte)
                    self.assertIn(diag_esperado, texto_preguntas)

                    def completar_independiente(a, root, prompt, **kwargs):
                        self.assertEqual(kwargs['env']['ORQUESTAR_ID'], 'T-ADV-0102')
                        f = motor.fichero_de(root, 'T-ADV-0102')
                        f.write_text(f.read_text(encoding='utf-8').replace('status: planned', 'status: completed'), encoding='utf-8')
                        rev = root / 'docs/review/code_reviews/T-ADV-0102-code-review.md'
                        rev.parent.mkdir(parents=True, exist_ok=True)
                        rev.write_text('**Veredicto:** APROBADO\n', encoding='utf-8')
                        self.git('add', '.', root=root)
                        self.git('commit', '-qm', 'completar B', root=root)
                        return 0, {}, ''

                    with (patch.object(motor, 'git', side_effect=lambda *args, **kw: self.git(*args, root=sub_root)),
                          patch.object(motor, 'ejecutar', side_effect=completar_independiente)):
                        motor.bucle(self.args_bucle(max_pasos=2), sub_root)
                    self.assertEqual(len(intentos_http), llamadas_http_esperadas)

    def test_ca4_ca6_ca7_ca8_respuesta_durante_b_se_incorpora_entre_pasos_y_reanuda_a_y_c(self):
        """CA-4, CA-6, CA-7, CA-8: La respuesta recibida durante B no toca git en caliente, se incorpora al acabar B y reanuda A y C."""
        self.configurar_telegram()
        self.crear_tarea('T-ADV-0101', weight=10, depende_de=[])
        self.crear_tarea('T-ADV-0102', weight=20, depende_de=[])
        self.crear_tarea('T-ADV-0103', weight=30, depende_de=['T-ADV-0101'])
        self.git('add', '.')
        self.git('commit', '-qm', 'tareas A, B y C')

        enviados = []

        def fake_urlopen(url, datos=None, timeout=15):
            campos = parse_qs(datos.decode('utf-8')) if datos else {}
            enviados.append((campos.get('chat_id', [''])[0], campos.get('text', [''])[0]))
            return MagicMock(**{'__enter__.return_value.status': 200})

        orden_pasos = []
        confirmacion_durante_b = []
        estado_a_durante_b = []
        wip_recuperado_en_a = []
        prompt_en_a_reanudada = []

        (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')

        def fake_ejecutar(a, root, prompt, **kwargs):
            iid = kwargs['env']['ORQUESTAR_ID']
            orden_pasos.append(iid)
            if iid == 'T-ADV-0101' and orden_pasos.count('T-ADV-0101') == 1:
                modulo_a = root / 'src' / 'modulo_a.py'
                modulo_a.parent.mkdir(parents=True, exist_ok=True)
                modulo_a.write_text('PROVEEDOR = "pendiente"\n', encoding='utf-8')
                motor.solicitar_intervencion(
                    root,
                    'T-ADV-0101',
                    '¿Usar proveedor OAuth interno o externo?',
                    contexto='Configuración de autenticación',
                    paso='task-dev',
                )
                return 0, {}, 'T-ADV-0101 bloqueada'
            if iid == 'T-ADV-0102':
                head_antes_respuesta = self.git('rev-parse', 'HEAD')
                resp_tg = gateway.responder(
                    root,
                    '111',
                    '/responder Q-ADV-0001 Usar proveedor OAuth interno',
                    {'111', '222'},
                )
                confirmacion_durante_b.append(resp_tg)
                estado_a_durante_b.append((
                    motor.frontmatter(motor.fichero_de(root, 'T-ADV-0101'))['status'],
                    self.git('rev-parse', 'HEAD') == head_antes_respuesta,
                    self.git('status', '--porcelain'),
                ))
                f_b = motor.fichero_de(root, 'T-ADV-0102')
                f_b.write_text(
                    f_b.read_text(encoding='utf-8').replace('status: planned', 'status: completed'),
                    encoding='utf-8',
                )
                rev = root / 'docs/review/code_reviews/T-ADV-0102-code-review.md'
                rev.parent.mkdir(parents=True, exist_ok=True)
                rev.write_text('**Veredicto:** APROBADO\n', encoding='utf-8')
                self.git('add', '.')
                self.git('commit', '-qm', 'feat(T-ADV-0102): completar B')
                return 0, {}, 'T-ADV-0102 completada'
            if iid == 'T-ADV-0101' and orden_pasos.count('T-ADV-0101') == 2:
                modulo_a = root / 'src' / 'modulo_a.py'
                wip_recuperado_en_a.append(
                    modulo_a.read_text(encoding='utf-8') if modulo_a.exists() else None
                )
                prompt_en_a_reanudada.append(prompt)
                fm = motor.frontmatter(motor.fichero_de(root, iid))
                self.assertEqual(fm['status'], 'planned')
                self.assertFalse(fm.get('pendiente_de'))
                q = motor.listar_preguntas(root)[0]
                self.assertEqual(q['estado'], 'incorporada')
                self.assertIn('Usar proveedor OAuth interno', (root / 'docs/review/versions/v1.1-revision.md').read_text(encoding='utf-8'))
                modulo_a.write_text('PROVEEDOR = "interno"\n', encoding='utf-8')
                f_a = motor.fichero_de(root, 'T-ADV-0101')
                f_a.write_text(
                    f_a.read_text(encoding='utf-8').replace('status: planned', 'status: completed').replace('status: in_progress', 'status: completed'),
                    encoding='utf-8',
                )
                rev = root / 'docs/review/code_reviews/T-ADV-0101-code-review.md'
                rev.parent.mkdir(parents=True, exist_ok=True)
                rev.write_text('**Veredicto:** APROBADO\n', encoding='utf-8')
                self.git('add', '.')
                self.git('commit', '-qm', 'feat(T-ADV-0101): completar A con OAuth interno')
                return 0, {}, 'T-ADV-0101 completada'
            if iid == 'T-ADV-0103':
                f_c = motor.fichero_de(root, 'T-ADV-0103')
                f_c.write_text(
                    f_c.read_text(encoding='utf-8').replace('status: planned', 'status: completed'),
                    encoding='utf-8',
                )
                rev = root / 'docs/review/code_reviews/T-ADV-0103-code-review.md'
                rev.parent.mkdir(parents=True, exist_ok=True)
                rev.write_text('**Veredicto:** APROBADO\n', encoding='utf-8')
                (root / 'docs/review/versions/v1.1-arquitectura.md').write_text('**Veredicto:** APROBADO\n', encoding='utf-8')
                self.git('add', '.')
                self.git('commit', '-qm', 'feat(T-ADV-0103): completar C')
                return 0, {}, 'T-ADV-0103 completada'
            return 0, {}, ''

        with (
            patch.object(motor, 'ejecutar', side_effect=fake_ejecutar),
            patch('urllib.request.urlopen', side_effect=fake_urlopen),
            redirect_stdout(io.StringIO()),
        ):
            codigo = motor.bucle(self.args_bucle(max_pasos=8, espera_max=0), self.root)

        self.assertEqual(codigo, 2)
        self.assertEqual(orden_pasos, ['T-ADV-0101', 'T-ADV-0102', 'T-ADV-0101', 'T-ADV-0103'])
        self.assertEqual(estado_a_durante_b, [('blocked', True, '')])
        self.assertIn(
            'Respuesta recibida para Q-ADV-0001 (T-ADV-0101); se incorporará al terminar el paso en curso',
            confirmacion_durante_b[0],
        )
        self.assertEqual(wip_recuperado_en_a, ['PROVEEDOR = "pendiente"\n'])
        self.assertIn('Usar proveedor OAuth interno', prompt_en_a_reanudada[0])
        self.assertTrue(any('reanudada' in txt.lower() and 'T-ADV-0101' in txt for _, txt in enviados))

        for iid in ('T-ADV-0101', 'T-ADV-0102', 'T-ADV-0103'):
            self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, iid))['status'], 'completed')

    def test_ca6_respuesta_insuficiente_mantiene_bloqueo_y_explica_que_falta(self):
        """CA-6: Una respuesta que no resuelve el impedimento conserva el bloqueo y explica qué falta."""
        self.configurar_telegram()
        self.crear_tarea('T-ADV-0101', weight=10, depende_de=[])
        self.git('add', '.')
        self.git('commit', '-qm', 'tarea A')

        enviados = []

        def fake_urlopen(url, datos=None, timeout=15):
            campos = parse_qs(datos.decode('utf-8')) if datos else {}
            enviados.append((campos.get('chat_id', [''])[0], campos.get('text', [''])[0]))
            return MagicMock(**{'__enter__.return_value.status': 200})

        with patch('urllib.request.urlopen', side_effect=fake_urlopen), redirect_stdout(io.StringIO()):
            motor.solicitar_intervencion(
                self.root,
                'T-ADV-0101',
                'Indica la URL base y el puerto del servicio',
                contexto='Configuración de despliegue',
                paso='task-dev',
            )
            (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')
            resp = gateway.responder(
                self.root,
                '111',
                '/responder Q-ADV-0001 PENDIENTE: falta definir URL y puerto',
                {'111'},
            )
            self.assertIn('Respuesta recibida para Q-ADV-0001', resp)
            resueltas = motor.incorporar_respuestas(self.root)

        self.assertEqual(resueltas, [])
        fm = motor.frontmatter(motor.fichero_de(self.root, 'T-ADV-0101'))
        self.assertEqual((fm['status'], fm['pendiente_de']), ('blocked', 'humano'))
        q = motor.listar_preguntas(self.root)[0]
        self.assertEqual(q['estado'], 'pendiente')
        self.assertIn('falta definir URL y puerto', q.get('motivo_insuficiente', ''))
        self.assertTrue(any('sigue bloqueada' in txt.lower() and 'falta definir url y puerto' in txt.lower() for _, txt in enviados))

    def test_ca5_ca8_validacion_autorizacion_referencias_multiples_preguntas_y_duplicados(self):
        """CA-5, CA-8: Autorización, ambigüedad, inexistentes, cerradas, otro proyecto, múltiples preguntas y duplicados."""
        self.configurar_telegram()
        self.crear_tarea('T-ADV-0101', weight=10)
        self.crear_tarea('T-ADV-0102', weight=20)
        self.crear_tarea('T-ADV-0109', weight=90)
        self.git('add', '.')
        self.git('commit', '-qm', 'tareas')

        with patch.object(motor, 'avisar', return_value=True), redirect_stdout(io.StringIO()):
            motor.solicitar_intervencion(self.root, 'T-ADV-0101', '¿Proveedor OAuth?', contexto='Auth')
            motor.solicitar_intervencion(self.root, 'T-ADV-0102', '¿Motor de base de datos?', contexto='DB')
            q9 = motor.solicitar_intervencion(self.root, 'T-ADV-0109', '¿Región?', contexto='Cloud')
            (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')
            gateway.responder(self.root, '111', f'/responder {q9["id"]} eu-west-1', {'111'})
            motor.incorporar_respuestas(self.root)

        (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')
        autorizados = {'111', '222'}
        with patch.object(motor, 'cargar_cierre_version') as cierre:
            self.assertIsNone(gateway.responder(self.root, '999', '/cerrar v1.1 confirmo', autorizados))
            cierre.assert_not_called()

        self.assertIsNone(gateway.responder(self.root, '999', '/responder Q-ADV-0001 Sí', autorizados))
        self.assertEqual(motor.listar_preguntas(self.root, solo_pendientes=True)[0]['estado'], 'pendiente')

        r_ambigua = gateway.responder(self.root, '111', '/responder Usar interno', autorizados)
        self.assertIn('ambigua', r_ambigua.lower())
        self.assertIn('Q-ADV-0001', r_ambigua)
        self.assertIn('Q-ADV-0002', r_ambigua)

        r_inex = gateway.responder(self.root, '111', '/responder Q-ADV-9999 Usar interno', autorizados)
        self.assertIn('no existe', r_inex.lower())

        r_cerrada = gateway.responder(self.root, '111', '/responder Q-ADV-0003 Usar interno', autorizados)
        self.assertIn('cerrada', r_cerrada.lower())

        r_otro = gateway.responder(self.root, '111', '/responder Q-DOS-0001 Usar interno', autorizados)
        self.assertIn('no pertenece a este proyecto', r_otro.lower())

        r_q2 = gateway.responder(self.root, '111', '/responder Q-ADV-0002 Usar Postgres', autorizados)
        self.assertIn('Q-ADV-0002', r_q2)
        self.assertIn('T-ADV-0102', r_q2)
        por_id = {q['id']: q for q in motor.listar_preguntas(self.root)}
        self.assertEqual(por_id['Q-ADV-0001']['estado'], 'pendiente')
        self.assertIsNone(por_id['Q-ADV-0001'].get('respuesta_en_cola'))
        self.assertEqual(por_id['Q-ADV-0002']['respuesta_en_cola'], 'Usar Postgres')

        r_preg = gateway.responder(self.root, '111', '/preguntas', autorizados)
        r_est = gateway.responder(self.root, '111', '/estado', autorizados)
        self.assertIn('Q-ADV-0001', r_preg)
        self.assertIn('/responder Q-ADV-0001', r_preg)
        self.assertIn('Q-ADV-0001', r_est)
        for consulta in (r_preg, r_est):
            self.assertIn('T-ADV-0101', consulta)
            self.assertIn('¿Proveedor OAuth?', consulta)
            self.assertIn('/responder Q-ADV-0001', consulta)

        r_q1 = gateway.responder(self.root, '111', '/responder T-ADV-0101 Usar OAuth interno', autorizados)
        self.assertIn('Q-ADV-0001', r_q1)
        r_dup = gateway.responder(self.root, '111', '/responder Q-ADV-0001 Usar OAuth interno', autorizados)
        self.assertIn('duplicada', r_dup.lower())

        with patch.object(motor, 'avisar', return_value=True):
            incorporadas = motor.incorporar_respuestas(self.root)
        self.assertEqual([x['id'] for x in incorporadas], ['Q-ADV-0002', 'Q-ADV-0001'])
        self.assertEqual(autorizados, {'111', '222'})
        with patch.object(motor, 'cargar_cierre_version') as cierre:
            self.assertIsNone(gateway.responder(self.root, '999', '/cerrar v1.1 confirmo', autorizados))
            cierre.assert_not_called()

        (self.root / motor.PID).unlink(missing_ok=True)
        r_cerrar = gateway.responder(self.root, '111', '/cerrar v1.1 confirmo', autorizados)
        self.assertIn('No se completó el cierre', r_cerrar)

    def test_ca4_ca7_espera_sin_trabajo_elegible_reanudacion_y_parada_manual(self):
        """CA-4, CA-7: Distingue bloqueo de tarea vs global, espera cuando no hay elegibles y reanuda salvo parada manual."""
        self.configurar_telegram()
        self.crear_tarea('T-ADV-0101', weight=10, depende_de=[])
        self.crear_tarea('T-ADV-0102', status='completed', weight=20, depende_de=[])
        self.crear_tarea('T-ADV-0103', weight=30, depende_de=['T-ADV-0101'])
        rev_b = self.root / 'docs/review/code_reviews/T-ADV-0102-code-review.md'
        rev_b.parent.mkdir(parents=True, exist_ok=True)
        rev_b.write_text('**Veredicto:** APROBADO\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'B completada, A y C pendientes')

        with patch.object(motor, 'avisar', return_value=True), redirect_stdout(io.StringIO()):
            motor.solicitar_intervencion(
                self.root,
                'T-ADV-0101',
                '¿Usar proveedor OAuth interno o externo?',
                contexto='Sin valor por defecto seguro',
            )

        e = motor.estado(self.root, 'docs/requirements')
        self.assertEqual(e[0], 'PARAR')
        self.assertIn('Bloqueos en v1.1', e[1])
        self.assertIn('T-ADV-0101', e[1])
        self.assertIn('Q-ADV-0001', e[1])
        texto_parte = motor.parte(self.root)
        self.assertIn('Bloqueo de tarea', texto_parte)
        self.assertNotIn('Bloqueo global', texto_parte)

        lanzamientos_fondo = []
        with (
            patch.object(motor, 'en_fondo', side_effect=lambda r, argumentos=None: lanzamientos_fondo.append(r) or 0),
            patch.object(motor, 'avisar', return_value=True),
        ):
            r_auto = gateway.responder(
                self.root,
                '111',
                '/responder Q-ADV-0001 Usar proveedor OAuth interno',
                {'111'},
            )
        self.assertEqual(len(lanzamientos_fondo), 1)
        self.assertIn('reanudada', r_auto.lower())
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, 'T-ADV-0101'))['status'], 'planned')

        with patch.object(motor, 'avisar', return_value=True), redirect_stdout(io.StringIO()):
            motor.solicitar_intervencion(
                self.root,
                'T-ADV-0101',
                '¿Confirmar dominio secundario?',
                contexto='Dominio',
            )
        (self.root / motor.PARADA).write_text('parada manual', encoding='utf-8')
        lanzamientos_con_parada = []
        with (
            patch.object(motor, 'en_fondo', side_effect=lambda r, argumentos=None: lanzamientos_con_parada.append(r) or 0),
            patch.object(motor, 'avisar', return_value=True),
        ):
            r_parada = gateway.responder(
                self.root,
                '111',
                '/responder Q-ADV-0002 auth.ejemplo.es',
                {'111'},
            )
        self.assertEqual(len(lanzamientos_con_parada), 0)
        self.assertIn('parada manual', r_parada.lower())

    def test_ca8_recuperacion_tras_reinicio_y_recarga_sin_doble_reanudacion(self):
        """CA-8: Preguntas, respuestas y estado de incorporación sobreviven a reinicios y recargas sin reanudar dos veces."""
        self.configurar_telegram()
        self.crear_tarea('T-ADV-0101', weight=10)
        self.crear_tarea('T-ADV-0104', weight=40)
        self.git('add', '.')
        self.git('commit', '-qm', 'tareas 101 y 104')

        with patch.object(motor, 'avisar', return_value=True), redirect_stdout(io.StringIO()):
            motor.solicitar_intervencion(self.root, 'T-ADV-0101', '¿Pregunta 1?', contexto='Ctx 1')
            motor.solicitar_intervencion(self.root, 'T-ADV-0104', '¿Pregunta 2?', contexto='Ctx 2')

        (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')
        gateway.responder(self.root, '111', '/responder Q-ADV-0002 Respuesta 2', {'111'})
        with patch.object(motor, 'avisar', return_value=True):
            primera_inc = motor.incorporar_respuestas(self.root)
        self.assertEqual([q['id'] for q in primera_inc], ['Q-ADV-0002'])

        gateway.responder(self.root, '111', '/responder Q-ADV-0001 Respuesta 1', {'111'})

        motor_recargado = _cargar_modulo('orquestar_recargado', ROOT_REPO / 'skills' / 'orquestar' / 'orquestar.py')
        with patch.object(motor_recargado, 'avisar', return_value=True):
            segunda_inc = motor_recargado.incorporar_respuestas(self.root)
            tercera_inc = motor_recargado.incorporar_respuestas(self.root)

        self.assertEqual([q['id'] for q in segunda_inc], ['Q-ADV-0001'])
        self.assertEqual(tercera_inc, [])
        por_id = {q['id']: q for q in motor_recargado.listar_preguntas(self.root)}
        self.assertEqual(por_id['Q-ADV-0001']['estado'], 'incorporada')
        self.assertEqual(por_id['Q-ADV-0002']['estado'], 'incorporada')
        self.assertEqual(por_id['Q-ADV-0001']['pregunta'], '¿Pregunta 1?')
        self.assertEqual(por_id['Q-ADV-0001']['contexto'], 'Ctx 1')
        self.assertEqual(por_id['Q-ADV-0001']['respuesta'], 'Respuesta 1')
        self.assertEqual(por_id['Q-ADV-0002']['respuesta'], 'Respuesta 2')

    def test_espera_activa_recibe_por_gateway_y_continua_sin_relanzar(self):
        """La espera sin elegibles conserva el canal y retoma A y C sin otro lanzamiento."""
        self.configurar_telegram()
        self.crear_tarea('T-ADV-0101')
        self.crear_tarea('T-ADV-0103', depende_de=['T-ADV-0101'])
        self.git('add', '.')
        self.git('commit', '-qm', 'tareas')
        with patch.object(motor, 'avisar', return_value=True):
            motor.solicitar_intervencion(self.root, 'T-ADV-0101', '?Proveedor?', contexto='Auth')
        (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')
        pasos = []

        def durante_espera(segundos):
            self.assertIn('Q-ADV-0001', gateway.responder(self.root, '111', '/preguntas', {'111'}))
            self.assertIn('recibida', gateway.responder(self.root, '111', '/responder Q-ADV-0001 Interno', {'111'}))

        def completar(a, root, prompt, **kwargs):
            iid = kwargs['env']['ORQUESTAR_ID']
            pasos.append(iid)
            f = motor.fichero_de(root, iid)
            f.write_text(f.read_text(encoding='utf-8').replace('status: planned', 'status: completed'), encoding='utf-8')
            rev = root / f'docs/review/code_reviews/{iid}-code-review.md'
            rev.parent.mkdir(parents=True, exist_ok=True)
            rev.write_text('**Veredicto:** APROBADO\n', encoding='utf-8')
            (root / 'docs/review/versions/v1.1-arquitectura.md').write_text('APROBADO', encoding='utf-8')
            self.git('add', '.')
            self.git('commit', '-qm', 'completar')
            return 0, {}, ''

        with (patch.object(motor.time, 'sleep', side_effect=durante_espera),
              patch.object(motor, 'ejecutar', side_effect=completar),
              patch.object(motor, 'en_fondo') as fondo,
              patch.object(motor, 'avisar', return_value=True), redirect_stdout(io.StringIO())):
            motor.bucle(self.args_bucle(max_pasos=5, espera_max=1), self.root)
            fondo.assert_not_called()
        self.assertEqual(pasos, ['T-ADV-0101', 'T-ADV-0103'])


    def test_referencia_tarea_selecciona_pregunta_pendiente_actual(self):
        """Una pregunta cerrada anterior no oculta la pregunta actual de la misma tarea."""
        self.crear_tarea('T-ADV-0101')
        self.git('add', '.')
        self.git('commit', '-qm', 'tarea')
        with patch.object(motor, 'avisar', return_value=True):
            motor.solicitar_intervencion(self.root, 'T-ADV-0101', 'Proveedor inicial')
            (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')
            gateway.responder(self.root, '111', '/responder Q-ADV-0001 Interno', {'111'})
            motor.incorporar_respuestas(self.root)
            motor.solicitar_intervencion(self.root, 'T-ADV-0101', 'Dominio pendiente')
            respuesta = gateway.responder(self.root, '111', '/responder T-ADV-0101 auth.local', {'111'})
        self.assertIn('Q-ADV-0002', respuesta)
        self.assertEqual(motor.listar_preguntas(self.root)[1]['respuesta_en_cola'], 'auth.local')
        self.assertEqual(motor.listar_preguntas(self.root)[0]['respuesta'], 'Interno')

    def test_respuesta_se_incorpora_en_rama_de_la_tarea(self):
        """Una respuesta recibida con otra rama activa no modifica esa rama."""
        self.crear_tarea('T-ADV-0101')
        self.git('add', '.')
        self.git('commit', '-qm', 'tarea')
        with patch.object(motor, 'avisar', return_value=True):
            motor.solicitar_intervencion(self.root, 'T-ADV-0101', 'Proveedor')
            (self.root / motor.PID).write_text(str(os.getpid()), encoding='utf-8')
            gateway.responder(self.root, '111', '/responder Q-ADV-0001 Interno', {'111'})
            self.git('checkout', '-qb', 'release/v1.2')
            antes = self.git('rev-parse', 'release/v1.2')
            motor.incorporar_respuestas(self.root)
        self.assertEqual(self.git('rev-parse', 'release/v1.2'), antes)
        self.assertIn('status: planned', self.git('show', 'release/v1.1:docs/plan/tasks/T-ADV-0101.md'))
        self.assertEqual(motor.listar_preguntas(self.root)[0]['estado'], 'incorporada')

    def test_reinicio_completa_bloqueo_tras_publicar_registro(self):
        """Una interrupción antes de escribir la tarea no deja una pregunta sin bloqueo local."""
        self.crear_tarea('T-ADV-0101')
        self.git('add', '.')
        self.git('commit', '-qm', 'tarea')
        with patch.object(motor.intervencion, 'anotar', side_effect=OSError('corte simulado')):
            with self.assertRaises(OSError):
                motor.solicitar_intervencion(self.root, 'T-ADV-0101', 'Proveedor')
        persistidas = json.loads((self.root / 'orquestar_preguntas.json').read_text(encoding='utf-8'))
        self.assertEqual([(q['id'], q['pregunta']) for q in persistidas], [('Q-ADV-0001', 'Proveedor')])
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, 'T-ADV-0101'))['status'], 'planned')
        recargado = _cargar_modulo('orquestar_corte', ROOT_REPO / 'skills/orquestar/orquestar.py')
        with patch.object(recargado, 'avisar', return_value=True):
            recargado.incorporar_respuestas(self.root)
        fm = recargado.frontmatter(recargado.fichero_de(self.root, 'T-ADV-0101'))
        self.assertEqual((fm['status'], fm.get('pendiente_de')), ('blocked', 'humano'))
        self.assertEqual(len(motor.listar_preguntas(self.root, True)), 1)


    def test_bloqueo_incompleto_con_trabajo_ajeno_no_ejecuta_tarea(self):
        """La persistencia incompleta retiene la ejecución hasta poder guardar el bloqueo con seguridad."""
        self.crear_tarea('T-ADV-0101')
        self.git('add', '.')
        self.git('commit', '-qm', 'tarea')
        with patch.object(motor.intervencion, 'anotar', side_effect=OSError('corte')):
            with self.assertRaises(OSError):
                motor.solicitar_intervencion(self.root, 'T-ADV-0101', 'Proveedor')
        ajeno = self.root / 'trabajo_ajeno.txt'
        ajeno.write_text('conservar', encoding='utf-8')
        with (patch.object(motor, 'ejecutar', return_value=(0, {}, '')) as ejecutar,
              patch.object(motor, 'avisar', return_value=True), redirect_stdout(io.StringIO())):
            self.assertEqual(motor.bucle(self.args_bucle(max_pasos=1), self.root), 2)
            self.assertEqual(ejecutar.call_count, 0, 'La tarea no debe ejecutarse con un bloqueo sin persistir')
        self.assertEqual(ajeno.read_text(encoding='utf-8'), 'conservar')
        self.assertEqual(motor.listar_preguntas(self.root)[0]['estado'], 'pendiente')
        self.assertIn('Bloqueo global', motor.parte(self.root))


if __name__ == '__main__':
    unittest.main()
