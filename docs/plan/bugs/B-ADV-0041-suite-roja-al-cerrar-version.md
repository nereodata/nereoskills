---
id: B-ADV-0041
title: "La suite falla al cerrar la versión"
type: bug
weight: 10
dificultad: media
version: "v1.1.2"
status: planned
depende_de: []
created_at: 2026-11-11
suite_cierre: true
suite_clave: f992801fe955b479570e4395bb2ea2ac9a927ac38686d061b5dbcd534ed68680
updated_at: 2026-11-11
suite_dificultad: media
suite_intentos: 0
---

# B-ADV-0041: La suite falla al cerrar la versión

## Descripción del fallo
La suite completa de cierre devuelve un código distinto de cero. Debe pasar antes de revisar o cerrar la versión.

## Reproducir
Ejecutar el comando indicado en la evidencia desde la raíz del proyecto.

## Último fallo de suite
- Comando: "python -m unittest discover -s tests"
- Código: 1; árbol: 5fcc56a6d7e67f51410a18cda7408d048d745de7; fecha: 2026-11-11T14:50:20

    ........[master (root-commit) 3dbc952] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 04cbde9] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 83db8a1] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 83db8a1] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 2cb64eb] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) da747f8] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) f8e1825] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) ba62788] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) 4925acd] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) e8aac90] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    ..[master (root-commit) b2bc179] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    ................To C:\Users\IVNMOR~1\AppData\Local\Temp\tmpuyeh0q7v\origin.git
     * [new tag]         v0.1.0 -> v0.1.0
    [main 7909d09] feat: bump v0.1.1
     1 file changed, 1 insertion(+), 1 deletion(-)
    To C:\Users\IVNMOR~1\AppData\Local\Temp\tmpuyeh0q7v\origin.git
       b23223a..7909d09  main -> main
     * [new tag]         v0.1.1 -> v0.1.1
    ................
    [orquestar] 1. PARAR: Versión v0.1 terminada.
    [orquestar] PARAR: Versión v0.1 terminada.
    
    [orquestar] 1. PARAR: Versión v0.1 terminada.
    [orquestar] PARAR: Versión v0.1 terminada.
    
    [orquestar] 1. PARAR: Versión v0.1 terminada.
    [orquestar] PARAR: Versión v0.1 terminada.
    .
    [orquestar] 1. PARAR: Requisitos con preguntas sin valor por defecto seguro.
    [orquestar] PARAR: Requisitos con preguntas sin valor por defecto seguro.
    ..
    [orquestar] 1. PARAR: Versión v0.1 terminada.
    [orquestar] PARAR: Versión v0.1 terminada.
    .
    [orquestar] 1. PASO: task-dev T1
    
    [orquestar] 2. PASO: task-dev T1
    [orquestar] PARAR: el arnés terminó con código 1 (sin cuota tras esperar 1.0 h (--espera-max)). Relanza cuando se resuelva.
    .[orquestar] mensaje de Telegram no enviado (OSError)
    [orquestar] mensaje de Telegram no enviado (OSError)
    .
    [orquestar] 1. PARAR: Versión v0.1 terminada. Revisa
    [orquestar] PARAR: Versión v0.1 terminada. Revisa
    
    [orquestar] 1. FIN: Todas las tareas con versión están cerradas.
    .
    [orquestar] 1. PARAR: Versión v0.1 terminada. Revisa
    [orquestar] PARAR: Versión v0.1 terminada. Revisa
    
    [orquestar] 1. PARAR: Versión v1.1.2 terminada. Revisa
    [orquestar] PARAR: Versión v1.1.2 terminada. Revisa
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
    [orquestar] hades sin cuota: termina el paso sin tocar estados; el bucle esperará la cuota y reintentará.
    
    [orquestar] 2. FIN: Cerrado.
    .............................hecho
    hecho
    [orquestar] agy status: ERROR (returncode: 0)
    .......s........Exception in thread Thread-3668 (_readerthread):
    Traceback (most recent call last):
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\threading.py", line 1075, in _bootstrap_inner
        self.run()
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\threading.py", line 1012, in run
        self._target(*self._args, **self._kwargs)
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\subprocess.py", line 1599, in _readerthread
        buffer.append(fh.read())
                      ^^^^^^^^^
      File "<frozen codecs>", line 322, in decode
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe0 in position 9: invalid continuation byte
    EException in thread Thread-3672 (_readerthread):
    Traceback (most recent call last):
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\threading.py", line 1075, in _bootstrap_inner
        self.run()
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\threading.py", line 1012, in run
        self._target(*self._args, **self._kwargs)
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\subprocess.py", line 1599, in _readerthread
        buffer.append(fh.read())
                      ^^^^^^^^^
      File "<frozen codecs>", line 322, in decode
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe0 in position 9: invalid continuation byte
    EException in thread Thread-3676 (_readerthread):
    Traceback (most recent call last):
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\threading.py", line 1075, in _bootstrap_inner
        self.run()
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\threading.py", line 1012, in run
        self._target(*self._args, **self._kwargs)
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\subprocess.py", line 1599, in _readerthread
        buffer.append(fh.read())
                      ^^^^^^^^^
      File "<frozen codecs>", line 322, in decode
    UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe0 in position 9: invalid continuation byte
    E[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    .456
    
    123
    
    789
    
    ..[orquestar] verificación reutilizada: "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\python.exe" -c "print(789)" ya pasó sobre este mismo árbol (f56c00c966).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (3 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (4 intentos en dificil).
    .
    [orquestar] 1. PARAR: Versión v0.1 terminada. Revisa
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
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (3 intentos en dificil).
    .
    [orquestar] 1. PASO: revisar-version v0.1 release/v0.1
    [orquestar] cambios guardados en el stash «orquestar: another 2026-11-11 14:48:08»
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
    [orquestar] B-DEM-0001: subo dificultad de media a dificil (3 recaídas de la misma causa)
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en media).
    [orquestar] B-DEM-0001: subo dificultad de media a dificil (3 recaídas de la misma causa)
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en dificil).
    .
    [orquestar] 1. PARAR: Versión v1.1.2 terminada. Revisa docs/review/versions/v1.1.2-revision.md: registra defectos con /bug-add o cierra con /release, y relanza.
    [orquestar] PARAR: Versión v1.1.2 terminada. Revisa docs/review/versions/v1.1.2-revision.md: registra defectos con /bug-add o cierra con /release, y relanza.
    
    [orquestar] 1. PARAR: Versión v1.1.2 terminada. Revisa docs/review/versions/v1.1.2-revision.md: registra defectos con /bug-add o cierra con /release, y relanza.
    [orquestar] PARAR: Versión v1.1.2 terminada. Revisa docs/review/versions/v1.1.2-revision.md: registra defectos con /bug-add o cierra con /release, y relanza.
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
    
    [orquestar] PARAR: detenido a petición (--parar). Relanza para seguir.
    .
    [orquestar] 1. PASO: calcular-dependencias
    
    [orquestar] 2. PASO: calcular-dependencias
    [orquestar] PARAR: Dependencias inválidas en el backlog tras 2 intentos de corregirlas: T1 depende de T9, que no existe
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en dificil).
    
    [orquestar] 1. PASO: revisar-version v0.1 release/v0.1
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (3 intentos en dificil).
    [orquestar] PARAR: Diagnóstico de la suite pendiente. revisor no disponible
    
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
    [orquestar] B-DEM-0001: subo dificultad de media a dificil (3 recaídas de la misma causa)
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en dificil).
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en dificil).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (3 intentos en dificil).
    ...............[orquestar] hades sin cuota: termina el paso sin tocar estados; el bucle esperará la cuota y reintentará.
    ............................................[gateway] error con el mensaje 1: RuntimeError('x')
    ...........................[master (root-commit) 8d3c4e3] mismatch
     1 file changed, 3 insertions(+)
     create mode 100644 pyproject.toml
    .[master (root-commit) db23bce] v0.2.0
     3 files changed, 5 insertions(+)
     create mode 100644 adevv/__init__.py
     create mode 100644 pyproject.toml
     create mode 100644 skills/demo/SKILL.md
    .................
    ======================================================================
    ERROR: test_windows_descendiente_con_padre_salido_y_pipes_heredados (test_orquestar.SubprocesoColgadoTests.test_windows_descendiente_con_padre_salido_y_pipes_heredados) (modo='json_gracia')
    El cierre alcanza al hijo después de salir el padre, en ambos lectores.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iván Moreno\SW\Adevv\tests\test_orquestar.py", line 2384, in test_windows_descendiente_con_padre_salido_y_pipes_heredados
        self.assertNotIn(f'"{int(pid_file.read_text())}"', consulta.stdout,
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\unittest\case.py", line 1156, in assertNotIn
        if member in container:
           ^^^^^^^^^^^^^^^^^^^
    TypeError: argument of type 'NoneType' is not iterable
    
    ======================================================================
    ERROR: test_windows_descendiente_con_padre_salido_y_pipes_heredados (test_orquestar.SubprocesoColgadoTests.test_windows_descendiente_con_padre_salido_y_pipes_heredados) (modo='json_timeout')
    El cierre alcanza al hijo después de salir el padre, en ambos lectores.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iván Moreno\SW\Adevv\tests\test_orquestar.py", line 2384, in test_windows_descendiente_con_padre_salido_y_pipes_heredados
        self.assertNotIn(f'"{int(pid_file.read_text())}"', consulta.stdout,
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\unittest\case.py", line 1156, in assertNotIn
        if member in container:
           ^^^^^^^^^^^^^^^^^^^
    TypeError: argument of type 'NoneType' is not iterable
    
    ======================================================================
    ERROR: test_windows_descendiente_con_padre_salido_y_pipes_heredados (test_orquestar.SubprocesoColgadoTests.test_windows_descendiente_con_padre_salido_y_pipes_heredados) (modo='lineas_timeout')
    El cierre alcanza al hijo después de salir el padre, en ambos lectores.
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iván Moreno\SW\Adevv\tests\test_orquestar.py", line 2384, in test_windows_descendiente_con_padre_salido_y_pipes_heredados
        self.assertNotIn(f'"{int(pid_file.read_text())}"', consulta.stdout,
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\unittest\case.py", line 1156, in assertNotIn
        if member in container:
           ^^^^^^^^^^^^^^^^^^^
    TypeError: argument of type 'NoneType' is not iterable
    
    ----------------------------------------------------------------------
    Ran 261 tests in 395.828s
    
    FAILED (errors=3, skipped=1)
