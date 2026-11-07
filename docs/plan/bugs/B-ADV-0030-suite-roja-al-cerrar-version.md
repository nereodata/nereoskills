---
id: B-ADV-0030
title: "La suite falla al cerrar la versión"
type: bug
weight: 10
dificultad: media
version: "v1.1"
status: completed
depende_de: []
created_at: 2026-11-07
suite_cierre: true
suite_clave: f992801fe955b479570e4395bb2ea2ac9a927ac38686d061b5dbcd534ed68680
updated_at: 2026-11-07
suite_dificultad: media
suite_intentos: 0
---

# B-ADV-0030: La suite falla al cerrar la versión

## Descripción del fallo
La suite completa de cierre devuelve un código distinto de cero. Debe pasar antes de revisar o cerrar la versión.

## Triaje
- base_calidad: 2cce40f3828c3d68622878f0c11c8253f294f65d
- Subfase A: Definición: [SKIP] Contrato existente de tests de regresión y política de cuotas/progreso; no altera requisitos de producto ni añade nuevos contratos funcionales.
- Subfase B: Diseño: [SKIP] Corrección puramente de tests en `tests/test_orquestar.py` para adaptar los mocks y aserciones a la firma de progreso de B-ADV-0027.
- Subfase C1: Pruebas: [SKIP] Los tests que capturan y reproducen exactamente el fallo ya existen en `tests/test_orquestar.py` (`test_loop_resumes_developer_session_after_quota_wait` y `test_loop_retries_immediately_with_reserva_on_quota_without_waiting`).
- Subfase C2: Corrección: [EXEC] Ajustar en `tests/test_orquestar.py` el `side_effect` de `firma` (4 elementos) en `test_loop_resumes_developer_session_after_quota_wait` y la aserción de `reintentos_acumulados` (`pasos == 0` tras progreso) en `test_loop_retries_immediately_with_reserva_on_quota_without_waiting`.
- Subfase D: QA: [EXEC] Revisión de Hades (`/review-code`) sobre el delta de B-ADV-0030.
- Subfase E: Documentación: [EXEC] Documentar resolución en este fichero de bug y en `docs/review/versions/v1.1-revision.md`.
- Subfase F: Cierre: [EXEC] Comprobaciones de calidad del delta, verificación al cierre en verde, marcar completed y commit semántico `fix(B-ADV-0030)`.
- Verificación al cierre: `python -m unittest tests.test_orquestar.EscaladaTests.test_loop_resumes_developer_session_after_quota_wait tests.test_orquestar.ReservaCuotaTests.test_loop_retries_immediately_with_reserva_on_quota_without_waiting` porque comprueba de manera directa e inmediata los dos tests unitarios afectados por la regresión de B-ADV-0027.

## Resolución
- En `tests/test_orquestar.py`:
  - `test_loop_resumes_developer_session_after_quota_wait`: ampliado el mock de `motor.firma` a `side_effect=['a', 'a', 'b', 'b']` para alimentar las dos llamadas por vuelta que realiza `bucle()` (al inicio y al cierre de cada turno con `despues = firma(root, a.docs)` introducido en B-ADV-0027), eliminando el fallo por `StopIteration`.
  - `test_loop_retries_immediately_with_reserva_on_quota_without_waiting`: actualizada la aserción de `motor.reintentos_acumulados(self.root, 'T-ADV-0001')` a `self.assertEqual(pasos, 0)` conforme al contrato de B-ADV-0027, dado que el paso ejecutado con reserva experimenta progreso (`'a'` -> `'b'`) y por tanto no acumula reintentos indebidos de atasco.
- Revisión de Hades:
  - Código (`/review-code`): APROBADO (media 9.7 / 10) en `docs/review/code_reviews/B-ADV-0030-code-review.md` sin hallazgos.
- Verificación del triaje: 2 pruebas en verde vía `adevv orquestar --verificar`, comprobación de calidad del delta y `git diff --check` limpios.

## Último fallo de suite
- Comando: "python -m unittest discover -s tests"
- Código: 1; árbol: 8dede6c83dc5b1ad74ed55e683d2bcff7524b3df; fecha: 2026-11-07T14:28:40

    .....[master (root-commit) 48a306e] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 0d415b2] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) afbe26b] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) e39d9e3] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 16f39c9] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 4957a51] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) 3e621b5] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) 030e1c2] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) 204e699] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) 128a179] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    ..[master (root-commit) 32f0053] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    ...To C:\Users\IVNMOR~1\AppData\Local\Temp\tmpzm2fkhvb\origin.git
     * [new tag]         v0.1.0 -> v0.1.0
    [main 2759f08] feat: bump v0.1.1
     1 file changed, 1 insertion(+), 1 deletion(-)
    To C:\Users\IVNMOR~1\AppData\Local\Temp\tmpzm2fkhvb\origin.git
       5342362..2759f08  main -> main
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
    E...
    [orquestar] 1. PASO: task-dev T-ADV-0001
    [orquestar] hades sin cuota: termina el paso ahora mismo sin tocar estados; el bucle esperar� la cuota y reintentar�.
    
    [orquestar] 2. FIN: Cerrado.
    ...................F....hecho
    hecho
    [orquestar] agy status: ERROR (returncode: 0)
    .....[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    .456
    
    123
    
    789
    
    ..[orquestar] verificaci�n reutilizada: "C:\Users\Iv�n Moreno\AppData\Local\Programs\Python\Python312\python.exe" -c "print(789)" ya pas� sobre este mismo �rbol (f56c00c966).
    
    [orquestar] 1. PARAR: Versi�n v0.1 terminada. Revisa
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] PARAR: alcanzado --max-pasos=1.
    .
    [orquestar] 1. PASO: revisar-version v0.1 release/v0.1
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] PARAR: alcanzado --max-pasos=1.
    .
    [orquestar] 1. PASO: revisar-version v0.1 release/v0.1
    [orquestar] cambios guardados en el stash �orquestar: another 2026-11-07 14:27:40�
    [orquestar] revisar-version v0.1: sin progreso (1/2)
    [orquestar] PARAR: alcanzado --max-pasos=1.
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en media).
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
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (3 intentos en dificil).
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0002: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0003: suite roja registrada para v0.2 (0 intentos en media).
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (1 intentos en media).
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (2 intentos en media).
    [orquestar] B-DEM-0001: subo dificultad de media a dificil (3 arreglos tras los que la suite sigue roja)
    [orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en dificil).
    .[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    .............................................[gateway] error con el mensaje 1: RuntimeError('x')
    ...........................[master (root-commit) fe41b1f] mismatch
     1 file changed, 3 insertions(+)
     create mode 100644 pyproject.toml
    .[master (root-commit) b5324da] v0.2.0
     3 files changed, 5 insertions(+)
     create mode 100644 adevv/__init__.py
     create mode 100644 pyproject.toml
     create mode 100644 skills/demo/SKILL.md
    .................
    ======================================================================
    ERROR: test_loop_resumes_developer_session_after_quota_wait (test_orquestar.EscaladaTests.test_loop_resumes_developer_session_after_quota_wait)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\SW\Adevv\tests\test_orquestar.py", line 693, in test_loop_resumes_developer_session_after_quota_wait
        self.assertEqual(motor.bucle(args, self.root), 0)
                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iv�n Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 3224, in bucle
        despues = firma(root, a.docs)
                  ^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iv�n Moreno\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1139, in __call__
        return self._mock_call(*args, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iv�n Moreno\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1143, in _mock_call
        return self._execute_mock_call(*args, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iv�n Moreno\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 1200, in _execute_mock_call
        result = next(effect)
                 ^^^^^^^^^^^^
    StopIteration
    
    ======================================================================
    FAIL: test_loop_retries_immediately_with_reserva_on_quota_without_waiting (test_orquestar.ReservaCuotaTests.test_loop_retries_immediately_with_reserva_on_quota_without_waiting)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iv�n Moreno\SW\Adevv\tests\test_orquestar.py", line 1209, in test_loop_retries_immediately_with_reserva_on_quota_without_waiting
        self.assertEqual(pasos, 1)
    AssertionError: 0 != 1
    
    ----------------------------------------------------------------------
    Ran 205 tests in 187.394s
    
    FAILED (failures=1, errors=1)
