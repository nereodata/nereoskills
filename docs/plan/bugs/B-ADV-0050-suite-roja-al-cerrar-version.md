---
id: B-ADV-0050
title: "La suite falla al cerrar la versión"
type: bug
weight: 10
dificultad: media
version: "v1.2"
status: planned
depende_de: []
created_at: 2026-11-14
suite_cierre: true
suite_clave: f992801fe955b479570e4395bb2ea2ac9a927ac38686d061b5dbcd534ed68680
updated_at: 2026-11-14
suite_dificultad: media
suite_intentos: 0
suite_accion: ninguna
---

# B-ADV-0050: La suite falla al cerrar la versión

## Descripción del fallo
La suite completa de cierre devuelve un código distinto de cero. Debe pasar antes de revisar o cerrar la versión.

## Reproducir
Ejecutar el comando indicado en la evidencia desde la raíz del proyecto.

## Último fallo de suite
- Comando: "python -m unittest discover -s tests"
- Código: 1; árbol: 51a24acbf196d906b27e66334f360dd0d6c084c4; fecha: 2026-11-14T20:38:44

    ........[master (root-commit) ff462f8] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) ed590ba] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 0380d0f] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 98c98f1] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 5eeaa65] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    .[master (root-commit) 4033a67] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) b1130aa] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) d373217] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) 0416768] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    [master (root-commit) 45d2f0e] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    ..[master (root-commit) 0a26cf8] init
     6 files changed, 22 insertions(+)
     create mode 100644 docs/requirements/platform_plan.md
     create mode 100644 docs/requirements/platform_review.md
     create mode 100644 docs/requirements/req_analysis.md
     create mode 100644 docs/requirements/requirements.md
     create mode 100644 docs/requirements/work_plan.md
     create mode 100644 task_config.yaml
    ................Fuentes consultadas: docs/plan/bugs/B-ADV-0010-filtro.md, docs/plan/tasks/T-ADV-0002-vista.md, docs/review/versions/v0.1-revision.md.
    id: B-ADV-0010
    title: "Filtro roto"
    status: blocked
    id: T-ADV-0002
    title: "Vista principal"
    status: in_progress
    Bloqueo: falta credencial de entorno de pruebas en B-ADV-0010.
    Acciones rechazadas por permisos de solo lectura (write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file, write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file, write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file); no puedo escribir, borrar, ejecutar comandos ni controlar procesos.
    Fuentes consultadas: docs/plan/bugs/B-ADV-0010-filtro.md, docs/plan/tasks/T-ADV-0002-vista.md, docs/plan/tasks/T-ADV-0003-cierre.md, docs/review/versions/v0.1-revision.md.
    id: B-ADV-0010
    title: "Filtro roto"
    status: blocked
    id: T-ADV-0002
    title: "Vista principal"
    status: completed
    id: T-ADV-0003
    title: "Cierre"
    status: in_progress
    Bloqueo: falta credencial de entorno de pruebas en B-ADV-0010.
    Acciones rechazadas por permisos de solo lectura (write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file, write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file, write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file, write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file); no puedo escribir, borrar, ejecutar comandos ni controlar procesos.
    Fuentes consultadas: docs/plan/bugs/B-ADV-0010-filtro.md, docs/plan/tasks/T-ADV-0002-vista.md, docs/review/versions/v0.1-revision.md.
    id: B-ADV-0010
    title: "Filtro roto"
    status: blocked
    id: T-ADV-0002
    title: "Vista principal"
    status: in_progress
    Bloqueo: falta credencial de entorno de pruebas en B-ADV-0010.
    Acciones rechazadas por permisos de solo lectura (escribir_fichero, borrar_fichero, ejecutar_comando, controlar_proceso, leer_fichero, escribir_fichero, borrar_fichero, ejecutar_comando, controlar_proceso, leer_fichero); no puedo escribir, borrar, ejecutar comandos ni controlar procesos.
    Fuentes consultadas: docs/plan/bugs/B-ADV-0010-filtro.md, docs/plan/tasks/T-ADV-0002-vista.md, docs/plan/tasks/T-ADV-0003-cierre.md, docs/review/versions/v0.1-revision.md.
    id: B-ADV-0010
    title: "Filtro roto"
    status: blocked
    id: T-ADV-0002
    title: "Vista principal"
    status: completed
    id: T-ADV-0003
    title: "Cierre"
    status: in_progress
    Bloqueo: falta credencial de entorno de pruebas en B-ADV-0010.
    Acciones rechazadas por permisos de solo lectura (escribir_fichero, borrar_fichero, ejecutar_comando, controlar_proceso, leer_fichero, escribir_fichero, borrar_fichero, ejecutar_comando, controlar_proceso, leer_fichero, escribir_fichero, borrar_fichero, ejecutar_comando, controlar_proceso, leer_fichero); no puedo escribir, borrar, ejecutar comandos ni controlar procesos.
    Fuentes consultadas: docs/plan/bugs/B-ADV-0010-filtro.md, docs/plan/tasks/T-ADV-0002-vista.md, docs/review/versions/v0.1-revision.md.
    id: B-ADV-0010
    title: "Filtro roto"
    status: blocked
    id: T-ADV-0002
    title: "Vista principal"
    status: in_progress
    Bloqueo: falta credencial de entorno de pruebas en B-ADV-0010.
    Acciones rechazadas por permisos de solo lectura (Write, Edit, Bash, WebFetch, Read, Read, Read, Write, Edit, Bash, WebFetch, Read, Read, Read, Write, Edit, Bash, WebFetch, Read, Read, Read); no puedo escribir, borrar, ejecutar comandos ni controlar procesos.
    Fuentes consultadas: docs/plan/bugs/B-ADV-0010-filtro.md, docs/plan/tasks/T-ADV-0002-vista.md, docs/plan/tasks/T-ADV-0003-cierre.md, docs/review/versions/v0.1-revision.md.
    id: B-ADV-0010
    title: "Filtro roto"
    status: blocked
    id: T-ADV-0002
    title: "Vista principal"
    status: completed
    id: T-ADV-0003
    title: "Cierre"
    status: in_progress
    Bloqueo: falta credencial de entorno de pruebas en B-ADV-0010.
    Acciones rechazadas por permisos de solo lectura (Write, Edit, Bash, WebFetch, Read, Read, Read, Write, Edit, Bash, WebFetch, Read, Read, Read, Write, Edit, Bash, WebFetch, Read, Read, Read, Write, Edit, Bash, WebFetch, Read, Read, Read); no puedo escribir, borrar, ejecutar comandos ni controlar procesos.
    .
    usage limit reached, resets in 1200s
    
    
    
    Your organization has disabled Claude subscription access for Claude Code.
    
    
    Fuentes consultadas: docs/plan/bugs/B-ADV-0010-filtro.md, docs/plan/tasks/T-ADV-0002-vista.md, docs/review/versions/v0.1-revision.md.
    id: B-ADV-0010
    title: "Filtro roto"
    status: blocked
    id: T-ADV-0002
    title: "Vista principal"
    status: in_progress
    Bloqueo: falta credencial de entorno de pruebas en B-ADV-0010.
    Acciones rechazadas por permisos de solo lectura (escribir_fichero, borrar_fichero, ejecutar_comando, controlar_proceso, leer_fichero, escribir_fichero, borrar_fichero, ejecutar_comando, controlar_proceso, leer_fichero); no puedo escribir, borrar, ejecutar comandos ni controlar procesos.
    
    Your organization has disabled Claude subscription access for Claude Code.
    
    
       
    .Fuentes consultadas: docs/plan/bugs/B-ADV-0010-filtro.md, docs/plan/tasks/T-ADV-0002-vista.md, docs/plan/tasks/T-ADV-0099-inyeccion.md, docs/review/versions/v0.1-revision.md.
    id: B-ADV-0010
    title: "Filtro roto"
    status: blocked
    id: T-ADV-0002
    title: "Vista principal"
    status: in_progress
    id: T-ADV-0099
    status: planned
    Bloqueo: falta credencial de entorno de pruebas en B-ADV-0010.
    Acciones rechazadas por permisos de solo lectura (escribir_fichero, borrar_fichero, ejecutar_comando, controlar_proceso, leer_fichero, escribir_fichero, borrar_fichero, ejecutar_comando, controlar_proceso, leer_fichero, escribir_fichero, borrar_fichero, ejecutar_comando, controlar_proceso, leer_fichero); no puedo escribir, borrar, ejecutar comandos ni controlar procesos.
    Fuentes consultadas: docs/plan/bugs/B-ADV-0010-filtro.md, docs/plan/tasks/T-ADV-0002-vista.md, docs/plan/tasks/T-ADV-0099-inyeccion.md, docs/review/versions/v0.1-revision.md.
    id: B-ADV-0010
    title: "Filtro roto"
    status: blocked
    id: T-ADV-0002
    title: "Vista principal"
    status: in_progress
    id: T-ADV-0099
    status: planned
    Bloqueo: falta credencial de entorno de pruebas en B-ADV-0010.
    Acciones rechazadas por permisos de solo lectura (Write, Edit, Bash, WebFetch, Read, Read, Read, Write, Edit, Bash, WebFetch, Read, Read, Read, Write, Edit, Bash, WebFetch, Read, Read, Read, Write, Edit, Bash, WebFetch, Read, Read, Read); no puedo escribir, borrar, ejecutar comandos ni controlar procesos.
    Fuentes consultadas: docs/plan/bugs/B-ADV-0010-filtro.md, docs/plan/tasks/T-ADV-0002-vista.md, docs/plan/tasks/T-ADV-0099-inyeccion.md, docs/review/versions/v0.1-revision.md.
    id: B-ADV-0010
    title: "Filtro roto"
    status: blocked
    id: T-ADV-0002
    title: "Vista principal"
    status: in_progress
    id: T-ADV-0099
    status: planned
    Bloqueo: falta credencial de entorno de pruebas en B-ADV-0010.
    Acciones rechazadas por permisos de solo lectura (write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file, write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file, write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file, write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file); no puedo escribir, borrar, ejecutar comandos ni controlar procesos.
    .Fuentes consultadas: docs/plan/bugs/B-ADV-0010-filtro.md, docs/plan/tasks/T-ADV-0002-vista.md, docs/review/versions/v0.1-revision.md.
    id: B-ADV-0010
    title: "Filtro roto"
    status: blocked
    id: T-ADV-0002
    title: "Vista principal"
    status: in_progress
    Bloqueo: falta credencial de entorno de pruebas en B-ADV-0010.
    Acciones rechazadas por permisos de solo lectura (write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file, write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file, write_file, command, unsandboxed, mcp, read_url, read_file, read_file, read_file); no puedo escribir, borrar, ejecutar comandos ni controlar procesos.
    ................[orquestar] ejecutando "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\python.exe" -c "from pathlib import Path; p = Path('src/precios.py'); p.write_text(p.read_text(encoding='utf-8') + '# mutado\n', encoding='utf-8')": ejecución previa invalidada por cambio en vuelo (entradas modificadas durante la ejecución)
    .ok-b-adv-0031
    
    ok-b-adv-0031
    
    .[preflight] verificación reutilizada: "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\python.exe" -c "print('ok-b-adv-0031')" (evidencia aprobada vigente para la misma identidad (845985c582): el último resultado real fue verde para el mismo comando, entradas y entorno).
    ..ok-b-adv-0031
    
    [preflight] ejecutando "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\python.exe" -c "print('ok-b-adv-0031')": cambio en contenido relevante: cambio de entradas (entradas modificadas)
    .ok-b-adv-0031
    
    ..To C:\Users\IVNMOR~1\AppData\Local\Temp\tmp9y6vrof2\origin.git
     * [new tag]         v0.1.0 -> v0.1.0
    [main dae2359] feat: bump v0.1.1
     1 file changed, 1 insertion(+), 1 deletion(-)
    To C:\Users\IVNMOR~1\AppData\Local\Temp\tmp9y6vrof2\origin.git
       78ccb5c..dae2359  main -> main
     * [new tag]         v0.1.1 -> v0.1.1
    .........[orquestar] revisión pendiente de Hades: falta el dictamen formal.
    [orquestar] hades sin cuota; se conserva la recuperación vigente.
    [orquestar] revisión pendiente de Hades: falta el dictamen formal.
    [orquestar] hades sin cuota; se conserva la recuperación vigente.
    [orquestar] revisión pendiente de Hades: falta el dictamen formal.
    [orquestar] hades sin cuota; se conserva la recuperación vigente.
    .
    [orquestar] 1. PASO: bug-fix B-AFN-0185 release/v0.7
    
    [orquestar] 2. PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    [orquestar] PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    
    [orquestar] 1. PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    [orquestar] PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    .
    [orquestar] 1. PASO: bug-fix B-AFN-0185 release/v0.7
    
    
    [orquestar] 2. PASO: bug-fix B-AFN-0185 release/v0.7
    
    [orquestar] 3. PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    [orquestar] PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    
    [orquestar] 1. PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    [orquestar] PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    .
    [orquestar] 1. PASO: bug-fix B-AFN-0185 release/v0.7
    
    
    [orquestar] 2. PASO: bug-fix B-AFN-0185 release/v0.7
    [orquestar] PARAR: el arnés terminó con código 1 (sin cuota tras esperar 0 h (--espera-max); intervención de artemisa pendiente para bug-fix B-AFN-0185 en codex/desarrollo). Relanza cuando se resuelva.
    
    [orquestar] 1. PASO: bug-fix B-AFN-0185 release/v0.7
    
    [orquestar] 2. PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    [orquestar] PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    
    [orquestar] 1. PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    [orquestar] PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    ..
    [orquestar] 1. PASO: bug-fix B-AFN-0185 release/v0.7
    [orquestar] PARAR: el arnés terminó con código 1 (sin cuota tras esperar 0 h (--espera-max); intervención de artemisa pendiente para bug-fix B-AFN-0185 en codex/desarrollo). Relanza cuando se resuelva.
    
    [orquestar] 1. PASO: bug-fix B-AFN-0185 release/v0.7
    
    [orquestar] 2. PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    [orquestar] PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    
    [orquestar] 1. PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    [orquestar] PARAR: B-AFN-0185: diagnóstico terminal de la suite. Artemisa ya atendió esta intervención. Consulta el resultado en el bug.
    ....................
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
    E[orquestar] mensaje de Telegram no enviado (OSError)
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
    F............................hecho
    hecho
    [orquestar] agy status: ERROR (returncode: 0)
    .......s.....s....[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
    .456
    
    123
    
    789
    
    [orquestar] verificación reutilizada: "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\python.exe" -c "print(789)" ya pasó sobre este mismo árbol (f56c00c966); el último resultado real fue verde para el mismo comando, entradas y entorno.
    ..[orquestar] B-DEM-0001: suite roja registrada para v0.1 (0 intentos en media).
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
    [orquestar] cambios guardados en el stash «orquestar: another 2026-11-14 20:36:45»
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
    [orquestar] PARAR: Diagnóstico de la suite pendiente. 
    revisor no disponible
    
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
    .........[orquestar] puerta determinista en rojo para T-DEMO-0001; reabriendo para corrección.
    .............[orquestar] hades sin cuota: termina el paso sin tocar estados; el bucle esperará la cuota y reintentará.
    ............................................[gateway] error con el mensaje 1: RuntimeError('x')
    ...........................[master (root-commit) 66c1a1b] mismatch
     1 file changed, 3 insertions(+)
     create mode 100644 pyproject.toml
    .[master (root-commit) cffc04b] v0.2.0
     3 files changed, 5 insertions(+)
     create mode 100644 adevv/__init__.py
     create mode 100644 pyproject.toml
     create mode 100644 skills/demo/SKILL.md
    .................
    ======================================================================
    ERROR: test_quota_wait_and_quota_stop_notify (test_orquestar.AvisosTelegramTests.test_quota_wait_and_quota_stop_notify)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iván Moreno\SW\Adevv\tests\test_orquestar.py", line 407, in test_quota_wait_and_quota_stop_notify
        _, enviados = self.avisos(('PASO', 'task-dev', 'T1', None), ejecucion=sin_cuota)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iván Moreno\SW\Adevv\tests\test_orquestar.py", line 374, in avisos
        codigo = motor.bucle(self.args, self.root)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iván Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 4674, in bucle
        prompt = construir_prompt_paso(root, paso, arg)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iván Moreno\SW\Adevv\skills\orquestar\orquestar.py", line 572, in construir_prompt_paso
        nota_dec, _ = decision_item.contexto_prompt(root, rama_actual, arg)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iván Moreno\SW\Adevv\adevv\decision_item.py", line 223, in contexto_prompt
        d = leer(root, rama, iid)
            ^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iván Moreno\SW\Adevv\adevv\decision_item.py", line 51, in leer
        ruta = _ruta(root, rama, iid)
               ^^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iván Moreno\SW\Adevv\adevv\decision_item.py", line 43, in _ruta
        carpeta = _carpeta(root)
                  ^^^^^^^^^^^^^^
      File "C:\Users\Iván Moreno\SW\Adevv\adevv\decision_item.py", line 33, in _carpeta
        res = _git(root, "rev-parse", "--absolute-git-dir", check=False)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iván Moreno\SW\Adevv\adevv\decision_item.py", line 24, in _git
        res = subprocess.run(["git", *args], cwd=root, env=env, input=datos, capture_output=True)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\subprocess.py", line 548, in run
        with Popen(*popenargs, **kwargs) as process:
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\subprocess.py", line 1026, in __init__
        self._execute_child(args, executable, preexec_fn, close_fds,
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\subprocess.py", line 1538, in _execute_child
        hp, ht, pid, tid = _winapi.CreateProcess(executable, args,
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    FileNotFoundError: [WinError 2] El sistema no puede encontrar el archivo especificado
    
    ======================================================================
    FAIL: test_subagent_out_of_credits_triggers_quota_wait_in_loop (test_orquestar.EscaladaTests.test_subagent_out_of_credits_triggers_quota_wait_in_loop)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "C:\Users\Iván Moreno\SW\Adevv\tests\test_orquestar.py", line 681, in test_subagent_out_of_credits_triggers_quota_wait_in_loop
        esperar.assert_called_once_with(self.root, 300, cuotas_esperadas=ANY)
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 961, in assert_called_once_with
        return self.assert_called_with(*args, **kwargs)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      File "C:\Users\Iván Moreno\AppData\Local\Programs\Python\Python312\Lib\unittest\mock.py", line 949, in assert_called_with
        raise AssertionError(_error_message()) from cause
    AssertionError: expected call not found.
    Expected: esperar(WindowsPath('C:/Users/IVNMOR~1/AppData/Local/Temp/tmp3kl4k124'), 300, cuotas_esperadas=<ANY>)
      Actual: esperar(WindowsPath('C:/Users/IVNMOR~1/AppData/Local/Temp/tmp3kl4k124'), 299.9902412, cuotas_esperadas={'desde': 0, 'pares': {('agy', 'gemini-3.8-flash-medium')}})
    
    ----------------------------------------------------------------------
    Ran 313 tests in 480.737s
    
    FAILED (failures=1, errors=1, skipped=2)
