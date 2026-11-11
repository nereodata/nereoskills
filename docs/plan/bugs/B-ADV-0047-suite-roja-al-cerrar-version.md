---
id: B-ADV-0047
title: "La suite falla al cerrar la versión"
type: bug
weight: 10
dificultad: media
version: "v1.1.3"
status: planned
depende_de: []
created_at: 2026-11-11
suite_cierre: true
suite_clave: f992801fe955b479570e4395bb2ea2ac9a927ac38686d061b5dbcd534ed68680
updated_at: 2026-11-11
suite_dificultad: media
suite_intentos: 0
suite_accion: ninguna
---

# B-ADV-0047: La suite falla al cerrar la versión

## Descripción del fallo
La suite completa de cierre devuelve un código distinto de cero. Debe pasar antes de revisar o cerrar la versión.

## Reproducir
Ejecutar el comando indicado en la evidencia desde la raíz del proyecto.

## Último fallo de suite
- Comando: "python -m unittest discover -s tests"
- Código: 1; árbol: 6fe188aa84ca26bf6f6cfb81fe01783d33cdb169; fecha: 2026-11-11T20:10:13

    ........[master (root-commit) 3e6c769] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 2acfc3b] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 45e7f77] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 5943c7a] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 9452f59] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) b7490e7] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) 7d9943f] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) cb0b21c] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) 866027a] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) 6c69c78] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    ..[master (root-commit) 02654dd] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .....F..FFFFF.FF.To C:\Users\IVNMOR~1\AppData\Local\Temp\tmp6u8bes2c\origin.git
     * [new tag]         v0.1.0 -> v0.1.0
    [main 01a15ba] feat: bump v0.1.1
     1 file changed, 1 insertion(+), 1 deletion(-)
    To C:\Users\IVNMOR~1\AppData\Local\Temp\tmp6u8bes2c\origin.git
       7005880..01a15ba  main -> main
     * [new tag]         v0.1.1 -> v0.1.1
    ................
    [orquestar] 1. PARAR: Versi�n v0.1 terminada.
    [orquestar] PARAR: Versi�n v0.1 terminada.
    
    [orquestar] 1. PARAR: Versi�n v0.1 terminada.
    [orquestar] PARAR: Versi�n v0.1 terminada.
    
    [orquestar] 1. PARAR: Versi�n v0.1 terminada.
    [orquestar] PARAR: Versi�n v0.1 terminada.
    .
    [orquestar] 1. PARAR: Requisitos con preguntas sin valor por defecto seguro.
    [orquestar] PARAR: Requisitos con preguntas sin valor por defecto seguro.
    ..
    [orquestar] 1. PARAR: Versi�n v0.1 terminada.
    [orquestar] PARAR: Versi�n v0.1 terminada.
    .
    [orquestar] 1. PASO: task-dev T1
    
    [orquestar] 2. PASO: task-dev T1
    [orquestar] PARAR: el arn�s termin� con c�digo 1 (sin cuota tras esperar 1.0 h (--espera-max)). Relanza cuando se resuelva.
    .[orquestar] mensaje de Telegram no enviado (OSError)
    [orquestar] mensaje de Telegram no enviado (OSError)
    .
    [orquestar] 1. PARAR: Versi�n v0.1 terminada. Revisa
    [orquestar] PARAR: Versi�n v0.1 terminada. Revisa
    
    [orquestar] 1. FIN: Todas las tareas con versi�n est�n cerradas.
    .
    [orquestar] 1. PARAR: Versi�n v0.1 terminada. Revisa
    [orquestar] PARAR: Versi�n v0.1 terminada. Revisa
    
    [orquestar] 1. PARAR: Versi�n v1.1.2 terminada. Revisa
    [orquestar] PARAR: Versi�n v1.1.2 terminada. Revisa
    .............[orquestar] T1: detectada bajada manual de dificultad de dificil a sencilla; reinicio contadores.
    ................ok
    ok
    .
    [orquestar] 1. PASO: task-dev T-ADV-0001
    [orquestar] T-ADV-0001: 2 rechazos seguidos de Hades; escalo a claude-opus-5-5-medium
    [orquestar] PARAR: alcanzado --max-pasos=1.
    .
    [orquestar] 1. PASO: task-dev T-ADV-0001
    
    [orquestar] 2. PASO: task-dev T-ADV-0001
    [orquestar] sin progreso (1/2)
    
    [orquestar] 3. FIN: Cerrado.
    ....
    [orquestar] 1. PASO: task-dev T-ADV-0001
    [orquestar] hades sin cuota: termina el paso sin tocar estados; el bucle esperar� la cuota y reintentar�.
    
    [orquestar] 2. FIN: Cerrado.
    .............................hecho
    hecho
    [orquestar] agy status: ERROR (returncode: 0)
    .......s.....s....[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    .456
    
    123
    
    789
    
    ..[orquestar] verificaci�n reutilizada: "C:\Users\Iv�n Moreno\AppData\Local\Programs\Python\Python312\python.exe" -c "print(789)" ya pas� sobre este mismo �rbol (f56c00c966).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (3 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (4 intentos en dificil).
    .
    [orquestar] 1. PARAR: Versi�n v0.1 terminada. Revisa
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] PARAR: alcanzado --max-pasos=1.
    .
    [orquestar] 1. PASO: revisar-version v0.1 release/v0.1
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] PARAR: alcanzado --max-pasos=1.
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (3 intentos en dificil).
    F[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (3 intentos en dificil).
    F
    [orquestar] 1. PASO: revisar-version v0.1 release/v0.1
    [orquestar] cambios guardados en el stash �orquestar: another 2026-11-11 20:08:25�
    [orquestar] revisar-version v0.1: sin progreso (1/2)
    [orquestar] PARAR: alcanzado --max-pasos=1.
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en media).
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en media).
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en media).
    [orquestar] B-DEM-0001: subo dificultad de media a dificil (3 reca�das de la misma causa)
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en media).
    [orquestar] B-DEM-0001: subo dificultad de media a dificil (3 reca�das de la misma causa)
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en dificil).
    .
    [orquestar] 1. PARAR: Versi�n v1.1.2 terminada. Revisa docs/review/versions/v1.1.2-revision.md: registra defectos con /bug-add o cierra con /release, y relanza.
    [orquestar] PARAR: Versi�n v1.1.2 terminada. Revisa docs/review/versions/v1.1.2-revision.md: registra defectos con /bug-add o cierra con /release, y relanza.
    
    [orquestar] 1. PARAR: Versi�n v1.1.2 terminada. Revisa docs/review/versions/v1.1.2-revision.md: registra defectos con /bug-add o cierra con /release, y relanza.
    [orquestar] PARAR: Versi�n v1.1.2 terminada. Revisa docs/review/versions/v1.1.2-revision.md: registra defectos con /bug-add o cierra con /release, y relanza.
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (3 intentos en dificil).
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (3 intentos en dificil).
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en dificil).
    .
    [orquestar] 1. PASO: revisar-version v0.1 release/v0.1
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    
    [orquestar] 2. PASO: revisar-version v0.1 release/v0.1
    [orquestar] revisar-version v0.1: sin progreso (1/2)
    
    [orquestar] PARAR: detenido a petici�n (--parar). Relanza para seguir.
    .
    [orquestar] 1. PASO: calcular-dependencias
    
    [orquestar] 2. PASO: calcular-dependencias
    [orquestar] PARAR: Dependencias inv�lidas en el backlog tras 2 intentos de corregirlas: T1 depende de T9, que no existe
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en dificil).
    
    [orquestar] 1. PASO: revisar-version v0.1 release/v0.1
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (3 intentos en dificil).
    [orquestar] PARAR: Diagn�stico de la suite pendiente. revisor no disponible
    
    [orquestar] 1. PASO: diagnosticar-suite B-DEM-0001 release/v0.1
    [orquestar] sin progreso (1/2)
    [orquestar] PARAR: alcanzado --max-pasos=1.
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0002: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0003: suite roja registrada para v0.2 (0 intentos en media).
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en media).
    [orquestar] B-DEM-0001: subo dificultad de media a dificil (3 reca�das de la misma causa)
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en dificil).
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (3 intentos en dificil).
    ................[orquestar] hades sin cuota: termina el paso sin tocar estados; el bucle esperar� la cuota y reintentar�.
    F...........................................[gateway] error con el mensaje 1: RuntimeError('x')
    ...........................[master (root-commit) bc037f0] mismatch
     1 file changed, 3 insertions(+)
     create mode 100644 pyproject.toml
    .[master (root-commit) cb3ace5] v0.2.0
     3 files changed, 5 insertions(+)
     create mode 100644 adevv/__init__.py
     create mode 100644 pyproject.toml
     create mode 100644 skills/demo/SKILL.md
    .................
    ======================================================================
    FAIL: test_dependencia_pendiente_no_anuncia_elegibilidad (test_control_intervenciones.ControlIntervencionesTests.test_dependencia_pendiente_no_anuncia_elegibilidad)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\AppData\Local\Temp\adevv-hotfix-v1.1.3\tests\test_control_intervenciones.py", line 197, in test_dependencia_pendiente_no_anuncia_elegibilidad
        self.assertIn('dependencias', salida)
    AssertionError: 'dependencias' not found in 'Respuesta recibida para Q-ADV-0001; la tarea sigue bloqueada.\n'
    
    ======================================================================
    FAIL: test_incorporacion_cli_y_cerrada_no_relanzan_dos_veces (test_control_intervenciones.ControlIntervencionesTests.test_incorporacion_cli_y_cerrada_no_relanzan_dos_veces)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\AppData\Local\Temp\adevv-hotfix-v1.1.3\tests\test_control_intervenciones.py", line 136, in test_incorporacion_cli_y_cerrada_no_relanzan_dos_veces
        self.assertIn('reanudada', salida)
    AssertionError: 'reanudada' not found in 'Respuesta recibida para Q-ADV-0001; la tarea sigue bloqueada.\n'
    
    ======================================================================
    FAIL: test_insuficiente_conserva_bloqueo_y_motivo (test_control_intervenciones.ControlIntervencionesTests.test_insuficiente_conserva_bloqueo_y_motivo) (texto='PENDIENTE: falta URL')
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\AppData\Local\Temp\adevv-hotfix-v1.1.3\tests\test_control_intervenciones.py", line 175, in test_insuficiente_conserva_bloqueo_y_motivo
        self.assertIn(motivo, self.cli(texto=texto)[1])
    AssertionError: 'falta URL' not found in 'Respuesta recibida para Q-ADV-0001; la tarea sigue bloqueada.\n'
    
    ======================================================================
    FAIL: test_insuficiente_conserva_bloqueo_y_motivo (test_control_intervenciones.ControlIntervencionesTests.test_insuficiente_conserva_bloqueo_y_motivo) (texto='INSUFICIENTE: falta puerto')
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\AppData\Local\Temp\adevv-hotfix-v1.1.3\tests\test_control_intervenciones.py", line 175, in test_insuficiente_conserva_bloqueo_y_motivo
        self.assertIn(motivo, self.cli(texto=texto)[1])
    AssertionError: 'falta puerto' not found in 'Respuesta recibida para Q-ADV-0001; la tarea sigue bloqueada.\n'
    
    ======================================================================
    FAIL: test_otra_pregunta_conserva_bloqueo (test_control_intervenciones.ControlIntervencionesTests.test_otra_pregunta_conserva_bloqueo)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\AppData\Local\Temp\adevv-hotfix-v1.1.3\tests\test_control_intervenciones.py", line 183, in test_otra_pregunta_conserva_bloqueo
        self.assertIn('otra pregunta', self.cli()[1])
    AssertionError: 'otra pregunta' not found in 'Respuesta recibida para Q-ADV-0001; la tarea sigue bloqueada.\n'
    
    ======================================================================
    FAIL: test_parada_manual_impide_relanzar (test_control_intervenciones.ControlIntervencionesTests.test_parada_manual_impide_relanzar)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\AppData\Local\Temp\adevv-hotfix-v1.1.3\tests\test_control_intervenciones.py", line 167, in test_parada_manual_impide_relanzar
        self.assertTrue(any('incorporada' in str(c) for c in self.aviso.call_args_list))
    AssertionError: False is not true
    
    ======================================================================
    FAIL: test_reinicio_tras_recepcion_incorpora_una_vez (test_control_intervenciones.ControlIntervencionesTests.test_reinicio_tras_recepcion_incorpora_una_vez)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\AppData\Local\Temp\adevv-hotfix-v1.1.3\tests\test_control_intervenciones.py", line 148, in test_reinicio_tras_recepcion_incorpora_una_vez
        self.assertEqual(motor.frontmatter(self.tarea)['status'], 'blocked')
    AssertionError: 'planned' != 'blocked'
    - planned
    + blocked
    
    
    ======================================================================
    FAIL: test_reserva_pid_visible_antes_de_segunda_respuesta (test_control_intervenciones.ControlIntervencionesTests.test_reserva_pid_visible_antes_de_segunda_respuesta)
    El hijo simulado no publica su PID: debe reservarlo el lanzador.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\AppData\Local\Temp\adevv-hotfix-v1.1.3\tests\test_control_intervenciones.py", line 223, in test_reserva_pid_visible_antes_de_segunda_respuesta
        self.assertIn('reanudada', self.cli()[1])
    AssertionError: 'reanudada' not found in 'Respuesta recibida para Q-ADV-0001; la tarea sigue bloqueada.\n'
    
    ======================================================================
    FAIL: test_destination_add_failure_resumes_developer_strategy_once (test_orquestar.SuiteRecoveryTests.test_destination_add_failure_resumes_developer_strategy_once)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\AppData\Local\Temp\adevv-hotfix-v1.1.3\tests\test_orquestar.py", line 1679, in test_destination_add_failure_resumes_developer_strategy_once
        self.assertIn('aplicar diagn�stico de la suite', self.git('log', '-1', '--format=%s'))
    AssertionError: 'aplicar diagn�stico de la suite' not found in 'fix(B-DEM-0001): aplicar diagnóstico de la suite'
    
    ======================================================================
    FAIL: test_destination_commit_failure_resumes_with_original_verdict (test_orquestar.SuiteRecoveryTests.test_destination_commit_failure_resumes_with_original_verdict)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\AppData\Local\Temp\adevv-hotfix-v1.1.3\tests\test_orquestar.py", line 1654, in test_destination_commit_failure_resumes_with_original_verdict
        self.assertIn('aplicar diagn�stico de la suite', self.git('log', '-1', '--format=%s'))
    AssertionError: 'aplicar diagn�stico de la suite' not found in 'fix(B-DEM-0001): aplicar diagnóstico de la suite'
    
    ======================================================================
    FAIL: test_cuota_de_hades_estado_recuperacion_y_revalidacion (test_revision_release.RevisionesReleaseTests.test_cuota_de_hades_estado_recuperacion_y_revalidacion)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\AppData\Local\Temp\adevv-hotfix-v1.1.3\tests\test_revision_release.py", line 204, in test_cuota_de_hades_estado_recuperacion_y_revalidacion
        self.assertEqual(before, self.snapshot())
    AssertionError: Tuples differ: ('e74[1618 chars]n', 'docs/platform_plan.md': b'APROBADO\r\n', [403 chars]te'}) != ('e74[1618 chars]n', '.adevv-metricas/registro.lock': b'', 'doc[441 chars]te'})
    
    First differing element 4:
    {'.gi[373 chars]n', 'docs/platform_plan.md': b'APROBADO\r\n', [402 chars]nte'}
    {'.gi[373 chars]n', '.adevv-metricas/registro.lock': b'', 'doc[440 chars]nte'}
    
    Diff is 2500 characters long. Set self.maxDiff to None to see it.
    
    ----------------------------------------------------------------------
    Ran 263 tests in 348.121s
    
    FAILED (failures=11, skipped=2)
