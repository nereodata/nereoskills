"""Entrega de una intervención E2E, con Git, selector, mandatos y registro de cuota reales."""
import argparse
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import chdir
from pathlib import Path
from unittest.mock import patch

from tests.test_orquestar import motor


class IntervencionSuiteTests(unittest.TestCase):
    iid = 'B-AFN-0185'
    solicitud = 'ab' * 32
    mandato = 'Aislar la operación de cierre y acreditar la corrección antes de reanudar.'
    respuesta = '**Veredicto formal: RECHAZADO. Media: 7,75/10.**'

    def escribir(self, ruta, texto):
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(texto, encoding='utf-8')

    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.enterContext(chdir(self.root))
        for args in [('init', '-qb', 'release/v0.7'), ('config', 'user.name', 'Suite'),
                     ('config', 'user.email', 'suite@example.test')]:
            subprocess.run(['git', *args], check=True)
        for nombre in ('requirements', 'req_analysis', 'platform_plan', 'platform_review', 'work_plan'):
            self.escribir(self.root / f'docs/{nombre}.md', 'APROBADO\n')
        self.escribir(self.root / 'task_config.yaml', 'project: {name: demo}\n')
        self.escribir(self.root / 'orchestration.json', json.dumps({
            'hades': {'harness': 'agy', 'model': 'argon', 'reserva': [{'harness': 'codex', 'model': 'juez'}]},
            'development': {'harness': 'codex', 'model': 'desarrollo'}}))
        self.ficha = self.root / f'docs/plan/bugs/{self.iid}.md'
        self.informe = self.root / f'docs/review/test_reviews/{self.iid}-test-review.md'
        self.preparar_bloqueo()
        motor.excluir(self.root)
        subprocess.run(['git', 'add', '.'], check=True)
        subprocess.run(['git', 'commit', '-qm', 'candidato 70/71 y rechazo de C1'], check=True)
        self.args = argparse.Namespace(docs='docs', idea=None, test=None, harness=None, estado=False,
                                       max_pasos=3, reintentos=2, espera_max=0, cmd=None, presupuesto=None)
        self.enterContext(patch.object(motor, 'iniciar_gateway'))
        self.enterContext(patch.object(motor, 'recargar_version', return_value=False))
        self.enterContext(patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe))
        self.aviso = self.enterContext(patch.object(motor, 'avisar'))
        self.marcar_cuota('agy', 'argon')

    def preparar_bloqueo(self):
        self.escribir(self.ficha, '---\nid: B-AFN-0185\nversion: v0.7\nstatus: blocked\n'
                      'pendiente_de: intervencion_tecnica\ndepende_de: []\nsuite_cierre: true\n'
                      'suite_accion: resuelta\nsuite_intentos: 3\n---\n\n## Hallazgo de Hades enrutado\n'
                      f'- Destino: `artemisa`\n- Evidencia: rechazo C1 RT-01 de la solicitud {self.solicitud}.\n')
        self.escribir(self.informe, '**Veredicto:** RECHAZADO\n\n### RT-01\n'
                      '- **Para:** `desarrollador/artemisa`.\n- **Destino del hallazgo:** `resolver`.\n'
                      '- **Ruta terminal de la solicitud:** `tecnico`.\n'
                      f'\nEl dictamen de la solicitud `{self.solicitud}` autoriza la intervención.\n')
        grupo = {'solicitud': self.solicitud, 'intentos': 3, 'evidencias': [{'salida': '70/71'}],
                 'estrategia_aplicada': True, 'dictamen': {'destino': 'desarrollador', 'terminal': {
                     'destino': 'tecnico', 'responsable': 'Mantenedor del arnés', 'intervencion': self.mandato}}}
        self.escribir(self.ficha.with_suffix('.json'), json.dumps({'actual': 'cierre', 'grupos': {'cierre': grupo}}))

    def marcar_cuota(self, proveedor, modelo):
        motor.registrar(self.root, {'tipo': 'agente', 'fecha': motor.ahora(), 'arnes': proveedor,
                                    'modelo_cuota': modelo, 'cuota_espera_s': 86400})

    def ejecutar_recorrido(self, sin_cuota=False, desde_revision=False):
        historial = self.ficha.with_suffix('.json').read_bytes()
        bloqueo = self.ficha.read_text(encoding='utf-8')
        entregas = []
        cuota_en_ejecucion = desde_revision and sin_cuota
        if desde_revision:
            self.ficha.write_text(bloqueo.replace('status: blocked', 'status: in_progress')
                                  .replace('pendiente_de: intervencion_tecnica', ''), encoding='utf-8')
        elif sin_cuota:
            self.marcar_cuota('codex', 'desarrollo')

        def desarrollar(args, root, prompt, env, rol, **kwargs):
            nonlocal cuota_en_ejecucion
            self.assertEqual((env['ORQUESTAR_PASO'], env['ORQUESTAR_ID'], rol['model']),
                             ('bug-fix', self.iid, 'desarrollo'))
            if desde_revision and motor.frontmatter(self.ficha)['status'] == 'in_progress':
                with (patch.dict(os.environ, env), patch.object(motor, 'lanzar',
                      return_value=(0, {}, self.respuesta)) as reserva):
                    self.assertEqual(motor.agente(root, 'hades', 'revisar candidato'), 0)
                    self.assertEqual(reserva.call_args.args[2], 'codex')
                self.ficha.write_text(bloqueo, encoding='utf-8')
                return 0, {}, 'C1 rechazado'
            self.assertIn(self.mandato, prompt)
            self.assertIn(self.solicitud, prompt)
            if cuota_en_ejecucion:
                cuota_en_ejecucion = False
                return 1, {}, 'out of credits'
            entregas.append(prompt)
            return 0, {}, 'Persiste el mismo impedimento'

        with patch.object(motor, 'ejecutar', side_effect=desarrollar):
            self.assertEqual(motor.bucle(self.args, self.root), 2)
            if sin_cuota:
                self.assertEqual(entregas, [])
                _, evento, texto = self.aviso.call_args.args
                self.assertEqual(evento, 'cuota')
                for referencia in ('bug-fix', self.iid, 'codex/desarrollo'):
                    self.assertIn(referencia, texto)
                motor.recuperar_cuota(self.root, 'codex', 'desarrollo')
                self.assertEqual(motor.bucle(self.args, self.root), 2)
            self.assertEqual(len(entregas), 1)
            self.assertEqual(motor.bucle(self.args, self.root), 2)
            self.assertEqual(len(entregas), 1)
        if desde_revision:
            self.assertEqual([r.get('veredicto') for r in motor.leer_metricas(self.root)
                              if r.get('rol') == 'hades'], ['RECHAZADO'])
        self.assertFalse(motor.configuraciones_con_cuota(self.root, [{'harness': 'agy', 'model': 'argon'}]))
        self.assertEqual(motor.frontmatter(self.ficha)['status'], 'blocked')
        self.assertEqual(self.ficha.with_suffix('.json').read_bytes(), historial)
        self.assertEqual(motor.listar_preguntas(self.root), [])

    def test_desde_el_rechazo(self):
        self.ejecutar_recorrido(desde_revision=True)

    def test_desde_el_rechazo_sin_cuota(self):
        self.ejecutar_recorrido(desde_revision=True, sin_cuota=True)

    def test_relanzar_ficha_historica_sin_cuota(self):
        self.ejecutar_recorrido(sin_cuota=True)

    def test_conclusion_tecnica_explicita_del_diagnostico(self):
        historial = json.loads(self.ficha.with_suffix('.json').read_text(encoding='utf-8'))
        grupo = historial['grupos']['cierre']
        grupo['recaida_tras_estrategia'] = True
        grupo['dictamen'].update(causa='Timeout', decision='Se agotó el intento focal')
        grupo['dictamen']['terminal']['agente'] = 'artemisa'
        grupo['dictamen']['terminal']['condicion_salida'] = 'Cinco cierres trazados concluyen.'
        self.escribir(self.ficha.with_suffix('.json'), json.dumps(historial))
        self.escribir(self.ficha, self.ficha.read_text(encoding='utf-8').replace(
            'suite_accion: resuelta', 'suite_accion: pendiente').replace('status: blocked', 'status: planned'))
        self.informe.unlink()
        self.assertEqual(motor.aplicar_diagnostico_suite(self.root, self.ficha), (self.iid, ''))
        self.mandato += '\nCondición de salida: Cinco cierres trazados concluyen.'
        self.ejecutar_recorrido()

    def test_nombre_libre_o_asignacion_caducada(self):
        inicial = self.informe.read_text(encoding='utf-8')
        ficha, historial = self.ficha.read_bytes(), self.ficha.with_suffix('.json').read_bytes()
        otro = inicial.replace(self.solicitud, 'cd' * 32).replace('RT-01', 'RT-02')
        for informe in ('', inicial.replace(self.solicitud, 'cd' * 32), otro + f'\n## Historial\nSolicitud {self.solicitud}',
                        inicial.replace('RECHAZADO', 'APROBADO'), inicial.replace('artemisa', 'externo')):
            self.escribir(self.informe, informe)
            estado, motivo = motor.estado(self.root, 'docs')
            self.assertEqual(estado, 'PARAR')
            self.assertIn('asignación', motivo)
            self.assertEqual(self.ficha.read_bytes(), ficha)
            self.assertEqual(self.ficha.with_suffix('.json').read_bytes(), historial)

    def test_citas_o_entrega_sin_dictamen(self):
        for salida in ('> ' + self.respuesta, 'Ejemplo:\n```\n' + self.respuesta + '\n```', 'Informe pendiente'):
            with patch.object(motor, 'lanzar', return_value=(0, {}, salida)):
                self.assertEqual(motor.agente(self.root, 'hades', 'revisar candidato'), 1)
        self.assertFalse(any(r.get('veredicto') for r in motor.leer_metricas(self.root)))
