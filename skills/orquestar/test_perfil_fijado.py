"""Perfil de modelo fijado por la tarea: lectura, validación, precedencia, reservas y estricto."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import aislamiento_telegram


def cargar(nombre):
    """Carga el motor del árbol de trabajo sin usar la versión instalada."""
    spec = importlib.util.spec_from_file_location(nombre, Path(__file__).with_name(nombre + '.py'))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


motor = cargar('orquestar')

CONFIG = {'artemisa': {'harness': 'claude', 'model': 'sonnet', 'effort': 'medium',
                       'dificultad': {'dificil': {'model': 'opus', 'effort': 'high'}},
                       'reserva': [{'model': 'haiku'}, {'harness': 'codex', 'model': 'gpt'}],
                       'escalada': {'rechazos': 2, 'model': 'opus'}},
          'hades': {'harness': 'claude', 'model': 'sonnet'},
          'atenea': {'harness': 'claude', 'model': 'sonnet'}}

TAREA = '---\nid: T-X-0001\ntitle: "x"\ntype: funcional\nweight: 1\nversion: "v1.0.0"\nstatus: planned\n{extra}---\n\n# x\n'


class PerfilFijadoBase(unittest.TestCase):
    """Raíz temporal con backlog real y configuración fija, sin procesos ni red."""

    def setUp(self):
        """Aísla disco, configuración, avisos y consola."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / 'docs/plan/tasks').mkdir(parents=True)
        (self.root / 'docs/plan/bugs').mkdir(parents=True)
        motor.AVISOS_PERFIL.clear()
        self.enterContext(patch.dict(motor.os.environ, {}, clear=True))
        self.enterContext(patch.object(motor, 'config', side_effect=lambda root: CONFIG))
        self.enterContext(patch.object(motor, 'excluir'))
        self.enterContext(patch.object(motor, 'ahora', return_value='2026-10-27T12:00:00+00:00'))
        self.aviso = self.enterContext(patch.object(motor, 'avisar'))
        self.consola = self.enterContext(patch('builtins.print'))

    def tarea(self, extra, iid='T-X-0001', dificultad=None):
        """Escribe una tarea con el frontmatter indicado y la devuelve."""
        extra = (f'dificultad: {dificultad}\n' if dificultad else '') + extra
        f = self.root / f'docs/plan/tasks/{iid}.md'
        f.write_text(TAREA.replace('T-X-0001', iid).replace('{extra}', extra), encoding='utf-8')
        return f


class LecturaYValidacionTests(PerfilFijadoBase):
    """El campo opcional se lee en sus dos formas y se rechaza lo inválido."""

    def test_sin_perfil_nada_cambia(self):
        """Sin el campo, el perfil es exactamente el de la dificultad."""
        self.tarea('', dificultad='dificil')
        self.assertIsNone(motor.perfil_de(self.root, 'T-X-0001'))
        self.assertEqual(motor.rol_de(self.root, 'task-dev', 'dificil', iid='T-X-0001'),
                         motor.rol_de(self.root, 'task-dev', 'dificil'))
        self.assertEqual(motor.rol_de(self.root, 'task-dev', 'dificil')[1]['model'], 'opus')

    def test_perfil_unico_en_flujo_y_en_bloque(self):
        """Ambas sintaxis YAML dan el mismo perfil único."""
        self.tarea('perfil: {harness: claude, model: claude-opus-5-5, effort: high}\n')
        flujo = motor.perfil_de(self.root, 'T-X-0001')
        self.tarea('perfil:\n  harness: claude\n  model: claude-opus-5-5\n  effort: high\n')
        self.assertEqual(motor.perfil_de(self.root, 'T-X-0001'), flujo)
        self.assertEqual(flujo['unico'], {'harness': 'claude', 'model': 'claude-opus-5-5', 'effort': 'high'})
        self.assertFalse(flujo['estricto'])

    def test_perfil_por_rol(self):
        """Cada rol lee solo su perfil, en bloque o en flujo."""
        self.tarea('perfil:\n  artemisa: {model: opus}\n  hades:\n    model: haiku\n    effort: low\n')
        perfil = motor.perfil_de(self.root, 'T-X-0001')
        self.assertEqual(perfil['roles'], {'artemisa': {'model': 'opus'}, 'hades': {'model': 'haiku', 'effort': 'low'}})
        self.assertIsNone(perfil['unico'])

    def test_perfiles_invalidos_se_informan(self):
        """Arnés, esfuerzo, rol, campo y forma inválidos dan un error claro con el ID."""
        casos = {
            'perfil: {harness: nube, model: x}\n': 'arnés no soportado "nube"',
            'perfil: {model: x, effort: enorme}\n': 'esfuerzo no válido "enorme"',
            'perfil: {artemis: {model: x}}\n': 'rol desconocido "artemis"',
            'perfil: {modelo: x}\n': 'campo desconocido "modelo"',
            'perfil: opus\n': 'debe ser un mapa',
            'perfil: {model: x, estricto: quizas}\n': '"estricto" debe ser true o false',
            'perfil: {model: x, hades: {model: y}}\n': 'mezcla campos sueltos',
            'perfil: {estricto: true}\n': 'indica al menos',
        }
        for extra, mensaje in casos.items():
            with self.subTest(extra=extra):
                self.tarea(extra)
                errores = motor.errores_perfil(motor.backlog(self.root))
                self.assertTrue(errores and errores[0].startswith('T-X-0001: '), errores)
                self.assertIn(mensaje, ' '.join(errores))
                self.assertIsNone(motor.perfil_de(self.root, 'T-X-0001'))

    def test_perfil_invalido_para_el_bucle_sin_lanzar_paso(self):
        """El estado se detiene con el error del backlog, igual que las dependencias inválidas."""
        for nombre in ('task_config.yaml',):
            (self.root / nombre).write_text('levels: {}\n', encoding='utf-8')
        docs = self.root / 'docs'
        for nombre, texto in (('requirements/requirements.md', 'x'), ('requirements/req_analysis.md', 'ok'),
                              ('requirements/platform_plan.md', 'x'),
                              ('requirements/platform_review.md', '**Veredicto:** APROBADO'),
                              ('requirements/work_plan.md', 'x')):
            (docs / nombre).parent.mkdir(parents=True, exist_ok=True)
            (docs / nombre).write_text(texto, encoding='utf-8')
        self.tarea('perfil: {harness: nube}\n')
        e = motor.estado(self.root, 'docs/requirements')
        self.assertEqual(e[0], 'PARAR')
        self.assertIn('T-X-0001', e[1])
        self.assertIn('arnés no soportado', e[1])

    def test_perfil_invalido_de_tarea_cerrada_no_para(self):
        """Solo cuentan las pendientes."""
        f = self.tarea('perfil: {harness: nube}\n')
        f.write_text(f.read_text(encoding='utf-8').replace('status: planned', 'status: completed'), encoding='utf-8')
        self.assertEqual(motor.errores_perfil(motor.backlog(self.root)), [])

    def test_los_pasos_no_cambian_el_perfil(self):
        """Promover la dificultad solo toca `dificultad`."""
        f = self.tarea('perfil: {model: opus, effort: high}\n', dificultad='media')
        antes = motor.perfil_de(self.root, 'T-X-0001')
        self.assertEqual(motor.promover_dificultad(self.root, 'T-X-0001'), 'dificil')
        self.assertIn('perfil: {model: opus, effort: high}', f.read_text(encoding='utf-8'))
        self.assertEqual(motor.perfil_de(self.root, 'T-X-0001'), antes)


class PrecedenciaTests(PerfilFijadoBase):
    """El perfil fijado sustituye al de dificultad y se completa desde él."""

    def test_unico_sustituye_y_completa_desde_la_dificultad(self):
        """Falta `effort`: se toma del perfil que tocaría por dificultad."""
        self.tarea('perfil: {model: claude-opus-5-5}\n', dificultad='dificil')
        rol, cfg = motor.rol_de(self.root, 'task-dev', 'dificil', iid='T-X-0001')
        self.assertEqual((rol, cfg['harness'], cfg['model'], cfg['effort']), ('artemisa', 'claude', 'claude-opus-5-5', 'high'))
        self.assertTrue(cfg['fijado'])
        self.tarea('perfil: {model: haiku}\n', dificultad='media')
        self.assertEqual(motor.rol_de(self.root, 'bug-fix', 'media', iid='T-X-0001')[1]['effort'], 'medium')

    def test_unico_solo_afecta_al_rol_del_paso(self):
        """El perfil único no toca a Atenea ni a Hades."""
        self.tarea('perfil: {model: opus}\n')
        self.assertEqual(motor.rol_de(self.root, 'especificar', 'media', iid='T-X-0001')[1]['model'], 'sonnet')
        self.assertEqual(motor.aplicar_perfil(self.root, 'T-X-0001', 'hades', CONFIG['hades']), CONFIG['hades'])

    def test_perfil_por_rol_llega_a_los_subagentes(self):
        """Hades y Atenea usan el suyo; Artemisa, sin entrada, conserva el de dificultad."""
        self.tarea('perfil:\n  hades: {model: haiku}\n  atenea: {model: opus, effort: max}\n')
        self.assertEqual(motor.aplicar_perfil(self.root, 'T-X-0001', 'hades', CONFIG['hades'])['model'], 'haiku')
        self.assertEqual(motor.rol_de(self.root, 'especificar', 'media', iid='T-X-0001')[1]['effort'], 'max')
        self.assertEqual(motor.rol_de(self.root, 'task-dev', 'media', iid='T-X-0001')[1]['model'], 'sonnet')

    def test_reservas_de_la_dificultad_se_conservan_completas(self):
        """Las reservas heredan del perfil por dificultad, no del fijado."""
        self.tarea('perfil: {harness: codex, model: gpt-x}\n')
        cfg = motor.rol_de(self.root, 'task-dev', 'media', iid='T-X-0001')[1]
        self.assertEqual([(r['harness'], r['model']) for r in motor.lista_reservas(cfg)],
                         [('claude', 'haiku'), ('codex', 'gpt')])

    def test_agentes_lo_muestra_como_fijado(self):
        """`--agentes` marca los perfiles fijados por la tarea."""
        self.tarea('perfil: {model: opus}\n')
        with (patch.object(motor, 'estado', return_value=('PASO', 'task-dev', 'T-X-0001', '')),
              patch.object(motor, 'cuota_codex', return_value=None)):
            informe = motor.informe_agentes(self.root)
        self.assertIn('artemisa: claude/opus (medium) [fijado por la tarea]', informe)
        self.assertNotIn('hades: claude/sonnet [fijado', informe)

    def test_comentario_final_en_el_perfil(self):
        """Un comentario YAML tras el perfil, en flujo o en bloque, no lo invalida."""
        for extra in ('perfil: {model: opus, effort: high}  # solo esta tarea\n',
                      'perfil:  # solo esta tarea\n  model: opus  # caro\n  effort: high\n'):
            with self.subTest(extra=extra):
                self.tarea(extra)
                self.assertEqual(motor.perfil_de(self.root, 'T-X-0001')['unico'], {'model': 'opus', 'effort': 'high'})
        self.tarea('perfil: {model: "a#b"}\n')
        self.assertEqual(motor.perfil_de(self.root, 'T-X-0001')['unico'], {'model': 'a#b'})


class BucleTests(PerfilFijadoBase):
    """Reservas con aviso, estricto y bloqueo, ejercitados en el bucle real."""

    def setUp(self):
        """Tarea fijada y arneses simulados."""
        super().setUp()
        self.fijado = {'harness': 'claude', 'model': 'opus'}
        self.ausente = self.enterContext(patch.object(motor, 'buscar_ejecutable',
            side_effect=lambda exe: None if exe == 'claude' else exe))
        self.lanzar = self.enterContext(patch.object(motor, 'lanzar',
            return_value=(0, {'sesion': 'nueva'}, 'respuesta')))
        self.bloquear = self.enterContext(patch.object(motor, 'bloquear_sin_progreso'))

    def bucle(self, paso='task-dev', progreso=True, reintentos=2):
        """Un único paso del bucle con git y firma simulados."""
        args = motor.argparse.Namespace(idea=None, docs='docs', test=None, harness=None, estado=False,
                                        max_pasos=2, reintentos=reintentos, espera_max=2, cmd=None, presupuesto=None)
        with (patch.object(motor, 'iniciar_gateway'),
              patch.object(motor, 'recargar_version', return_value=False),
              patch.object(motor, 'ingerir', return_value=[]),
              patch.object(motor, 'estado', side_effect=[('PASO', paso, 'T-X-0001', ''), ('FIN', 'ok')]),
              patch.object(motor, 'firma', side_effect=['antes', 'despues' if progreso else 'antes']),
              patch.object(motor, 'git', return_value=''),
              patch.object(motor, 'buscar_sesion_paso', return_value=None),
              patch.object(motor, 'esperar', return_value=False) as esperar):
            return motor.bucle(args, self.root), esperar

    def avisos_de_perfil(self):
        """Avisos de que el perfil fijado cede ante una reserva."""
        return [c for c in self.aviso.call_args_list if 'perfil fijado' in c.args[2]]

    def test_arnes_ausente_usa_la_reserva_y_avisa_una_vez(self):
        """Sin el arnés fijado se sigue con las reservas de la dificultad y se avisa una sola vez."""
        self.tarea('perfil: {harness: claude, model: opus}\n')
        codigo, _ = self.bucle()
        self.assertEqual(codigo, 0)
        self.assertEqual(self.lanzar.call_args.args[2], 'codex')
        self.assertFalse(motor.leer_metricas(self.root)[-1].get('perfil_fijado'))
        avisos = self.avisos_de_perfil()
        self.assertEqual(len(avisos), 1)
        self.assertIn('T-X-0001: perfil fijado claude/opus sin arnés; uso la reserva codex/gpt', avisos[0].args[2])

    def test_perfil_disponible_se_marca_como_fijado(self):
        """Lo ejecutado con el perfil fijado lleva la marca en métricas, sin avisos."""
        self.ausente.side_effect = lambda exe: exe
        self.tarea('perfil: {harness: claude, model: opus}\n')
        codigo, _ = self.bucle()
        self.assertEqual(codigo, 0)
        self.assertIn('opus', self.lanzar.call_args.args[0])
        self.assertTrue(motor.leer_metricas(self.root)[-1].get('perfil_fijado'))
        self.assertEqual(self.avisos_de_perfil(), [])

    def test_sin_cuota_usa_la_reserva_y_avisa(self):
        """Con el perfil fijado agotado se sigue con la primera reserva disponible."""
        self.ausente.side_effect = lambda exe: exe
        self.tarea('perfil: {harness: claude, model: opus}\n')
        with patch.object(motor, 'configuraciones_con_cuota',
                          side_effect=lambda root, cfgs: [c for c in cfgs if c.get('model') != 'opus']):
            codigo, _ = self.bucle()
        self.assertEqual(codigo, 0)
        self.assertEqual(self.lanzar.call_count, 1)
        self.assertIn('haiku', self.lanzar.call_args.args[0])
        self.assertEqual(len(self.avisos_de_perfil()), 1)
        fila = [f for f in motor.leer_metricas(self.root) if f.get('tipo') == 'paso'][-1]
        self.assertFalse(fila.get('perfil_fijado'))
        self.assertIn('sin cuota', self.avisos_de_perfil()[0].args[2])

    def test_estricto_sin_cuota_espera_sin_cambiar_de_modelo(self):
        """Con `estricto` no se usa ninguna reserva: el bucle espera la cuota."""
        self.ausente.side_effect = lambda exe: exe
        self.tarea('perfil: {harness: claude, model: opus, estricto: true}\n')
        with (patch.object(motor, 'configuraciones_con_cuota', return_value=[]),
              patch.object(motor, 'cuota_descartada', side_effect=lambda root, orig, sel, **kw: (30, orig[0]))):
            codigo, esperar = self.bucle()
        self.assertEqual(codigo, 2)
        esperar.assert_called_once()
        self.lanzar.assert_not_called()
        self.bloquear.assert_not_called()
        self.assertEqual(self.avisos_de_perfil(), [])

    def test_estricto_con_arnes_ausente_bloquea_para_la_persona(self):
        """El arnés no existe y no se cambia de modelo: la tarea se bloquea."""
        self.tarea('perfil: {harness: claude, model: opus, estricto: true}\n')
        self.bucle()
        self.lanzar.assert_not_called()
        self.bloquear.assert_called_once()
        self.assertIn('estricto', self.bloquear.call_args.kwargs['causa'])
        self.assertIn('"claude"', self.bloquear.call_args.kwargs['causa'])

    def test_estricto_bloquea_en_lugar_de_escalar(self):
        """Tras los rechazos que escalarían o subirían la dificultad, se bloquea."""
        self.ausente.side_effect = lambda exe: exe
        self.tarea('perfil: {harness: claude, model: opus, estricto: true}\n', dificultad='media')
        with patch.object(motor, 'reintentos_acumulados', return_value=(1, 2)):
            self.bucle()
        self.lanzar.assert_not_called()
        self.bloquear.assert_called_once()
        self.assertIn('2 rechazos seguidos de Hades', self.bloquear.call_args.kwargs['causa'])
        self.assertEqual(motor.dificultad_de(self.root, 'T-X-0001'), 'media')

    def test_estricto_en_dificil_no_bloquea_por_ejecuciones(self):
        """En `dificil` el flujo normal no cambia de modelo, así que el estricto tampoco bloquea."""
        self.ausente.side_effect = lambda exe: exe
        self.tarea('perfil: {harness: claude, model: opus, estricto: true}\n', dificultad='dificil')
        with patch.object(motor, 'reintentos_acumulados', return_value=(3, 0)):
            self.bucle()
        self.bloquear.assert_not_called()
        self.lanzar.assert_called_once()

    def test_estricto_en_dificil_bloquea_al_escalar(self):
        """En `dificil` el tope de rechazos que escalaría bloquea la tarea."""
        self.ausente.side_effect = lambda exe: exe
        self.tarea('perfil: {harness: claude, model: opus, estricto: true}\n', dificultad='dificil')
        with (patch.object(motor, 'reintentos_acumulados', return_value=(0, 0)),
              patch.object(motor, 'rechazos', return_value=2)):
            self.bucle()
        self.lanzar.assert_not_called()
        self.bloquear.assert_called_once()
        self.assertIn('2 rechazos seguidos de Hades', self.bloquear.call_args.kwargs['causa'])

    def test_estricto_sin_progreso_bloquea_en_lugar_de_subir_la_dificultad(self):
        """Tras los intentos sin progreso se bloquea y la dificultad no cambia."""
        self.ausente.side_effect = lambda exe: exe
        self.tarea('perfil: {harness: claude, model: opus, estricto: true}\n', dificultad='media')
        self.bucle(progreso=False, reintentos=1)
        self.bloquear.assert_called_once()
        self.assertEqual(motor.dificultad_de(self.root, 'T-X-0001'), 'media')

    def test_no_estricto_sigue_escalando_y_promoviendo(self):
        """Sin `estricto`, la promoción actúa como hoy."""
        self.ausente.side_effect = lambda exe: exe
        self.tarea('perfil: {harness: claude, model: opus}\n', dificultad='media')
        with patch.object(motor, 'reintentos_acumulados', return_value=(3, 0)):
            self.bucle()
        self.assertEqual(motor.dificultad_de(self.root, 'T-X-0001'), 'dificil')
        self.bloquear.assert_not_called()

    def test_estricto_en_analisis_no_amplia_la_cadena(self):
        """Los pasos de análisis de una tarea estricta no pasan a otros modelos."""
        self.tarea('perfil:\n  atenea: {model: opus}\n  estricto: true\n')
        cadena = motor.cadena_analisis(self.root, 'especificar', 'media', 'T-X-0001')
        self.assertEqual([c['model'] for c in cadena], ['opus'])


class AltaTests(PerfilFijadoBase):
    """Las altas desde Telegram aceptan el perfil al crear la tarea."""

    def test_extraer_perfil(self):
        """`--perfil` y `--estricto` salen del título."""
        self.assertEqual(motor.extraer_perfil('Arreglar login'), ('Arreglar login', None, None))
        titulo, perfil, error = motor.extraer_perfil('Arreglar login --perfil claude/opus/high --estricto')
        self.assertEqual((titulo, error), ('Arreglar login', None))
        self.assertEqual(perfil, {'harness': 'claude', 'model': 'opus', 'effort': 'high', 'estricto': 'true'})
        self.assertIn('arnés no soportado', motor.extraer_perfil('x --perfil nube/m')[2])
        self.assertIn('estricto', motor.extraer_perfil('x --estricto')[2])

    def test_alta_escribe_un_perfil_valido(self):
        """La tarea creada con perfil pasa la validación y se lee igual."""
        _, perfil, _ = motor.extraer_perfil('Cambio mecánico --perfil claude/haiku/low --estricto')
        iid, f = motor.alta(self.root, 'tarea', 'Cambio mecánico', 'u1', perfil)
        leido = motor.perfil_de(self.root, iid)
        self.assertEqual(leido, {'unico': {'harness': 'claude', 'model': 'haiku', 'effort': 'low'},
                                 'roles': {}, 'estricto': True})
        iid2, _ = motor.alta(self.root, 'bug', 'Sin perfil', 'u1')
        self.assertIsNone(motor.perfil_de(self.root, iid2))

    def test_buzon_conserva_el_perfil(self):
        """El perfil viaja del gateway al backlog por el buzón."""
        with patch.object(motor.subprocess, 'run'):
            motor.apuntar(self.root, 'tarea', 'Con perfil', 'u1', {'model': 'opus'})
            (iid, _), = motor.ingerir(self.root)
        self.assertEqual(motor.perfil_de(self.root, iid)['unico'], {'model': 'opus'})


if __name__ == '__main__':
    unittest.main()
