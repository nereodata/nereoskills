"""Contrato B-ADV-0020: recuperación y clasificación de agotamientos persistidos."""
import importlib.util
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest.mock import patch

from tests import aislamiento_telegram


spec = importlib.util.spec_from_file_location('cuota_supuesta_motor', Path(__file__).with_name('orquestar.py'))
motor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(motor)


class CuotaSupuestaTests(unittest.TestCase):
    """Usa JSONL real y arneses simulados, sin red ni esperas reales."""

    def setUp(self):
        """Prepara un proceso nuevo con reloj controlado y reserva disponible."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.instante = motor.fecha_estado('2026-10-27T12:00:00+00:00')
        self.cfg = {'hades': {'harness': 'codex', 'model': 'm1',
                             'reserva': {'harness': 'claude', 'model': 'm2'}}}
        self.enterContext(patch.object(motor, 'ahora', side_effect=lambda: self.instante.isoformat()))
        self.enterContext(patch.object(motor, 'config', side_effect=lambda root: self.cfg))
        self.enterContext(patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe))
        self.enterContext(patch.object(motor, 'construir_prompt_agente', return_value='revisa'))
        self.enterContext(patch.object(motor, 'excluir'))
        self.enterContext(patch.dict(motor.os.environ, {}, clear=True))
        self.aviso = self.enterContext(patch.object(motor, 'avisar'))
        self.enterContext(patch('builtins.print'))

    def marca(self, arnes='codex', modelo='m1', segundos=300, **extra):
        """Persiste una marca anterior al proceso actual."""
        motor.registrar(self.root, dict(tipo='agente', fecha=(self.instante - timedelta(seconds=60)).isoformat(),
                                       arnes=arnes, modelo_cuota=modelo, cuota_espera_s=segundos, **extra))

    def invocar(self, respuestas):
        """Ejecuta el camino público de revisión y devuelve los arneses utilizados."""
        with patch.object(motor, 'lanzar', side_effect=respuestas) as lanzar:
            motor.agente(self.root, 'hades', 'revisa')
        return [llamada.args[2] for llamada in lanzar.call_args_list]

    def consulta(self, opcion):
        """Consulta las entradas CLI con deducción de estado real y sin procesos externos."""
        with (patch.object(motor.sys, 'argv', ['orquestar', opcion]),
              patch.object(motor.Path, 'cwd', return_value=self.root),
              patch.object(motor.sys, 'stdout'), patch.object(motor.sys, 'stderr'),
              patch.object(motor, 'recibir_recarga', return_value=None),
              patch.object(motor, 'pid_vivo', return_value=None),
              patch.object(motor, 'cuota_codex', return_value=None),
              patch('builtins.print') as imprimir):
            self.assertIn(motor.main(), (0, 2))
        return '\n'.join(str(c.args[0]) for c in imprimir.call_args_list if c.args)

    def test_relanzar_supuesta_e_historica_recupera_sin_reescribir(self):
        """El primer paso prueba las sospechas y añade recuperación al responder."""
        for extra, segundos in (({'cuota_tipo': 'supuesta', 'cuota_origen': 'sin hora en la respuesta'}, 300),
                                ({}, 1800)):
            with self.subTest(extra=extra):
                (self.root / motor.METRICAS).unlink(missing_ok=True)
                self.marca(segundos=segundos, **extra)
                prefijo = (self.root / motor.METRICAS).read_bytes()
                self.assertEqual(self.invocar([(0, {}, 'APROBADO')]), ['codex'])
                self.assertNotIn(('codex', 'm1'), motor.consumo_cuotas(self.root, self.instante)[1])
                self.assertTrue((self.root / motor.METRICAS).read_bytes().startswith(prefijo))
                self.assertTrue(any(f.get('tipo') == 'cuota_recuperada' for f in motor.leer_metricas(self.root)))

    def test_reales_e_historicas_conservan_restriccion(self):
        """Una marca histórica de 3600 segundos conserva los 3540 restantes."""
        for extra in ({}, {'cuota_tipo': 'real', 'cuota_origen': 'hora en la respuesta'}):
            self.marca(segundos=3600, **extra)
            prefijo = (self.root / motor.METRICAS).read_bytes()
            self.assertEqual(self.invocar([(0, {}, 'APROBADO')]), ['claude'])
            hasta = motor.consumo_cuotas(self.root, self.instante)[1][('codex', 'm1')]
            self.assertEqual((hasta - self.instante).total_seconds(), 3540)
            self.assertTrue((self.root / motor.METRICAS).read_bytes().startswith(prefijo))

    def test_intervalo_configurado_invalido_y_ausente(self):
        """El límite exacto vuelve a priorizar el titular antes que la reserva."""
        for valor, segundos in ((120, 120), (0, 300), (-5, 300), ('texto', 300),
                                (None, 300), (True, 300), ('ausente', 300)):
            with self.subTest(valor=valor):
                (self.root / motor.METRICAS).unlink(missing_ok=True)
                self.cfg.pop('cuota_reintento_s', None)
                if valor != 'ausente':
                    self.cfg['cuota_reintento_s'] = valor
                self.assertEqual(self.invocar([(1, {}, 'quota'), (0, {}, 'APROBADO')]), ['codex', 'claude'])
                self.instante += timedelta(seconds=segundos - 1)
                self.assertEqual(self.invocar([(0, {}, 'APROBADO')]), ['claude'])
                self.instante += timedelta(seconds=1)
                self.assertEqual(self.invocar([(0, {}, 'APROBADO')]), ['codex'])

    def test_sospecha_sin_reserva_no_se_sondea_antes_del_intervalo(self):
        """La falta de reservas no permite saltarse los 300 segundos entre sondeos."""
        self.cfg['hades'].pop('reserva')
        self.assertEqual(self.invocar([(1, {}, 'quota')]), ['codex'])
        self.instante += timedelta(seconds=299)
        self.assertEqual(self.invocar([]), [])
        self.instante += timedelta(seconds=1)
        self.assertEqual(self.invocar([(0, {}, 'APROBADO')]), ['codex'])

    def test_reset_cli_selecciona_solo_pares_y_conserva_historico(self):
        """La orden recupera modelo, arnés o todos sin afectar los ajenos."""
        pares = {('codex', 'm1'), ('codex', 'm2'), ('claude', 'm1')}
        for selector, elegidos in (('codex/m1', {('codex', 'm1')}),
                                  ('codex', {('codex', 'm1'), ('codex', 'm2')}), ('', pares)):
            with self.subTest(selector=selector):
                (self.root / motor.METRICAS).unlink(missing_ok=True)
                for arnes, modelo in pares:
                    self.marca(arnes, modelo, 3600, cuota_tipo='real', cuota_origen='hora en la respuesta')
                prefijo = (self.root / motor.METRICAS).read_bytes()
                args = ['orquestar', '--cuota-reset'] + ([selector] if selector else [])
                with (patch.object(motor.sys, 'argv', args), patch.object(motor.Path, 'cwd', return_value=self.root),
                      patch.object(motor.sys, 'stdout'), patch.object(motor.sys, 'stderr'),
                      patch.object(motor, 'iniciar_gateway') as gateway):
                    self.assertEqual(motor.main(), 0)
                gateway.assert_not_called()
                cuotas = motor.consumo_cuotas(self.root, self.instante)[1]
                self.assertEqual(set(cuotas), pares - elegidos)
                self.assertTrue((self.root / motor.METRICAS).read_bytes().startswith(prefijo))
                recuperados = {(f['arnes'], f['modelo_cuota']) for f in motor.leer_metricas(self.root)
                               if f.get('tipo') == 'cuota_recuperada'}
                self.assertEqual(recuperados, elegidos)
                for par in pares:
                    configuraciones = [{'harness': par[0], 'model': par[1]}, {'harness': 'agy', 'model': 'libre'}]
                    seleccion = motor.configuraciones_con_cuota(self.root, configuraciones)
                    self.assertEqual(configuraciones[0] in seleccion, par in elegidos)
                perfiles = [('hades', 'base', {'harness': h, 'model': m}) for h, m in pares]
                with (patch.object(motor, 'estado', return_value=('FIN', '', '', '')),
                      patch.object(motor, 'perfiles_agentes', return_value=perfiles),
                      patch.object(motor, 'cuota_codex', return_value=None)):
                    informe = motor.informe_agentes(self.root)
                for h, m in pares:
                    linea = next(l for l in informe.splitlines() if l.startswith(f'{h}/{m}:'))
                    self.assertEqual('agotado' in linea, (h, m) not in elegidos)
                estado = self.consulta('--estado')
                for h, m in pares:
                    self.assertEqual(f'{h}/{m}: 100.0% consumido (agotado' in estado, (h, m) not in elegidos)

    def test_reset_despierta_espera_en_siguiente_comprobacion(self):
        """Una orden concurrente interrumpe la espera sin relanzar el proceso."""
        self.marca(segundos=3600, cuota_tipo='real')
        def reset(segundos):
            self.assertLessEqual(segundos, 30)
            motor.reset_cuotas(self.root, 'codex/m1')
        with patch.object(motor.time, 'sleep', side_effect=reset) as dormir:
            self.assertTrue(motor.esperar(self.root, 3600))
        dormir.assert_called_once()
        self.assertFalse((self.root / motor.ESPERA).exists())

    def test_creditos_una_vez_por_episodio_y_origen_visible(self):
        """Los créditos no generan avisos repetidos; una recuperación abre otro episodio."""
        for mensaje in ('out of credits', 'credit balance', 'billing_hard_limit'):
            with self.subTest(mensaje=mensaje):
                (self.root / motor.METRICAS).unlink(missing_ok=True)
                self.aviso.reset_mock()
                self.assertEqual(self.invocar([(1, {}, mensaje), (0, {}, 'APROBADO')]), ['codex', 'claude'])
                self.instante += timedelta(seconds=299)
                self.assertEqual(self.invocar([(0, {}, 'APROBADO')]), ['claude'])
                self.instante += timedelta(seconds=1)
                self.assertEqual(self.invocar([(1, {}, mensaje), (0, {}, 'APROBADO')]), ['codex', 'claude'])
                self.assertEqual(self.aviso.call_count, 1)
                self.assertIn('Sin créditos en codex: recarga y el bucle lo reintentará', self.aviso.call_args.args[2])
                for opcion in ('--agentes', '--estado'):
                    informe = self.consulta(opcion)
                    self.assertIn('supuesto', informe)
                    self.assertIn('sin créditos', informe)
                motor.reset_cuotas(self.root, 'codex')
                self.assertEqual(self.invocar([(1, {}, mensaje), (0, {}, 'APROBADO')]), ['codex', 'claude'])
                self.assertEqual(self.aviso.call_count, 2)

    def test_origen_real_visible(self):
        """El texto de recuperación confirma y explica la marca en los informes."""
        self.invocar([(1, {}, 'usage limit resets in 1 hour'), (0, {}, 'APROBADO')])
        hasta = self.instante + timedelta(seconds=3720)
        for opcion in ('--estado', '--agentes'):
            informe = self.consulta(opcion)
            self.assertIn('real', informe)
            self.assertIn('hora en la respuesta', informe)
            self.assertIn(f'agotado hasta {hasta:%H:%M %z}', informe)

    def test_reset_entre_lecturas_no_rompe_seleccion_ni_informe(self):
        """Intercala una recuperación tras leer las primeras filas del JSONL."""
        for consulta in ('seleccion', 'informe'):
            with self.subTest(consulta=consulta):
                (self.root / motor.METRICAS).unlink(missing_ok=True)
                self.marca(cuota_tipo='supuesta')
                leer = motor.leer_metricas
                primera = [True]
                def leer_y_reset(root):
                    """Devuelve la instantánea previa y deja un reset para la siguiente lectura."""
                    filas = leer(root)
                    if primera[0]:
                        primera[0] = False
                        motor.registrar(root, dict(tipo='cuota_recuperada', fecha=motor.ahora(),
                                                   arnes='codex', modelo_cuota='m1'))
                    return filas
                with (patch.object(motor, 'leer_metricas', side_effect=leer_y_reset),
                      patch.object(motor, 'cuota_codex', return_value=None)):
                    if consulta == 'seleccion':
                        resultado = motor.configuraciones_con_cuota(self.root, [self.cfg['hades'],
                                                                               self.cfg['hades']['reserva']])
                        self.assertIn(self.cfg['hades'], resultado)
                    else:
                        self.assertIn('codex/m1:', motor.informe_agentes(self.root))

    def bucle_real(self, respuesta, aviso=None):
        """Ejercita la transición real a espera con reset y Telegram simulados."""
        cfg = {'harness': 'claude', 'model': 'm2'}
        args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness=None,
                                       estado=False, max_pasos=2, reintentos=2, espera_max=2, cmd=None)
        self.cfg['artemisa'] = cfg
        with (patch.object(motor, 'iniciar_gateway'), patch.object(motor, 'recargar_version', return_value=False),
              patch.object(motor, 'ingerir', return_value=[]),
              patch.object(motor, 'estado', side_effect=[('PASO', 'bug-fix', 'B-ADV-0020', ''), ('FIN', 'ok')]),
              patch.object(motor, 'firma', return_value='igual'), patch.object(motor, 'git', return_value=''),
              patch.object(motor, 'ejecutar', return_value=(1, {}, respuesta)),
              patch.object(motor, 'avisar', side_effect=aviso) as avisar):
            self.assertEqual(motor.bucle(args, self.root), 0)
        return avisar.call_args_list

    def test_reset_antes_de_entrar_en_espera_no_duerme(self):
        """Recupera durante el aviso, una vez calculado el plazo pero antes de esperar."""
        def recuperar(root, evento, mensaje):
            """Simula otra orden que recupera la cuota antes del primer sleep."""
            if evento == 'cuota':
                motor.reset_cuotas(root, 'claude/m2')
        with patch.object(motor.time, 'sleep', side_effect=AssertionError('reset perdido')):
            self.bucle_real('usage limit resets in 58 minutes', recuperar)

    def test_creditos_antiguos_no_suprimen_aviso_real_ajeno(self):
        """Una marca vencida de otro perfil no oculta la cuota real de la espera actual."""
        self.marca(segundos=1, cuota_tipo='supuesta', cuota_origen='sin créditos')
        with patch.object(motor, 'esperar', return_value=True):
            llamadas = self.bucle_real('usage limit resets in 58 minutes')
        cuotas = [c.args[2] for c in llamadas if c.args[1] == 'cuota']
        self.assertEqual(len(cuotas), 1)
        self.assertIn('Sin cuota', cuotas[0])


if __name__ == '__main__':
    unittest.main()
