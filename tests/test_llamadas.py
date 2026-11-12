"""Regresión de T-AFN-0147 y contrato compartido de llamadas."""
import tempfile
import json
import os
import subprocess
import sys
from io import StringIO
from contextlib import redirect_stdout
import unittest
from pathlib import Path
from unittest.mock import patch

from adevv import llamadas
from skills.orquestar import test_progreso as soporte

motor = soporte.motor


class LlamadasTests(unittest.TestCase):
    setUp = soporte.ProgresoTests.setUp
    escribir = soporte.ProgresoTests.escribir
    crear_ficha = soporte.ProgresoTests.crear_ficha
    commit = soporte.ProgresoTests.commit
    git = soporte.ProgresoTests.git
    ejecutar = soporte.ProgresoTests.ejecutar
    filas = soporte.ProgresoTests.filas
    iid = 'T-AFN-0147'

    def test_afinn_ratifica_especificacion_y_rechaza_codigo_sin_arrastrar_cuota(self):
        self.escribir('orchestration.json', '{"hades":{"harness":"agy","model":"argon",'
                      '"reserva":[{"harness":"codex","model":"reserva"}]}}')
        motor.registrar(self.root, dict(tipo='agente', fecha=motor.ahora(), arnes='agy',
                                        modelo_cuota='argon', cuota_espera_s=86400))
        def accion(n):
            if n == 2:
                self.assertEqual(motor.frontmatter(self.ficha)['status'], 'planned')
                self.assertIn('corregir el diálogo', self.ficha.read_text(encoding='utf-8'))
                self.escribir('producto.py', 'def doble(n):\n    return n * 2\n')
                return 0, 'Artemisa recibió la corrección del diálogo'
            with (patch.dict(motor.os.environ, self.entorno),
                  patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe),
                  patch.object(motor, 'lanzar') as proveedor):
                proveedor.return_value = (0, {}, 'Veredicto formal para **T-AFN-0147: APROBADO**.')
                with patch.dict(motor.os.environ, ORQUESTAR_REVISION='spec'):
                    self.assertEqual(motor.agente(self.root, 'hades', 'especificación'), 1)
                proveedor.return_value = (0, {}, '**Veredicto:** APROBADO')
                with patch.dict(motor.os.environ, ORQUESTAR_REVISION='spec'):
                    self.assertEqual(motor.agente(self.root, 'hades', 'ratificación'), 0)
                proveedor.return_value = (0, {}, '**Veredicto:** RECHAZADO')
                with patch.dict(motor.os.environ, ORQUESTAR_REVISION='code'):
                    self.assertEqual(motor.agente(self.root, 'hades', 'código'), 0)
            motor.enrutar_hallazgo(self.root,self.iid,'artemisa',contexto='Hades: corregir el diálogo')
            return 0, 'Hallazgo enrutado a Artemisa'
        def ejecutar(args, root, prompt, env, rol, **kwargs):
            self.entorno = env
            return soporte.ProgresoTests.ejecutar(self, args, root, prompt, env, rol, **kwargs)
        self.accion = accion
        self.args.max_pasos = 2
        with patch.object(motor, 'ejecutar', side_effect=ejecutar):
            self.assertEqual(motor.bucle(self.args, self.root), 2)
        self.assertEqual(len(self.llamadas), 2)
        self.assertTrue(all(not f.get('bloqueo_agente') for f in self.filas()))
        self.assertFalse(motor.configuraciones_con_cuota(self.root, [{'harness':'agy','model':'argon'}]))

    def test_resultados_aislan_alcances_y_sobreviven_al_reinicio(self):
        with tempfile.TemporaryDirectory() as tmp:
            for inv, objetivo, estado, veredicto in (
                ('2540af11', 'spec', 'espera_cuota', ''),
                ('pruebas', 'test', 'recibida', 'APROBADO'),
                ('c8dbc875', 'spec', 'recibida', 'APROBADO'),
                ('db7b4a05', 'code', 'recibida', 'RECHAZADO')):
                r = llamadas.Resultado(inv, self.iid, 'task-dev', 'hades', estado, 0,
                    objetivo=objetivo, entradas='mismo-candidato', veredicto=veredicto)
                llamadas.publicar(tmp, r)
                if inv == 'pruebas':
                    self.assertEqual([x.invocacion for x in llamadas.pendientes(llamadas.leer(tmp))], ['2540af11'])
            self.assertEqual(llamadas.pendientes(llamadas.leer(tmp)), [])
            self.assertEqual(len(llamadas.leer(tmp)), 4)
            codigo = ('import sys; sys.path.insert(0,sys.argv[1]); from adevv.llamadas import leer,pendientes; '
                      'assert len(leer(sys.argv[2]))==4; assert pendientes(leer(sys.argv[2]))==[]')
            subprocess.run([sys.executable,'-B','-c',codigo,str(Path(__file__).resolve().parents[1]),tmp],check=True)

    def test_identidad_desconocida_no_cancela_otra_invocacion(self):
        a = llamadas.Resultado('vieja', self.iid, 'task-dev', 'hades', 'espera_cuota', 1)
        b = llamadas.Resultado('nueva', self.iid, 'task-dev', 'hades', 'recibida', 0)
        self.assertEqual(llamadas.pendientes([a,b]), [a])

    def test_espera_concurrente_tardia_no_revoca_ratificacion(self):
        antigua=llamadas.Resultado('antigua',self.iid,'task-dev','hades','espera_cuota',1,
            objetivo='spec',entradas='candidato',iniciada=1,orden=4)
        nueva=llamadas.Resultado('ratificacion',self.iid,'task-dev','hades','recibida',0,
            objetivo='spec',entradas='candidato',iniciada=2,orden=3)
        self.assertEqual(llamadas.pendientes([antigua,nueva]),[])

    def test_un_canal_no_oculta_otra_llamada_legacy_pendiente(self):
        self.escribir('orchestration.json','{"hades":{"harness":"codex","model":"juez"}}')
        def accion(n):
            with (patch.dict(os.environ,self.entorno),patch.dict(os.environ,ORQUESTAR_REVISION='spec'),
                  patch.object(motor,'buscar_ejecutable',side_effect=lambda exe:exe),
                  patch.object(motor,'lanzar',return_value=(0,{},'APROBADO'))):
                self.assertEqual(motor.agente(self.root,'hades','especificación'),0)
            motor.registrar(self.root,dict(tipo='agente',fecha=motor.ahora(),rol='hades',paso='task-dev',
                id=self.iid,arnes='agy',modelo_cuota='otro',sin_cuota=True,espera_s=3600,invocacion='legacy'))
            return 0,'espera de otro revisor'
        def ejecutar(args,root,prompt,env,rol,**kwargs):
            self.entorno=env
            return soporte.ProgresoTests.ejecutar(self,args,root,prompt,env,rol,**kwargs)
        self.accion=accion
        with patch.object(motor,'ejecutar',side_effect=ejecutar):
            self.assertEqual(motor.bucle(self.args,self.root),2)
        self.assertEqual(self.filas()[-1]['bloqueo_agente']['invocacion'],'legacy')
        self.assertTrue(self.filas()[-1]['correlacion_desconocida'])

    def test_fallo_de_hades_no_se_convierte_en_exito_del_padre(self):
        self.escribir('orchestration.json','{"hades":{"harness":"codex","model":"juez"}}')
        def accion(n):
            with (patch.dict(os.environ,self.entorno),patch.dict(os.environ,ORQUESTAR_REVISION='spec'),
                  patch.object(motor,'buscar_ejecutable',side_effect=lambda exe:exe),
                  patch.object(motor,'lanzar',return_value=(1,{},'Error técnico'))):
                self.assertEqual(motor.agente(self.root,'hades','especificación'),1)
            return 0,'padre terminó'
        def ejecutar(args,root,prompt,env,rol,**kwargs):
            self.entorno=env
            return soporte.ProgresoTests.ejecutar(self,args,root,prompt,env,rol,**kwargs)
        self.accion=accion
        with patch.object(motor,'ejecutar',side_effect=ejecutar):
            self.assertEqual(motor.bucle(self.args,self.root),2)
        self.assertTrue(self.filas()[-1]['revision_pendiente'])
        self.assertEqual(motor.frontmatter(self.ficha)['status'],'in_progress')

    def test_politica_comun_reserva_espera_y_conservacion(self):
        r = llamadas.Resultado('pendiente', self.iid, 'task-dev', 'hades', 'espera_cuota', 1, espera_s=3600)
        self.assertEqual(llamadas.recuperacion(r, hay_reserva=True), 'reserva')
        self.assertEqual(llamadas.recuperacion(r, limite=3600), 'esperar')
        self.assertEqual(llamadas.recuperacion(r, limite=0), 'conservar')

    def test_cli_del_rol_entrega_resultado_al_proceso_padre(self):
        self.escribir('orchestration.json','{"hades":{"harness":"codex","model":"juez"}}')
        script = (
            'import sys;sys.path.insert(0,sys.argv[1]);'
            'from tests.test_orquestar import motor;'
            'motor.buscar_ejecutable=lambda exe:exe;'
            'motor.lanzar=lambda *a,**k:(0,{}, "RECHAZADO");'
            'sys.argv=["orquestar","--agente","hades","--revision","spec","--prompt","revisar"];'
            'raise SystemExit(motor.main())')
        with tempfile.TemporaryDirectory() as canal:
            env={**os.environ,'ORQUESTAR_CANAL':canal,'ORQUESTAR_LLAMADA':'padre-real',
                 'ORQUESTAR_ID':self.iid,'ORQUESTAR_PASO':'task-dev'}
            subprocess.run([sys.executable,'-B','-c',script,str(Path(__file__).resolve().parents[1])],
                           env=env,check=True,capture_output=True)
            resultado,=llamadas.leer(canal)
            self.assertEqual((resultado.padre,resultado.objetivo,resultado.veredicto),
                             ('padre-real','spec','RECHAZADO'))
            self.assertEqual(resultado.perfil['model'],'juez')

    def test_reserva_roles_y_diagnostico_comparten_resultado(self):
        self.escribir('orchestration.json', json.dumps({'hades': {'harness':'agy','model':'argon',
                      'reserva':[{'harness':'codex','model':'reserva'}]}}))
        dictamen = json.dumps({'causa':'espera de cierre','decision':'investigar','destino':'desarrollador',
                    'terminal':{'destino':'tecnico','responsable':'equipo','intervencion':'corregir'}})
        proceso_real = subprocess.run
        for diagnostico in (False, True):
            for modo in ('reserva', 'cuota', 'fallo', 'sin_dictamen'):
                with self.subTest(diagnostico=diagnostico, modo=modo), tempfile.TemporaryDirectory() as canal:
                    resultados = []
                    inicio_metricas=len(motor.leer_metricas(self.root))
                    modo_actual=modo
                    def proveedor(cmd, root, harness, **kwargs):
                        resultados.append(harness)
                        consumo={'modelos':{harness:{'entrada':7}}}
                        if modo_actual == 'cuota' or (modo_actual == 'reserva' and harness == 'agy'):
                            return 1, consumo, 'out of credits'
                        if modo_actual == 'fallo':
                            return 1, consumo, 'Error de ejecución'
                        if modo_actual == 'sin_dictamen':
                            print('No hay entrega')
                            return 0, consumo, 'No hay entrega'
                        print(dictamen if diagnostico else 'RECHAZADO')
                        return 0, consumo, dictamen if diagnostico else 'RECHAZADO'
                    def proceso(args, *a, **kw):
                        if args[:3] != ['adevv','orquestar','--agente']:
                            return proceso_real(args, *a, **kw)
                        salida = StringIO()
                        with patch.dict(os.environ, kw['env']), redirect_stdout(salida):
                            codigo = motor.agente(self.root, 'hades', 'diagnosticar')
                        return subprocess.CompletedProcess(args,codigo,salida.getvalue(),'')
                    motor.reset_cuotas(self.root, None)
                    with (patch.dict(os.environ, ORQUESTAR_ID=self.iid, ORQUESTAR_PASO='task-dev',
                                     ORQUESTAR_CANAL=canal, ORQUESTAR_REVISION='spec', ORQUESTAR_LLAMADA='padre-prueba'),
                          patch.object(motor, 'buscar_ejecutable', side_effect=lambda exe: exe),
                          patch.object(motor, 'lanzar', side_effect=proveedor),
                          patch.object(subprocess, 'run', side_effect=proceso)):
                        if diagnostico:
                            grupo={'solicitud':'f'*64,'evidencias':[]}
                            if modo == 'reserva':
                                r=motor.diagnostico_suite.solicitar(self.root,self.iid,'suite',grupo,self.root/'historial.json')
                                self.assertEqual(r['destino'],'desarrollador')
                            else:
                                with self.assertRaises(motor.diagnostico_suite.DiagnosticoPendiente) as exc:
                                    motor.diagnostico_suite.solicitar(self.root,self.iid,'suite',grupo,self.root/'historial.json')
                                resultado=exc.exception.resultado
                        else:
                            motor.agente(self.root,'hades','revisión')
                            resultado=llamadas.leer(canal)[-1]
                        if modo != 'reserva' or not diagnostico:
                            esperado={'reserva':'recibida','cuota':'espera_cuota',
                                      'fallo':'fallo_tecnico','sin_dictamen':'entrega_pendiente'}
                            self.assertEqual(resultado.estado, esperado[modo])
                            self.assertEqual(resultado.trabajo,self.iid)
                            self.assertEqual(resultado.rol,'hades')
                            self.assertTrue(resultado.invocacion)
                            self.assertTrue(resultado.padre)
                            self.assertIn(resultado.perfil['harness'],('agy','codex'))
                            if modo != 'cuota':
                                self.assertEqual(resultado.perfil['model'],'reserva')
                        self.assertEqual(resultados, ['agy','codex'])
                        if modo == 'cuota':
                            invocacion_espera=resultado.invocacion
                            motor.reset_cuotas(self.root,None)
                            modo_actual='recuperado'
                            if diagnostico:
                                r=motor.diagnostico_suite.solicitar(self.root,self.iid,'suite',grupo,self.root/'historial.json')
                                self.assertEqual(r['destino'],'desarrollador')
                            else:
                                self.assertEqual(motor.agente(self.root,'hades','revisión'),0)
                                self.assertEqual(llamadas.pendientes(llamadas.leer(canal)),[])
                                self.assertIn(invocacion_espera,[r.invocacion for r in llamadas.leer(canal)])
                            self.assertEqual(resultados,['agy','codex','agy'])
                    coste=sum(m.get('entrada',0) for f in motor.leer_metricas(self.root)[inicio_metricas:]
                              for m in f.get('modelos',{}).values())
                    self.assertEqual(coste,7*len(resultados))

    def test_entrega_contradictoria_conserva_las_fuentes(self):
        self.escribir('orchestration.json','{"hades":{"harness":"codex","model":"juez"}}')
        def respuesta(*args,**kwargs):
            self.escribir(f'docs/review/spec_reviews/{self.iid}-spec-review.md', 'RECHAZADO')
            return 0, {}, 'APROBADO'
        with tempfile.TemporaryDirectory() as canal:
            with (patch.dict(os.environ, ORQUESTAR_ID=self.iid, ORQUESTAR_REVISION='spec', ORQUESTAR_CANAL=canal),
                  patch.object(motor,'buscar_ejecutable',side_effect=lambda exe:exe),
                  patch.object(motor,'lanzar',side_effect=respuesta)):
                motor.agente(self.root,'hades','revisión')
            r=llamadas.leer(canal)[-1]
            self.assertEqual(r.estado,'aclaracion_pendiente')
            self.assertEqual(r.fuentes,{'respuesta':'APROBADO','informe':'RECHAZADO'})
            with (patch.dict(os.environ, ORQUESTAR_ID=self.iid, ORQUESTAR_REVISION='spec', ORQUESTAR_CANAL=canal),
                  patch.object(motor,'buscar_ejecutable',side_effect=lambda exe:exe),
                  patch.object(motor,'lanzar',return_value=(1,{},'out of credits'))):
                self.assertEqual(motor.agente(self.root,'hades','aclarar'),1)
            recibidas=llamadas.leer(canal)
            self.assertEqual(llamadas.pendientes(recibidas)[0].estado,'espera_cuota')
            self.assertEqual(recibidas[0].fuentes,r.fuentes)
            motor.recuperar_cuota(self.root,'codex','juez')
            with (patch.dict(os.environ, ORQUESTAR_ID=self.iid, ORQUESTAR_REVISION='spec', ORQUESTAR_CANAL=canal),
                  patch.object(motor,'buscar_ejecutable',side_effect=lambda exe:exe),
                  patch.object(motor,'lanzar',return_value=(0,{},'RECHAZADO'))):
                self.assertEqual(motor.agente(self.root,'hades','aclarar'),0)
            self.assertEqual(llamadas.pendientes(llamadas.leer(canal)),[])
            self.assertEqual(len(llamadas.leer(canal)),3)

    def test_paso_principal_reserva_y_relanzamiento_sin_cuota(self):
        texto=self.ficha.read_text(encoding='utf-8')
        self.ficha.write_text('\n'.join(l for l in texto.splitlines() if not l.startswith('perfil:'))+'\n',encoding='utf-8')
        original=self.ficha.read_bytes()
        self.escribir('orchestration.json',json.dumps({'development':{'harness':'codex','model':'principal',
            'reserva':[{'harness':'agy','model':'reserva'}]}}))
        self.accion=lambda n:(1,'out of credits')
        self.args.max_pasos=1
        self.assertEqual(motor.bucle(self.args,self.root),2)
        self.assertEqual(self.perfiles,['principal','reserva'])
        self.assertEqual(self.ficha.read_bytes(),original)
        for harness, modelo in (('codex','principal'),('agy','reserva')):
            motor.recuperar_cuota(self.root,harness,modelo)
        self.accion=lambda n:(0,'entrega del trabajo pendiente')
        self.assertEqual(motor.bucle(self.args,self.root),2)
        self.assertEqual(self.perfiles,['principal','reserva','principal'])
        self.assertEqual(self.ficha.read_bytes(),original)
        coste=sum(m.get('entrada',0) for f in self.filas() for m in f.get('modelos',{}).values())
        self.assertEqual(coste,33)

    def test_rol_estricto_conserva_perfil_y_espera(self):
        texto=self.ficha.read_text(encoding='utf-8')
        texto=texto.replace('perfil: {harness: codex, model: potente, estricto: true}',
                            'perfil: {hades: {harness: agy, model: argon}, estricto: true}')
        self.ficha.write_text(texto,encoding='utf-8')
        self.escribir('orchestration.json',json.dumps({'hades':{'harness':'agy','model':'argon',
            'reserva':[{'harness':'codex','model':'reserva'}]}}))
        with tempfile.TemporaryDirectory() as canal:
            with (patch.dict(os.environ,ORQUESTAR_ID=self.iid,ORQUESTAR_REVISION='spec',ORQUESTAR_CANAL=canal),
                  patch.object(motor,'buscar_ejecutable',side_effect=lambda exe:exe),
                  patch.object(motor,'lanzar',return_value=(1,{},'out of credits')) as proveedor):
                self.assertEqual(motor.agente(self.root,'hades','especificación'),1)
            self.assertEqual(proveedor.call_count,1)
            resultado=llamadas.leer(canal)[-1]
            self.assertEqual(resultado.estado,'espera_cuota')
            self.assertEqual(resultado.perfil['model'],'argon')
