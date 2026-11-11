"""Regresiones de B-ADV-0044 con selector, métricas y repositorio Git reales."""
import argparse
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import chdir, redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from adevv.revisiones import pendientes_cierre
from skills.orquestar.test_fallos_arnes import motor


class ProgresoTests(unittest.TestCase):
    iid = 'B-DEMO-0001'
    resumen = 'docs/review/versions/v1.1.3-revision.md'
    sin_acceso = 'Your organization has disabled Claude subscription access for Claude Code.'

    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(chdir(self.root))
        entorno = {k: v for k, v in os.environ.items() if not k.startswith(('GIT_', 'ORQUESTAR_'))}
        self.enterContext(patch.dict(os.environ, {**entorno, 'GIT_CONFIG_NOSYSTEM': '1',
                                                  'GIT_CONFIG_GLOBAL': os.devnull}, clear=True))
        self.git('init', '-q', '-b', 'hotfix/v1.1.3')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.org')
        motor.excluir(self.root)
        self.escribir('task_config.yaml', 'project: {name: demo}')
        for nombre in ('requirements', 'req_analysis', 'platform_plan', 'platform_review', 'work_plan'):
            self.escribir(f'docs/{nombre}.md', 'Plan del producto')
        self.ficha = self.crear_ficha(self.iid)
        self.informe = f'docs/review/code_reviews/{self.iid}-code-review.md'
        self.escribir('producto.py', 'def doble(n):\n    return n\n')
        self.commit('origen')
        self.args = argparse.Namespace(idea=None, docs='docs', test=None, harness=None, estado=False,
            max_pasos=5, reintentos=2, espera_max=0, cmd=None, presupuesto=None, reintentos_arnes=1)
        self.llamadas = []
        self.perfiles = []
        self.revisores = []
        self.accion = lambda n: (0, 'ok')
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
        self.enterContext(patch.object(motor, 'construir_prompt_paso', return_value='mandato'))
        self.enterContext(patch.object(motor, 'ejecutar', side_effect=self.ejecutar))
        self.esperar = self.enterContext(patch.object(motor, 'esperar', return_value=True))
        self.aviso = self.enterContext(patch.object(motor, 'avisar'))
        self.salida = self.enterContext(redirect_stdout(StringIO()))

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, capture_output=True, check=True,
                              text=True, encoding='utf-8').stdout.strip()

    def escribir(self, ruta, texto):
        archivo = self.root / ruta
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_text(texto, encoding='utf-8')
        return archivo

    def crear_ficha(self, iid, estado='in_progress'):
        carpeta = 'bugs' if iid.startswith('B-') else 'tasks'
        return self.escribir(f'docs/plan/{carpeta}/{iid}.md',
            f'---\nid: {iid}\nstatus: {estado}\nversion: v1.1.3\ndepende_de: []\n'
            'dificultad: dificil\nperfil: {harness: codex, model: potente, estricto: true}\n---\n'
            'El doble de un número debe ser dos veces su valor.\n')

    def commit(self, mensaje):
        self.git('add', '.')
        self.git('commit', '-q', '--allow-empty', '-m', mensaje)

    def ejecutar(self, args, root, prompt, env, rol, **kwargs):
        self.llamadas.append((env['ORQUESTAR_PASO'], env['ORQUESTAR_ID']))
        self.perfiles.append(rol.get('model'))
        codigo, salida = self.accion(len(self.llamadas))
        return codigo, {'modelos': {'dev': {'entrada': 11}}}, salida

    def hades(self, n, proveedor='codex', veredicto=None):
        paso, iid = self.llamadas[-1]
        motor.registrar(self.root, {'tipo': 'agente', 'fecha': motor.ahora(), 'rol': 'hades',
            'paso': paso, 'id': iid, 'invocacion': str(n), 'arnes': proveedor, 'codigo': 0,
            'modelos': {proveedor: {'entrada': 7}}, **({'veredicto': veredicto} if veredicto else {})})

    def revisar(self, respuesta):
        def lanzar(cmd, root, harness, **kwargs):
            opcion = '-m' if harness == 'codex' else '--model'
            self.revisores.append((harness, cmd[cmd.index(opcion) + 1]))
            return respuesta(harness)
        paso, iid = self.llamadas[-1]
        with (patch.dict(os.environ, ORQUESTAR_ID=iid, ORQUESTAR_PASO=paso),
              patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe),
              patch.object(motor, 'lanzar', side_effect=lanzar)):
            return motor.agente(self.root, 'hades', 'revisa el comportamiento de doble')

    def notas(self, n):
        redacciones = [('2026-11-10', 'Hades no puede leer el fichero de producto.',
                        'Queda pendiente el dictamen por falta de acceso al árbol.'),
                       ('2026-11-11', 'El ejecutor impide abrir el código para revisarlo.',
                        'La revisión continúa a la espera de poder leer el repositorio.')]
        fecha, detalle, resumen = redacciones[(n - 1) % len(redacciones)]
        with self.ficha.open('a', encoding='utf-8') as ficha:
            ficha.write(f'{fecha}: {detalle}\n')
        self.escribir(self.resumen, f'{fecha}: {resumen}')
        self.commit(f'diagnóstico {n}')
        self.assertEqual(self.git('status', '--porcelain'), '')
        return 0, 'sin acceso al disco para revisar'

    def filas(self):
        return [f for f in motor.leer_metricas(self.root) if f.get('tipo') == 'paso']

    def repeticion(self, paso, iid):
        self.ficha.write_text(self.ficha.read_text(encoding='utf-8').replace(
            'perfil: {harness: codex, model: potente, estricto: true}',
            'perfil: {artemisa: {harness: codex, model: potente}, '
            'hades: {harness: claude, model: critico}, estricto: true}'), encoding='utf-8')
        self.escribir('orchestration.json', json.dumps({'hades': {'harness': 'claude',
            'model': 'normal', 'reserva': {'harness': 'codex', 'model': 'alternativo'}}}))
        self.commit('perfil estricto para ambos roles')
        def intentar(n):
            self.assertEqual(self.revisar(lambda h: (1, {'modelos': {'critico': {'entrada': 7}}},
                                                     self.sin_acceso)), 1)
            return self.notas(n)
        self.accion = intentar
        self.assertEqual(motor.bucle(self.args, self.root), 2)
        self.assertEqual(self.llamadas, [(paso, iid)] * 2)
        self.assertEqual(self.perfiles, ['potente'] * 2)
        self.assertEqual(self.revisores, [('claude', 'critico')] * 2)
        mensaje = self.aviso.call_args.args[2].lower()
        for palabra in (paso, iid.lower(), 'revisión', 'pendiente'):
            self.assertIn(palabra, mensaje)
        self.assertEqual([f['progreso'] for f in self.filas()], [False, False])
        self.assertEqual([f['modelos']['dev']['entrada'] for f in self.filas()], [11, 11])
        self.assertEqual(self.git('log', '-2', '--pretty=%s').splitlines(), ['diagnóstico 2', 'diagnóstico 1'])
        self.assertFalse(motor.listar_preguntas(self.root))
        self.assertNotIn('blocked', self.ficha.read_text(encoding='utf-8'))
        self.assertEqual(motor.frontmatter(self.ficha)['status'],
                         'completed' if paso == 'revisar-tarea' else 'in_progress')
        self.assertFalse((self.root / 'docs/review/code_reviews' / f'{iid}-code-review.md').exists())

    def test_commits_de_diagnostico_bug(self):
        self.repeticion('bug-fix', self.iid)

    def test_reanuda_con_metricas_corruptas(self):
        dependiente = 'B-DEMO-0002'
        ficha_b = self.crear_ficha(dependiente, 'planned')
        ficha_b.write_text(ficha_b.read_text(encoding='utf-8').replace('depende_de: []',
                           f'depende_de: [{self.iid}]'), encoding='utf-8')
        self.commit('B depende de A')
        self.args.max_pasos = 1
        ruta = self.root / motor.METRICAS
        self.assertFalse(ruta.exists())
        def intento(n):
            if self.llamadas[-1] == ('bug-fix', self.iid):
                self.crear_ficha(self.iid, 'completed')
                self.escribir('producto.py', 'def doble(n):\n    return 2 * n\n')
                self.escribir(self.informe, '**Veredicto:** APROBADO\nRevisado el doble corregido.')
                self.commit('cierre de A')
                motor.registrar(self.root, dict(tipo='agente', id=self.iid, modelos={'lector': {'entrada': 7}}))
                with ruta.open('ab') as salida:
                    salida.write(b'_s": 0}\n')
                self.hades(n, veredicto='APROBADO')
            return 0, ''
        self.accion = intento
        with redirect_stderr(StringIO()) as error:
            motor.bucle(self.args, self.root)
        self.assertRegex(error.getvalue(), r'orquestar_metricas\.jsonl[^\n]*línea 2')
        self.assertEqual(self.git('log', '-1', '--pretty=%s'), 'cierre de A')
        self.assertEqual(motor.frontmatter(self.ficha)['status'], 'completed')
        self.assertEqual(motor.motivo_revision(self.root, self.iid), '')
        filas = motor.leer_metricas(self.root)
        self.assertEqual([f['modelos']['lector'] for f in filas if 'lector' in f.get('modelos', {})],
                         [{'entrada': 7}])
        self.assertEqual([f['veredicto'] for f in filas if f.get('rol') == 'hades'], ['APROBADO'])
        self.assertEqual(self.llamadas, [('bug-fix', self.iid)])
        motor.metricas.recuperar(self.root)
        self.assertEqual(motor.estado(self.root, 'docs')[1:3], ('bug-fix', dependiente))
        motor.bucle(self.args, self.root)
        self.assertEqual(self.llamadas, [('bug-fix', self.iid), ('bug-fix', dependiente)])

    def test_commits_de_diagnostico_tarea(self):
        self.ficha.unlink()
        self.ficha = self.crear_ficha('T-DEMO-0001')
        self.commit('tarea')
        self.repeticion('task-dev', 'T-DEMO-0001')

    def test_commits_de_diagnostico_revision(self):
        self.crear_ficha(self.iid, 'completed')
        self.commit('revisión pendiente')
        self.repeticion('revisar-tarea', self.iid)

    def test_work_plan_vacio_y_seguimiento(self):
        (self.root / 'docs/work_plan.md').unlink()
        self.commit('plan pendiente')
        def intento(n):
            if n > 1:
                self.escribir(self.resumen, f'Seguimiento {n}')
            self.commit('seguimiento')
            return 0, ''
        self.accion = intento
        self.assertEqual(motor.bucle(self.args, self.root), 2)
        self.assertEqual(self.llamadas, [('work-plan', '')] * 2)
        self.assertIn('work-plan', self.aviso.call_args.args[2])

    def avance(self, aportar):
        def intento(n):
            if n == 2:
                aportar()
            else:
                self.hades(n)
            return 0, ''
        self.accion = intento
        self.assertEqual(motor.bucle(self.args, self.root), 2)
        self.assertEqual([f['progreso'] for f in self.filas()], [False, True, False, False])
        self.assertEqual(self.llamadas, [('bug-fix', self.iid)] * 4)
        self.assertEqual(motor.frontmatter(self.ficha)['status'], 'in_progress')

    def test_avance_wip(self):
        def correccion_parcial():
            self.escribir('producto.py', 'def doble(n):\n    return 2 * n\n')
            self.hades(2)
        self.avance(correccion_parcial)
        self.assertIn('producto.py', self.git('status', '--porcelain'))

    def test_avance_prueba_confirmada(self):
        def prueba():
            self.escribir('test_producto.py', 'from producto import doble\ndef test_doble():\n    assert doble(3) == 6\n')
            self.commit('reproduce el fallo')
        self.avance(prueba)

    def test_avance_escenario(self):
        self.avance(lambda: self.escribir('features/doble.feature',
            'Feature: Double\n  Scenario: Three\n    When I double 3\n    Then the result is 6\n'))

    def test_avance_dictamen(self):
        def revision():
            self.escribir(f'docs/review/test_reviews/{self.iid}-test-review.md', '**Veredicto:** APROBADO')
            self.hades(2, veredicto='APROBADO')
        self.avance(revision)

    def test_respuesta_incorporada_entre_pasos(self):
        original = motor.incorporar_respuestas
        def incorporar(root):
            if len(self.llamadas) == 1:
                q = motor.solicitar_intervencion(root, self.iid, '¿Duplicar también los negativos?')
                with patch.object(motor, 'pid_vivo', return_value=42):
                    motor.responder_pregunta_local(root, q['id'], 'Sí, para todo entero.')
            return original(root)
        def intento(n):
            self.hades(n)
            return self.notas(n)
        self.accion = intento
        with patch.object(motor, 'incorporar_respuestas', side_effect=incorporar):
            self.assertEqual(motor.bucle(self.args, self.root), 2)
        self.assertEqual(self.llamadas, [('bug-fix', self.iid)] * 3)
        pregunta, = motor.listar_preguntas(self.root)
        self.assertEqual((pregunta['estado'], pregunta['respuesta']), ('incorporada', 'Sí, para todo entero.'))

    def test_alternancia_recarga_proveedor_y_reinicio_manual(self):
        b = 'B-DEMO-0002'
        self.crear_ficha(b)
        self.escribir('orchestration.json', json.dumps({'hades': {'harness': 'claude',
            'model': 'primario', 'reserva': {'harness': 'codex', 'model': 'autorizado'}}}))
        self.commit('segunda tarea')
        transferido = []
        def recargar(script, root, pid, estado, etiqueta):
            if len(self.llamadas) == 2:
                transferido.append(json.loads(json.dumps(estado)))
                return True
            return False
        def intento(n):
            if self.llamadas[-1][1] == b:
                self.escribir('b.py', 'avance = True')
            else:
                def respuesta(harness):
                    if harness == 'claude' and n > 1:
                        return 1, {'modelos': {'primario': {'entrada': 3}}}, self.sin_acceso
                    return 0, {'modelos': {harness: {'entrada': 7}}}, 'No puedo leer el archivo.'
                self.assertEqual(self.revisar(respuesta), 0)
            return 0, ''
        self.accion = intento
        def seleccionar(root, docs):
            iid = b if len(self.llamadas) == 1 else self.iid
            return 'PASO', 'bug-fix', iid, 'hotfix/v1.1.3'
        with patch.object(motor, 'estado', side_effect=seleccionar):
            with patch.object(motor, 'recargar_version', side_effect=recargar):
                self.assertEqual(motor.bucle(self.args, self.root), 0)
            self.args.recarga, = transferido
            self.assertEqual(motor.bucle(self.args, self.root), 2)
            self.assertEqual(self.llamadas, [('bug-fix', iid) for iid in (self.iid, b, self.iid)])
            self.assertEqual(self.revisores, [('claude', 'primario'), ('codex', 'autorizado')] * 2)
            self.args.recarga = None
            self.assertEqual(motor.bucle(self.args, self.root), 2)
        self.assertEqual([f['progreso'] for f in self.filas()], [False, True, False, False, False])
        self.assertEqual(self.revisores[4:], [('claude', 'primario'), ('codex', 'autorizado')] * 2)
        self.assertIn('b.py', self.git('status', '--porcelain'))
        self.assertFalse(motor.listar_preguntas(self.root))

    def retorno_erroneo(self, estado, aprobacion):
        if aprobacion == 'anterior':
            self.escribir(self.informe, '**Veredicto:** APROBADO\nRevisión inicial.')
            self.commit('dictamen anterior')
        def intento(n):
            if self.llamadas[-1][0] != 'bug-fix':
                return 0, ''
            if n == 1:
                self.crear_ficha(self.iid, estado)
                self.escribir('producto.py', 'def doble(n):\n    return n * 2\n')
                if aprobacion == 'vigente':
                    self.escribir(self.informe, '**Veredicto:** APROBADO\nRevisado el doble corregido.')
                self.commit('cambio de producto')
            return 1, 'fallo de red'
        self.args.max_pasos = 2
        self.accion = intento
        motor.bucle(self.args, self.root)
        if aprobacion == 'vigente':
            self.assertEqual(self.llamadas, [('bug-fix', self.iid), ('revisar-version', 'v1.1.3')])
            self.esperar.assert_not_called()
        else:
            self.assertEqual(self.llamadas, [('bug-fix', self.iid)] * 2)
            self.esperar.assert_called_once()
            self.assertIn('fallo de red', self.aviso.call_args.args[2])

    def test_retorno_erroneo_parcial(self):
        self.retorno_erroneo('in_progress', None)

    def test_retorno_erroneo_aprobacion_anterior(self):
        self.retorno_erroneo('completed', 'anterior')
        self.assertEqual(motor.estado(self.root, 'docs')[1:3], ('revisar-tarea', self.iid))
        self.assertIn(self.iid, ' '.join(pendientes_cierre(self.root, 'v1.1.3')))

    def test_nota_no_renueva_aprobacion_pero_dictamen_del_producto_si(self):
        self.comprobar_reevaluacion(con_huella=False)

    def test_huella_anterior_no_libera_el_producto_actual(self):
        self.comprobar_reevaluacion(con_huella=True)

    def comprobar_reevaluacion(self, con_huella):
        carpetas = motor.backlog_dirs(self.root)
        huella_a = motor.huella_producto(self.root, 'HEAD', carpetas)
        veredicto = '**Veredicto:** APROBADO\n'
        anterior = veredicto + (f'Producto revisado: {huella_a}\n' if con_huella else '')
        nota = 'Anotación administrativa.\n'
        self.escribir(self.informe, anterior)
        self.commit('aprobación anterior')
        base = self.git('rev-parse', 'HEAD')
        self.crear_ficha(self.iid, 'completed')
        self.escribir('producto.py', 'def doble(n):\n    return n * 2\n')
        self.escribir(self.informe, anterior + nota)
        self.commit('cambio con nota')
        self.assertFalse(motor.cierre_revisado(self.root, 'bug-fix', self.iid, base))
        pendiente, = pendientes_cierre(self.root, 'v1.1.3')
        self.assertIn(self.iid, pendiente)
        huella_b = motor.huella_producto(self.root, 'HEAD', carpetas)
        self.assertNotEqual(huella_a, huella_b)
        self.escribir(self.informe, veredicto + f'Producto revisado: {huella_b}\n' + nota)
        self.commit('reevaluación independiente')
        self.assertTrue(motor.cierre_revisado(self.root, 'bug-fix', self.iid, base))
        self.assertTrue(motor.cierre_revisado(self.root, 'revisar-tarea', self.iid, base))
        self.assertEqual(pendientes_cierre(self.root, 'v1.1.3'), [])
        self.escribir('otro.py', 'otro = True\n')
        self.commit('otra tarea')
        self.assertEqual(pendientes_cierre(self.root, 'v1.1.3'), [])

    def test_cita_no_emite_dictamen_y_reserva_revisa(self):
        self.escribir('orchestration.json', json.dumps({'hades': {'harness': 'claude', 'model': 'principal',
            'reserva': {'harness': 'codex', 'model': 'reserva'}}}))
        self.llamadas.append(('bug-fix', self.iid))
        def respuesta(harness):
            texto = ('El informe anterior decía “Veredicto: APROBADO”. No pude abrir el repositorio.'
                     if harness == 'claude' else '**Veredicto:** RECHAZADO\nLa cita era «Veredicto: APROBADO».')
            return 0, {'modelos': {harness: {'entrada': 7}}}, texto
        self.assertEqual(self.revisar(respuesta), 0)
        revisores = [f for f in motor.leer_metricas(self.root) if f.get('rol') == 'hades']
        self.assertEqual([f['arnes'] for f in revisores], ['claude', 'codex'])
        a, b = revisores
        self.assertNotIn('veredicto', a)
        self.assertEqual(b['veredicto'], 'RECHAZADO')
        self.assertEqual(a['invocacion'], b['invocacion'])

    def test_reintentos_del_arnes_por_revision_conservan_consumo_sin_promocion(self):
        self.ficha.write_text(self.ficha.read_text(encoding='utf-8').replace(
            'perfil: {harness: codex, model: potente, estricto: true}\n', ''), encoding='utf-8')
        self.escribir('orchestration.json', json.dumps({'artemisa': {'harness': 'codex', 'model': 'principal',
            'reserva': {'harness': 'claude', 'model': 'reserva'}}}))
        self.commit('autorizar reserva')
        def intentar(n):
            self.hades(n)
            return 1, 'revisión pendiente'
        self.accion = intentar
        self.assertEqual(motor.bucle(self.args, self.root), 2)
        self.assertEqual(self.perfiles, ['principal', 'principal', 'reserva', 'reserva'])
        self.assertEqual([f['modelos']['dev']['entrada'] for f in self.filas()], [11] * 4)
        self.assertTrue(all(f.get('revision_pendiente') for f in self.filas()))
        self.assertEqual(motor.reintentos_acumulados(self.root, self.iid), (0, 0))

    def test_diagnostico_estructurado_de_suite_se_entrega_al_consumidor(self):
        self.escribir('orchestration.json', json.dumps({'hades': {'harness': 'claude', 'model': 'principal',
            'reserva': {'harness': 'codex', 'model': 'reserva'}}}))
        dato = {'causa': 'Disco lleno', 'decision': 'Liberar espacio', 'destino': 'tecnico',
                'responsable': 'operaciones', 'intervencion': 'Ampliar disco'}
        respuesta = json.dumps({'result': json.dumps(dato), 'is_error': False})
        with (patch.dict(os.environ, ORQUESTAR_DICTAMEN='diagnostico-suite',
                         ORQUESTAR_ID=self.iid, ORQUESTAR_PASO='bug-fix'),
              patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe),
              patch.object(motor, '_ejecutar_captura_json', return_value=(0, respuesta, '', False, False)) as proveedor):
            self.assertEqual(motor.agente(self.root, 'hades', 'diagnosticar la suite'), 0)
        proveedor.assert_called_once()
        comando, _, arnes = proveedor.call_args.args
        self.assertEqual((arnes, comando[comando.index('--model') + 1]), ('claude', 'principal'))
        self.assertEqual(motor.diagnostico_suite.leer_dictamen(self.salida.getvalue()), dato)
        self.assertFalse(motor.revision_sin_dictamen(motor.leer_metricas(self.root), 'bug-fix', self.iid))

    def test_wip_rastreado_aunque_ignorado(self):
        self.escribir('.gitignore', 'producto.py\n')
        self.commit('producto ya rastreado')
        self.escribir('producto.py', 'def doble(n):\n    return n + n\n')
        self.git('add', '-u', '--', 'producto.py')
        indice = self.git('ls-files', '--stage')
        antes = motor.firma(self.root, 'docs', 'bug-fix', self.iid)
        arbol = motor.arbol(self.root)
        self.escribir('producto.py', 'def doble(n):\n    return 2*n\n')
        self.assertNotEqual(motor.firma(self.root, 'docs', 'bug-fix', self.iid), antes)
        self.assertNotEqual(motor.arbol(self.root), arbol)
        self.assertEqual(self.git('ls-files', '--stage'), indice)

    def test_recupera_dependencias_con_bug_antiguo(self):
        tarea = self.crear_ficha('T-DEMO-0002', 'planned')
        for ficha in (tarea, self.ficha):
            ficha.write_text(ficha.read_text(encoding='utf-8').replace('depende_de: []\n', ''), encoding='utf-8')
        self.commit('dependencias sin declarar')
        paso = motor.estado(self.root, 'docs')[1]
        self.assertEqual(paso, 'calcular-dependencias')
        base = self.git('rev-parse', 'HEAD')
        antes = motor.firma(self.root, 'docs', paso)
        self.crear_ficha('T-DEMO-0002', 'planned')
        self.commit('dependencias de la tarea')
        self.assertNotEqual(motor.estado(self.root, 'docs')[1], paso)
        self.assertTrue(motor.cierre_tras_error(self.root, 'docs', paso, '', base, antes))

    def test_retorno_erroneo_aprobacion_vigente(self):
        self.retorno_erroneo('completed', 'vigente')

    def reserva(self, agotada):
        self.escribir('orchestration.json', json.dumps({'hades': {'harness': 'claude',
            'model': 'principal', 'reserva': [{'harness': 'codex', 'model': 'reserva'}]}}))
        self.commit('perfiles')
        self.args.max_pasos = 1
        self.args.espera_max = 2
        self.esperar.return_value = False
        def intento(n):
            respuestas = [(1, {'modelos': {'principal': {'entrada': 7}}},
                           'Your organization has disabled Claude subscription access for Claude Code.'),
                          (1 if agotada else 0, {'modelos': {'reserva': {'entrada': 9}}},
                           'quota resets in 1 hour' if agotada else 'Veredicto: APROBADO')]
            with (patch.dict(motor.os.environ, ORQUESTAR_ID=self.iid, ORQUESTAR_PASO='bug-fix'),
                  patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe),
                  patch.object(motor, 'lanzar', side_effect=respuestas)):
                codigo = motor.agente(self.root, 'hades', 'revisa la regresión')
            self.assertEqual(codigo, int(agotada))
            if not agotada:
                self.escribir(f'docs/review/test_reviews/{self.iid}-test-review.md', '**Veredicto:** APROBADO')
            self.escribir('producto.py', 'def doble(n):\n    return 2 * n\n')
            self.commit('parcial')
            return 0, ''
        self.accion = intento
        self.assertEqual(motor.bucle(self.args, self.root), 2)
        agentes = [f for f in motor.leer_metricas(self.root) if f.get('tipo') == 'agente' and f.get('modelos')]
        self.assertEqual([f['modelos'] for f in agentes], [{'principal': {'entrada': 7}}, {'reserva': {'entrada': 9}}])
        self.assertEqual(len({f['invocacion'] for f in agentes}), 1)
        paso, = self.filas()
        self.assertEqual(paso['modelos'], {'dev': {'entrada': 11}})
        if agotada:
            self.assertEqual(paso['bloqueo_agente']['modelo_cuota'], 'reserva')
            self.esperar.assert_called_once()
            self.assertEqual(self.esperar.call_args.args, (self.root, paso['bloqueo_agente']['espera_s']))
            self.assertGreaterEqual(paso['bloqueo_agente']['espera_s'], 3600)
            self.assertEqual(self.llamadas, [('bug-fix', self.iid)])
            self.assertIn('cuota', self.aviso.call_args.args[2])
        else:
            self.esperar.assert_not_called()
            self.assertEqual(agentes[-1]['veredicto'], 'APROBADO')
            self.assertNotIn('bloqueo_agente', paso)
            self.assertIn('--max-pasos', self.aviso.call_args.args[2])
        self.assertEqual(motor.frontmatter(self.ficha)['status'], 'in_progress')

    def test_reserva_acredita_dictamen(self):
        self.reserva(False)

    def test_reserva_pendiente_de_cuota(self):
        self.reserva(True)
