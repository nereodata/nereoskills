"""Recuperación de pasos con arnés simulado, sin red ni esperas reales."""
import argparse
import importlib.util
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import ANY, patch
from tests import aislamiento_telegram


SPEC = importlib.util.spec_from_file_location('motor_fallos', Path(__file__).with_name('orquestar.py'))
motor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(motor)


class FallosArnesTests(unittest.TestCase):
    """Observa perfiles, esperas, consumo y resultado del bucle real."""

    def setUp(self):
        """Aísla todo el entorno excepto decisión y registro de intentos."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.args = argparse.Namespace(idea=None, docs='docs', test=None, harness=None,
            estado=False, max_pasos=2, reintentos=1, espera_max=2, cmd=None,
            presupuesto=None, reintentos_arnes=3, recarga={'sin_progreso': 0})
        self.cfg = {'harness': 'claude', 'model': 'principal',
                    'reserva': [{'harness': 'codex', 'model': 'reserva'}]}
        self.progreso = False
        self.tiempo = 0
        self.instante = datetime(2026, 10, 27, 12, tzinfo=timezone.utc)
        self.enterContext(patch.object(motor, 'ahora', side_effect=lambda: (self.instante + timedelta(seconds=self.tiempo)).isoformat()))
        self.enterContext(patch.object(motor.time, 'monotonic', side_effect=lambda: self.tiempo))
        self.enterContext(patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe))
        self.enterContext(patch.dict(motor.os.environ, {}, clear=True))
        for nombre in ('iniciar_gateway', 'ingerir', 'construir_prompt_paso', 'excluir'):
            self.enterContext(patch.object(motor, nombre, return_value=[] if nombre == 'ingerir' else 'prompt'))
        self.enterContext(patch.object(motor, 'recargar_version', return_value=False))
        self.enterContext(patch.object(motor, 'comprobar_promocion', return_value=(False, '')))
        self.enterContext(patch.object(motor, 'rol_de', return_value=('artemisa', self.cfg)))
        self.enterContext(patch.object(motor, 'escalada', side_effect=lambda r, rol, cfg, arg: (cfg, False)))
        self.enterContext(patch.object(motor, 'config', return_value={}))
        self.enterContext(patch.object(motor, 'estado', side_effect=[('PASO', 'bug-fix', 'B-ADV-0011', ''), ('FIN', 'ok')]))
        self.enterContext(patch.object(motor, 'firma', side_effect=lambda *a: 'despues' if self.progreso else 'antes'))
        self.git = self.enterContext(patch.object(motor, 'git', return_value=''))
        self.enterContext(patch.object(motor, 'buscar_sesion_paso', return_value='sesion-vieja'))
        self.ejecutar = self.enterContext(patch.object(motor, 'ejecutar'))
        self.esperar = self.enterContext(patch.object(motor, 'esperar', return_value=True))
        self.aviso = self.enterContext(patch.object(motor, 'avisar'))
        self.enterContext(patch('builtins.print'))

    def simular(self, resultados):
        """Marca progreso únicamente en una respuesta satisfactoria."""
        resultados = iter(resultados)
        def ejecutar(*args, **kwargs):
            resultado = next(resultados)
            if resultado[0] == 0:
                self.progreso = True
            return resultado
        self.ejecutar.side_effect = ejecutar

    def correr(self):
        """Ejecuta el paso y lee sus métricas persistidas."""
        codigo = motor.bucle(self.args, self.root)
        return codigo, motor.leer_metricas(self.root)

    def test_transitorio_y_consumo_por_intento(self):
        """Dos fallos no consumen pasos ni presupuesto de falta de progreso."""
        self.simular([(1, {'modelos': {'m': {'entrada': 11}}}, 'network'),
                      (1, {'modelos': {'m': {'entrada': 13}}}, 'network'),
                      (0, {'modelos': {'m': {'entrada': 17}}}, 'ok')])
        codigo, filas = self.correr()
        self.assertEqual(codigo, 0)
        self.assertEqual([c.args[1] for c in self.esperar.call_args_list], [60, 300])
        self.assertEqual([c.kwargs['rol']['model'] for c in self.ejecutar.call_args_list], ['principal'] * 3)
        self.assertNotIn('sesion', self.ejecutar.call_args_list[1].kwargs)
        self.assertEqual([f['modelos']['m']['entrada'] for f in filas if f.get('tipo') == 'paso'], [11, 13, 17])
        self.assertFalse(any(f.get('sin_cuota') for f in filas))

    def test_persistente_agota_perfiles_y_diagnostico(self):
        """El aviso contiene la cola completa y limitada del último perfil."""
        self.args.reintentos_arnes = 1
        cola = 'B' * 1997 + 'FIN'
        self.simular([(7, {}, 'principal')] * 2 + [(8, {}, 'A' * 3000 + cola)] * 2)
        codigo, filas = self.correr()
        self.assertEqual(codigo, 2)
        self.assertEqual([c.kwargs['rol']['model'] for c in self.ejecutar.call_args_list],
                         ['principal', 'principal', 'reserva', 'reserva'])
        self.assertEqual([c.args[1] for c in self.esperar.call_args_list], [60, 60])
        mensaje = self.aviso.call_args.args[2]
        self.assertEqual(mensaje.split('Última salida del arnés:\n', 1)[1], cola)
        self.assertEqual(len([f for f in filas if f.get('tipo') == 'paso']), 4)
        self.assertFalse(any(f.get('sin_cuota') for f in filas))

    def test_cero_reintentos_reserva_sin_sesion(self):
        """Cero omite esperas pero permite recuperar con la reserva."""
        self.args.reintentos_arnes = 0
        self.simular([(1, {'sesion': 'fallida'}, 'network'), (0, {}, 'ok')])
        self.assertEqual(self.correr()[0], 0)
        self.esperar.assert_not_called()
        self.assertEqual(self.ejecutar.call_count, 2)
        self.assertNotIn('sesion', self.ejecutar.call_args.kwargs)
        self.assertEqual([c.kwargs['rol']['model'] for c in self.ejecutar.call_args_list], ['principal', 'reserva'])

    def test_default_y_espera_saturada(self):
        """El valor por defecto es tres; las esperas posteriores son 900."""
        for limite, esperas in [(None, [60, 300, 900]), (4, [60, 300, 900, 900])]:
            with self.subTest(limite=limite):
                self.args.max_pasos = 1
                if limite is None:
                    del self.args.reintentos_arnes
                else:
                    self.args.reintentos_arnes = limite
                self.cfg.pop('reserva', None)
                self.esperar.reset_mock()
                self.ejecutar.reset_mock()
                self.simular([(1, {}, 'network')] * (len(esperas) + 1))
                with patch.object(motor, 'estado', return_value=('PASO', 'bug-fix', 'B-ADV-0011', '')):
                    self.assertEqual(self.correr()[0], 2)
                self.assertEqual(self.ejecutar.call_count, len(esperas) + 1)
                self.assertEqual([c.args[1] for c in self.esperar.call_args_list], esperas)

    def test_parada_en_espera(self):
        """Una petición de parada impide ejecutar otro intento o reserva."""
        self.simular([(1, {}, 'network')])
        self.esperar.return_value = False
        self.assertEqual(self.correr()[0], 2)
        self.ejecutar.assert_called_once()
        self.assertFalse(any(c.args[1] == 'error' for c in self.aviso.call_args_list))

    def test_completado_en_disco_no_repite(self):
        """Un retorno incorrecto con paso completado y limpio no se repite."""
        def ejecutar(*args, **kwargs):
            self.registrar_cierre()
            self.progreso = True
            return 1, {}, 'network'
        self.ejecutar.side_effect = ejecutar
        self.assertEqual(self.correr()[0], 0)
        self.ejecutar.assert_called_once()
        self.esperar.assert_not_called()

    def test_cuota_mixta_con_fallo_de_reserva(self):
        """Los errores operacionales no borran ni inventan la cuota."""
        self.args.reintentos_arnes = 0
        self.simular([(1, {}, 'quota'), (1, {}, 'network')])
        self.esperar.return_value = False
        self.assertEqual(self.correr()[0], 2)
        self.esperar.assert_called_once_with(self.root, 300, cuotas_esperadas=ANY)
        filas = motor.leer_metricas(self.root)
        self.assertTrue(any(f.get('sin_cuota') and f['arnes'] == 'claude' for f in filas))
        reservas = [f for f in filas if f.get('tipo') == 'paso' and f['arnes'] == 'codex']
        self.assertEqual(len(reservas), 1)
        self.assertEqual(reservas[0]['codigo'], 1)
        for fila in reservas:
            self.assertFalse(fila.get('sin_cuota'))
            self.assertNotIn('cuota_espera_s', fila)
            self.assertNotIn('espera_s', fila)

    def test_exito_no_espera(self):
        """El camino exitoso sigue usando una única llamada al arnés."""
        self.simular([(0, {}, 'ok')])
        self.assertEqual(self.correr()[0], 0)
        self.ejecutar.assert_called_once()
        self.esperar.assert_not_called()

    def test_cli_rechaza_limites_invalidos(self):
        """La entrada inválida se rechaza antes de ejecutar el motor."""
        for valor in ('-1', 'abc', '1.5'):
            with (self.subTest(valor=valor), patch('sys.argv', ['orquestar', '--reintentos-arnes', valor]),
                  patch.object(motor, 'bucle') as bucle):
                with self.assertRaises(SystemExit) as error:
                    motor.main()
                self.assertEqual(error.exception.code, 2)
                bucle.assert_not_called()


    def test_cli_propaga_limite_valido_y_default(self):
        """El límite público llega intacto al bucle con cero, cuatro o defecto."""
        for opciones, esperado in [([], 3), (['--reintentos-arnes', '0'], 0),
                                   (['--reintentos-arnes', '4'], 4)]:
            with (self.subTest(opciones=opciones), patch('sys.argv', ['orquestar', *opciones]),
                  patch.object(motor.Path, 'cwd', return_value=self.root),
                  patch.object(motor, 'recibir_recarga', return_value=None),
                  patch.object(motor, 'validar_lanzamiento_bucle'),
                  patch.object(motor, 'pid_vivo', return_value=None),
                  patch.object(motor, 'es_propietario_pid', return_value=False),
                  patch.object(motor, 'bucle', return_value=0) as bucle):
                self.assertEqual(motor.main(), 0)
                self.assertEqual(bucle.call_args.args[0].reintentos_arnes, esperado)
                self.assertEqual(bucle.call_args.args[1], self.root)

    def registrar_cuota_previa(self, segundos):
        """Registra agotamiento del principal antes de seleccionar perfiles."""
        motor.registrar(self.root, {'tipo': 'paso', 'fecha': motor.ahora(),
            'arnes': 'claude', 'modelo_cuota': 'principal', 'cuota_espera_s': segundos,
            'codigo': 1, 'sin_cuota': True, 'modelos': {}})

    def test_compara_cuota_omitida_y_cuota_del_paso(self):
        """Una recuperación de 120 s prevalece sobre otra de 3600 s."""
        self.args.reintentos_arnes = 0
        self.args.espera_max = 0.5
        self.cfg['reserva'].append({'harness': 'agy', 'model': 'tercero'})
        self.registrar_cuota_previa(120)
        self.simular([(1, {}, 'quota resets in 1 hour'), (1, {}, 'network')])
        self.esperar.return_value = False
        self.assertEqual(self.correr()[0], 2)
        self.esperar.assert_called_once_with(self.root, 120, cuotas_esperadas=ANY)
        self.assertEqual([c.kwargs['rol']['model'] for c in self.ejecutar.call_args_list], ['reserva', 'tercero'])
        final = [f for f in motor.leer_metricas(self.root) if f.get('tipo') == 'paso'][-1]
        self.assertEqual(final['arnes'], 'claude')
        self.assertEqual(final['espera_s'], 120)

    def test_reconsidera_omitido_recuperado_durante_reintentos(self):
        """Un perfil recuperado se ejecuta una sola vez tras agotar la reserva."""
        self.args.reintentos_arnes = 1
        self.registrar_cuota_previa(30)
        def esperar(*args, **kwargs):
            self.tiempo += args[1]
            return True
        self.esperar.side_effect = esperar
        self.simular([(1, {}, 'network'), (1, {}, 'network'), (0, {}, 'ok')])
        self.assertEqual(self.correr()[0], 0)
        self.assertEqual([c.kwargs['rol']['model'] for c in self.ejecutar.call_args_list], ['reserva', 'reserva', 'principal'])
        self.assertEqual(self.esperar.call_count, 1)

    def test_fallos_sin_consumo_identifican_modelo(self):
        """Dos modelos del mismo arnés son distinguibles sin consumo inventado."""
        self.cfg['reserva'][0]['harness'] = 'claude'
        self.args.reintentos_arnes = 0
        self.simular([(1, {'duracion_s': 1}, 'network'), (1, {'duracion_s': 2}, 'network')])
        codigo, filas = self.correr()
        self.assertEqual(codigo, 2)
        intentos = [f for f in filas if f.get('tipo') == 'paso']
        self.assertEqual([f.get('modelo') for f in intentos], ['principal', 'reserva'])
        for fila in intentos:
            self.assertFalse(fila.get('sin_cuota'))
            self.assertNotIn('modelos', fila)

    def test_recuperado_persistente_no_reinicia_perfiles(self):
        """Un omitido recuperado también tiene presupuesto finito de intentos."""
        self.args.reintentos_arnes = 1
        self.registrar_cuota_previa(30)
        def esperar(*args, **kwargs):
            self.tiempo += args[1]
            return True
        self.esperar.side_effect = esperar
        self.simular([(1, {}, 'network')] * 4)
        self.assertEqual(self.correr()[0], 2)
        self.assertEqual([c.kwargs['rol']['model'] for c in self.ejecutar.call_args_list],
                         ['reserva', 'reserva', 'principal', 'principal'])
        self.assertEqual(self.esperar.call_count, 2)

    def revisar_dentro_del_paso(self, pendiente=False, dos_invocaciones=False, limpio=False):
        """Ejecuta reservas reales del rol dentro del paso con proveedores simulados."""
        self.args.espera_max = 0
        self.args.reintentos_arnes = 0
        cfg = {'hades': {'harness': 'claude', 'model': 'opus', 'reserva': [
            {'harness': 'agy', 'model': 'gemini'}, {'harness': 'codex', 'model': 'gpt'}]}}
        error = 'Your organization has disabled Claude subscription access for Claude Code.'
        resultados = [(1, {'modelos': {'opus': {'entrada': 2}}}, error),
                      (3, {'modelos': {'gemini': {'entrada': 3}}}, 'quota resets in 1 hour'),
                      (0, {'modelos': {'gpt': {'entrada': 5}}}, 'Veredicto: APROBADO')]
        if pendiente:
            resultados[-1] = (1, {}, 'quota resets in 2 hours')
            resultados.append((0, {'modelos': {'gpt': {'entrada': 7}}}, 'Veredicto: APROBADO'))
        elif dos_invocaciones:
            resultados = [(1, {}, 'network'), *resultados]
        def ejecutar(*args, **kwargs):
            with (patch.object(motor, 'config', return_value=cfg),
                  patch.object(motor, 'buscar_sesion_agente', return_value=None),
                  patch.object(motor, 'lanzar', side_effect=resultados),
                  patch.dict(motor.os.environ, kwargs['env'])):
                if dos_invocaciones:
                    self.assertEqual(motor.agente(self.root, 'hades', 'primera'), 1)
                revision = motor.agente(self.root, 'hades', 'revisa')
                if pendiente:
                    self.assertEqual(revision, 1)
                    cfg['hades'] = {'harness': 'codex', 'model': 'gpt-otra'}
                    self.assertEqual(motor.agente(self.root, 'hades', 'otra revisión'), 0)
                else:
                    self.assertEqual(revision, 0)
                    informe = self.root / 'review.md'
                    informe.write_text('Veredicto: APROBADO', encoding='utf-8')
            self.registrar_cierre(completado=not pendiente, limpio=not pendiente or limpio)
            self.progreso = True
            return 0, {'modelos': {'principal': {'entrada': 11}}}, 'paso terminado'
        self.ejecutar.side_effect = ejecutar
        return self.correr()

    def test_reserva_recuperada_no_propaga_cuota(self):
        """Claude denegado y Gemini agotado no detienen un paso revisado por Codex."""
        codigo, filas = self.revisar_dentro_del_paso()
        self.assertEqual(codigo, 0)
        self.esperar.assert_not_called()
        agentes = [f for f in filas if f.get('tipo') == 'agente']
        self.assertTrue(agentes[0]['acceso_denegado'])
        self.assertEqual(agentes[1]['modelo_cuota'], 'gemini')
        self.assertGreaterEqual(agentes[1]['cuota_espera_s'], 3600)
        self.assertEqual(agentes[-1]['veredicto'], 'APROBADO')
        self.assertEqual([f['modelos'] for f in agentes], [
            {'opus': {'entrada': 2}}, {'gemini': {'entrada': 3}}, {'gpt': {'entrada': 5}}])
        pasos = [f for f in filas if f.get('tipo') == 'paso']
        self.assertEqual([f['modelos'] for f in pasos], [{'principal': {'entrada': 11}}])
        self.assertFalse(any(f.get('sin_cuota') or f.get('espera_s') for f in pasos))
        marcas = motor.marcas_cuota(self.root, motor.fecha_estado(motor.ahora()))
        self.assertIn(('agy', 'gemini'), marcas)
        self.assertNotIn(('codex', 'gpt'), marcas)

    def test_revisiones_distintas_no_borran_cuota_pendiente(self):
        """Otra aprobación y progreso parcial no satisfacen la revisión que falta."""
        codigo, filas = self.revisar_dentro_del_paso(pendiente=True)
        self.assertEqual(codigo, 2)
        self.esperar.assert_not_called()
        mensaje = self.aviso.call_args.args[2]
        self.assertIn('agy', mensaje)
        self.assertIn('gemini', mensaje)
        self.assertIn('cuota', mensaje)
        pasos = [f for f in filas if f.get('tipo') == 'paso']
        self.assertFalse(any(f.get('sin_cuota') or f.get('espera_s') for f in pasos))

    def test_invocaciones_de_un_rol_se_correlacionan(self):
        """Dos llamadas al mismo rol conservan identidades independientes."""
        codigo, filas = self.revisar_dentro_del_paso(dos_invocaciones=True)
        self.assertEqual(codigo, 0)
        agentes = [f for f in filas if f.get('tipo') == 'agente']
        self.assertNotEqual(agentes[0]['invocacion'], agentes[1]['invocacion'])
        self.assertEqual(len({f['invocacion'] for f in agentes[1:]}), 1)

    def test_paso_completado_supera_espera_de_revision_anterior(self):
        """Una revisión reintentada y cerrada no deja cuota en el paso limpio."""
        self.args.espera_max = 0
        def ejecutar(*args, **kwargs):
            motor.registrar(self.root, {'tipo': 'agente', 'fecha': motor.ahora(),
                'rol': 'hades', 'arnes': 'agy', 'modelo_cuota': 'gemini',
                'codigo': 3, 'sin_cuota': True, 'espera_s': 3600})
            motor.registrar(self.root, {'tipo': 'agente', 'fecha': motor.ahora(),
                'rol': 'hades', 'arnes': 'codex', 'codigo': 0, 'veredicto': 'APROBADO'})
            self.registrar_cierre()
            self.progreso = True
            return 0, {}, 'completado y commiteado'
        self.ejecutar.side_effect = ejecutar
        codigo, filas = self.correr()
        self.assertEqual(codigo, 0)
        self.esperar.assert_not_called()
        paso = [f for f in filas if f.get('tipo') == 'paso'][-1]
        self.assertFalse(paso.get('sin_cuota') or paso.get('espera_s'))

    def registrar_cierre(self, completado=True, limpio=True):
        """Persiste el estado y revisión; simula un commit distinto con árbol limpio."""
        bugs = self.root / 'docs/plan/bugs'
        bugs.mkdir(parents=True, exist_ok=True)
        estado = 'completed' if completado else 'in_progress'
        (bugs / 'B-ADV-0011.md').write_text(
            f'---\nid: B-ADV-0011\nstatus: {estado}\n---\n', encoding='utf-8')
        informes = self.root / 'docs/review/code_reviews'
        informes.mkdir(parents=True, exist_ok=True)
        if completado:
            (informes / 'B-ADV-0011-code-review.md').write_text('**Veredicto:** APROBADO', encoding='utf-8')
        def git(*args, **kwargs):
            if args == ('rev-parse', 'HEAD'):
                return 'commit-final'
            if args == ('status', '--porcelain'):
                return '' if limpio else ' M bug.md'
            return ''
        self.git.side_effect = git

    def test_revision_pendiente_con_commit_parcial_limpio(self):
        """Un commit parcial limpio no resuelve la revisión obligatoria que falta."""
        codigo, filas = self.revisar_dentro_del_paso(pendiente=True, limpio=True)
        self.assertEqual(codigo, 2)
        self.assertIn('agy/gemini', self.aviso.call_args.args[2])
        self.esperar.assert_not_called()
        paso = [f for f in filas if f.get('tipo') == 'paso'][-1]
        self.assertEqual(paso['bloqueo_agente']['modelo_cuota'], 'gemini')
        self.assertFalse(paso.get('sin_cuota'))

    def test_resumen_no_renueva_recuperacion_original(self):
        """El tiempo de las reservas se descuenta sin desplazar el agotamiento real."""
        cfg = {'hades': {'harness': 'agy', 'model': 'primero',
                        'reserva': [{'harness': 'codex', 'model': 'segundo'}]}}
        def lanzar(*args, **kwargs):
            if args[2] == 'agy':
                return 1, {}, 'quota resets in 1 hour'
            self.tiempo += 4000
            return 1, {}, 'quota resets in 10 minutes'
        with (patch.object(motor, 'config', return_value=cfg),
              patch.object(motor, 'buscar_sesion_agente', return_value=None),
              patch.object(motor, 'lanzar', side_effect=lanzar)):
            self.assertEqual(motor.agente(self.root, 'hades', 'revisa'), 1)
        filas = motor.leer_metricas(self.root)
        resumen = filas[-1]
        self.assertEqual(resumen['modelo_cuota'], 'primero')
        self.assertEqual(resumen['espera_s'], 0)
        self.assertEqual(resumen['fecha'], filas[0]['fecha'])
        instante = motor.fecha_estado(motor.ahora())
        marcas = motor.marcas_cuota(self.root, instante)
        primero, segundo = filas[:2]
        vencimiento = motor.fecha_estado(primero['fecha']) + timedelta(seconds=primero['cuota_espera_s'])
        self.assertEqual(marcas[('agy', 'primero')]['hasta'], vencimiento)
        self.assertLessEqual(vencimiento, instante)
        _, vigentes = motor.consumo_cuotas(self.root, instante)
        self.assertNotIn(('agy', 'primero'), vigentes)
        self.assertEqual(vigentes[('codex', 'segundo')],
                         motor.fecha_estado(segundo['fecha']) + timedelta(seconds=segundo['cuota_espera_s']))
