"""Recorridos de T-ADV-0035 por el bucle, la CLI y el gateway con proveedores simulados."""

import io
import json
import os
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path
import unittest
from unittest.mock import patch

from skills.orquestar import test_progreso as soporte
from tests.test_telegram_gateway import gateway


motor = soporte.motor
PROMPT = motor.construir_prompt_paso
A, B, C = ('T-DEMO-0001', 'T-DEMO-0002', 'T-DEMO-0003')
DENEGADO = 'Your organization has disabled Claude subscription access for Claude Code.'


class DecisionItemTests(unittest.TestCase):
    iid = A
    escribir = soporte.ProgresoTests.escribir
    crear_ficha = soporte.ProgresoTests.crear_ficha
    commit = soporte.ProgresoTests.commit
    git = soporte.ProgresoTests.git
    filas = soporte.ProgresoTests.filas

    def setUp(self):
        soporte.ProgresoTests.setUp(self)
        self.args.docs = 'docs/requirements'
        for nombre in ('requirements', 'req_analysis', 'platform_plan', 'platform_review', 'work_plan'):
            self.escribir(f'{self.args.docs}/{nombre}.md', 'Plan del producto')
        motor.construir_prompt_paso.side_effect = PROMPT
        self.enterContext(patch.object(motor, 'get_active_version_dir', return_value=Path(motor.__file__).resolve().parents[2]))
        self.enterContext(patch.object(gateway, 'motor', motor))
        self.enterContext(patch.object(motor, 'telegram', return_value=('bot', ['111'], ['respuesta'])))
        self.enterContext(patch.object(motor, 'buscar_sesion_agente', return_value=None))
        self.executable = self.enterContext(patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe))
        self.proveedor = self.enterContext(patch.object(motor, 'lanzar'))
        self.escribir('orchestration.json', json.dumps({'hades': {'harness': 'claude', 'model': 'principal',
            'reserva': [{'harness': 'claude', 'model': 'reserva'}]}}))
        self.commit('requisitos y perfiles')
        self.args.max_pasos = 1
        self.prompts = []

    def ejecutar(self, args, root, prompt, env, rol, **kwargs):
        self.llamadas.append((env['ORQUESTAR_PASO'], env['ORQUESTAR_ID']))
        self.prompts.append(prompt)
        with patch.dict(os.environ, env, clear=True):
            return 0, {'modelos': {'dev': {'entrada': 10}}}, self.accion()

    def paso(self, accion):
        self.accion = accion
        motor.bucle(self.args, self.root)

    def cli(self, *args):
        stream = io.StringIO()
        stream.reconfigure = lambda **kw: None
        with patch.object(sys, 'argv', ['orquestar', *args]), redirect_stdout(stream):
            with patch.object(sys, 'stderr', stream):
                motor.main()
        return stream.getvalue()

    def canales(self, consulta, *fragmentos):
        respuestas = (self.cli('--' + consulta), gateway.responder(self.root, '111', '/' + consulta, {'111'}))
        for respuesta in respuestas:
            for fragmento in fragmentos:
                self.assertIn(fragmento.casefold(), respuesta.casefold(), respuesta)
        return respuestas

    def decision(self, **datos):
        return 'DECISION_ITEM ' + json.dumps(datos, ensure_ascii=False)

    def asignacion(self, destino, mandato, condicion, siguiente):
        conflicto = 'Los criterios requieren y prohíben el mismo catálogo.'
        self.paso(lambda: self.decision(clave='catalogos', impedimento=conflicto))
        self.canales('preguntas', 'Sin preguntas pendientes')
        self.paso(lambda: self.decision(clave='catalogos', destino=destino, mandato=mandato, condicion=condicion))
        self.assertIn('aclar', self.prompts[-1].lower())
        self.assertIn(conflicto, self.prompts[-1])
        self.canales('estado', A, destino, siguiente)
        self.canales('preguntas', 'Sin preguntas pendientes')
        self.paso(lambda: 'Recibido')
        self.assertEqual(self.llamadas[-1], (siguiente, A))
        for esperado in (mandato, condicion):
            self.assertIn(esperado, self.prompts[-1])

    def test_aclarar_conflicto_para_el_especificador(self):
        self.asignacion('especificador', 'reconciliar los dos criterios',
                        'un escenario resuelve el choque', 'especificar')

    def test_aclarar_conflicto_para_artemisa(self):
        self.asignacion('artemisa', 'reproducir la divergencia en CLI',
                        'una prueba reproduce el fallo', 'task-dev')

    def test_decision_humana_conserva_referencia_y_respuesta_al_relanzar(self):
        pregunta = '¿Qué catálogo debe usar A en producción, norte o sur?'
        def elegir(texto):
            return self.decision(clave='catalogo-produccion', destino='humano', pregunta=texto,
                                 impedimento='Solo el propietario puede elegir el catálogo de producción.')
        self.canales('preguntas', 'Sin preguntas pendientes')
        self.paso(lambda: elegir(pregunta))
        self.canales('estado', A, pregunta)
        cli, tg = self.canales('preguntas', A, pregunta)
        ref = re.findall(r'Q-[A-Z]+-\d+', cli)[0]
        self.assertIn(ref, tg)
        with patch.object(motor, 'pid_vivo', return_value=123):
            self.assertIn('recibida', self.cli('--responder', ref, 'catálogo norte'))
        self.paso(lambda: elegir('¿Norte o sur para el catálogo de producción?'))
        self.assertIn('catálogo norte', self.prompts[-1])
        self.canales('preguntas', ref, pregunta, A, 'catálogo norte')
        self.assertEqual([q['id'] for q in motor.listar_preguntas(self.root)], [ref])
        for estado in self.canales('estado', 'task-dev', A):
            self.assertNotIn('Bloqueo de tarea', estado)
        avisos = [c for c in self.aviso.call_args_list if pregunta in str(c) and '/responder' in str(c)]
        self.assertEqual(len(avisos), 1)

    def preparar_dependencias(self):
        self.crear_ficha(B, 'planned')
        c = self.crear_ficha(C, 'planned')
        c.write_text(c.read_text(encoding='utf-8').replace('depende_de: []', f'depende_de: [{A}]'), encoding='utf-8')
        self.commit('B independiente y C depende de A')

    def completar_b(self):
        self.assertEqual(self.llamadas[-1], ('task-dev', B))
        self.assertFalse((self.root / 'producto-a.txt').exists(), 'B ha recibido el WIP de A')
        self.crear_ficha(B, 'completed')
        self.escribir(f'docs/review/code_reviews/{B}-code-review.md',
                      'Veredicto: N/A\nMotivo: sin cambios de código en la tarea B.\n')
        self.commit('B completada')
        return 'B terminada'

    def revisar(self):
        with patch.dict(os.environ, ORQUESTAR_REVISION='test'):
            return motor.agente(self.root, 'hades', 'revisar los casos límite de A')

    def espera(self, causa, situacion, condicion):
        self.preparar_dependencias()
        wip = self.root / 'producto-a.txt'
        errores = {'suscripcion': DENEGADO, 'cuota': 'out of credits'}
        numero = 0

        def intento():
            nonlocal numero
            numero += 1
            if numero == 1:
                wip.write_text('trabajo pendiente de A', encoding='utf-8')
            else:
                self.assertEqual(wip.read_text(encoding='utf-8'), 'trabajo pendiente de A')
            if causa == 'servicio':
                return self.decision(clave='servicio-pruebas', destino='espera_tecnica', revision='test',
                    impedimento=('servicio de pruebas externo caído' if numero == 1 else 'sigue inaccesible'),
                    condicion=condicion)
            if causa == 'ejecutable':
                self.executable.side_effect = lambda exe: None if exe == 'claude' else exe
            else:
                self.proveedor.return_value = (1, {}, errores[causa] + ('' if numero == 1 else ' Detalle adicional.'))
            self.assertEqual(self.revisar(), 1)
            return 'La revisión sigue pendiente.'

        def trabajar():
            if len(self.llamadas) == 1:
                return intento()
            for estado in self.canales('estado', A, B, situacion, 'test', condicion):
                self.assertRegex(estado, r'task-dev\s+' + B)
            self.canales('preguntas', 'Sin preguntas pendientes')
            return self.completar_b()

        self.args.max_pasos = 2
        self.paso(trabajar)
        self.args.max_pasos = 1
        self.assertEqual(self.llamadas, [('task-dev', A), ('task-dev', B)])
        if causa == 'suscripcion':
            self.assertEqual([c.args[0][c.args[0].index('--model') + 1] for c in self.proveedor.call_args_list],
                             ['principal', 'reserva'])
        self.assertEqual(motor.frontmatter(motor.fichero_de(self.root, C))['status'], 'planned')
        if causa == 'cuota':
            motor.reset_cuotas(self.root)
        if causa == 'ejecutable':
            self.executable.side_effect = lambda exe: exe
        self.paso(intento)
        self.assertEqual(self.llamadas[-1], ('task-dev', A))
        self.assertEqual(numero, 2)
        self.assertFalse(self.filas()[-1]['progreso'])
        self.canales('estado', A, situacion, condicion)
        self.canales('preguntas', 'Sin preguntas pendientes')
        motor.reset_cuotas(self.root)
        self.executable.side_effect = lambda exe: exe
        self.proveedor.side_effect = ([(1, {}, DENEGADO), (0, {}, 'Veredicto: APROBADO')]
                                     if causa == 'suscripcion' else [(0, {}, 'Veredicto: APROBADO')])
        def recuperada():
            self.assertEqual(wip.read_text(encoding='utf-8'), 'trabajo pendiente de A')
            self.assertIn('test', self.prompts[-1])
            self.assertIn(condicion, self.prompts[-1])
            self.assertEqual(self.revisar(), 0)
            return 'Recibido el dictamen'
        self.paso(recuperada)
        self.assertEqual(self.llamadas, [('task-dev', A), ('task-dev', B), ('task-dev', A), ('task-dev', A)])
        revisiones = [r for r in motor.leer_metricas(self.root) if r.get('objetivo_llamada') == 'test']
        self.assertEqual(revisiones[-1]['veredicto'], 'APROBADO')
        self.assertEqual(len({r['entradas_llamada'] for r in revisiones}), 1)
        for estado in self.canales('estado', A):
            self.assertNotIn(situacion.casefold(), estado.casefold())

    def test_cuota_del_revisor(self):
        self.espera('cuota', 'espera de cuota', 'capacidad recuperada del rol requerido')

    def test_servicio_externo(self):
        self.espera('servicio', 'espera técnica', 'servicio de pruebas accesible')

    def test_ausencia_de_ejecutables_autorizados(self):
        self.espera('ejecutable', 'pausa motivada', 'ejecutable autorizado disponible')

    def test_acceso_agotado_tras_principal_y_reserva_claude(self):
        self.espera('suscripcion', 'espera técnica', 'recuperar acceso de un perfil autorizado')

