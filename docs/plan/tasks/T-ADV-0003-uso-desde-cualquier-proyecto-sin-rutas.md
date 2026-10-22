---
id: T-ADV-0003
title: "Adevv desde cualquier proyecto sin rutas"
type: funcional
weight: 130
version: "v0.1.0"
status: planned
depende_de: [T-ADV-0002]
origen: "F-02 (docs/requirements/funcionalidades/F-02_uso_sin_rutas.md)"
created_at: 2026-10-22
updated_at: 2026-10-22
---

# T-ADV-0003: Adevv desde cualquier proyecto sin rutas

## 🎯 Objetivo de Negocio
Hacer que el bucle de `/orquestar`, las revisiones de Hades, la verificación, el gateway de Telegram y los scripts de `/release` se invoquen desde cualquier proyecto mediante la orden global `adevv` sin depender de rutas al submódulo `.agents/`, incluyendo la inicialización automática de proyectos nuevos y la ejecución aislada del bucle sobre el propio repositorio fuente de Adevv.

### Hueco real (Delta sobre el código actual)
- **Ya existe:** `skills/orquestar/orquestar.py`, `skills/telegram_gateway/gateway.py`, `skills/release/scripts/*.py` y el conjunto de `skills/**`, `agents/**` y `workflows/**`.
- **Falta implementar:** El despacho en `adevv/cli.py` para `adevv orquestar`, `adevv telegram` y `adevv release manifiestos|completitud|changelog`; el uso de `adevv/yaml_lite.py` en el motor cuando no exista `PyYAML`; la construcción de prompts en `orquestar.py` con rutas absolutas entrecomilladas a la versión instalada activa, comandos `adevv ...` y la nota de aislamiento cuando se ejecuta sobre el repositorio fuente de Adevv (`RF-F02-09`); las validaciones previas al lanzar bucle (`RF-F02-06` para `instructions` inexistentes, `RF-F02-07` para elementos locales que ocultan o submódulo `.agents`, y `RF-F02-08` para creación automática de git + `task_config.yaml` mínimo con prefijo calculado); y la limpieza de referencias a `.agents/`, `python .../*.py`, `skills/<n>/scripts` y `../` en todas las instrucciones distribuibles.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (`@CA-F02-01`, `@CA-F02-02`, `@CA-F02-05`, `@RF-F02-01`):** `adevv orquestar <args>`, `adevv telegram <args>` y `adevv release manifiestos|completitud|changelog <args>` aceptan los mismos argumentos y producen la misma salida y códigos de retorno que los scripts originales; con `adevv orquestar --fondo` el proceso desacoplado recibe los argumentos originales, sigue vivo a los 5 segundos con `orquestar.pid` y no registra errores de argumentos en `orquestar.log`.
- [ ] **CA-M-2 (`@CA-F02-03`, `@CA-F02-10`, `@RF-F02-03`, `@RF-F02-09`):** Los prompts generados por el bucle y por `--agente` citan siempre las skills y los agentes por su ruta absoluta entrecomillada en la versión activa instalada (funcionando incluso cuando la instalación está en `C:` y el proyecto en `D:`) y las invocaciones de verificación y Hades como `adevv orquestar --verificar` y `adevv orquestar --agente hades` sin aparecer `orquestar.py`; cuando el bucle corre sobre el repositorio fuente de Adevv, el prompt sigue apuntando a la versión instalada e indica explícitamente que los cambios se hacen en `skills/`, `agents/` y `workflows/` del árbol de trabajo.
- [ ] **CA-M-3 (`@CA-F02-04`, `@CA-F02-05`, `@RF-F02-05`):** Ningún archivo de instrucciones del contenido distribuible (`skills/**` salvo `.py`, `agents/**`, `workflows/**`, `skills/release/templates/RELEASING.md`) contiene rutas relativas que empiecen por `.agents/`, invocaciones `python .../*.py`, referencias a `skills/<nombre>/scripts` ni rutas relativas `../`.
- [ ] **CA-M-4 (`@CA-F02-06`, `@CA-F02-07`, `@RF-F02-06`, `@RF-F02-07`):** Al lanzar un bucle, el sistema para antes de ejecutar ningún arnés si `orchestration.json` define un `<rol>.instructions` que no existe (`orchestration.json: <rol>.instructions apunta a <ruta>, que no existe.`), si el proyecto aún tiene `.agents` o su entrada en `.gitmodules` (`Este proyecto aún usa el submódulo .agents: sigue los pasos de migración del README.`), o si existen elementos locales en `.claude/`, `.codex/`, `.agents/` o `.agent/` que ocultan los de Adevv por carpeta o `name` (`Este proyecto tiene skills, agentes o workflows propios que ocultan los de Adevv: <rutas>. Bórralos o renómbralos.`), mientras que `adevv orquestar --estado` sigue respondiendo con normalidad.
- [ ] **CA-M-5 (`@CA-F02-08`, `@CA-F02-09`, `@RF-F02-08`):** Al lanzar un bucle en una carpeta con `docs/requirements/requirements.md` fuera de cualquier repositorio Git (y que no sea la carpeta personal ni la raíz de una unidad), el sistema crea automáticamente el repositorio Git y un commit inicial con `.gitignore` y `task_config.yaml` mínimo con el prefijo de tres letras calculado (`Mi app` → `MIA`, `Q1` → `PRJ`, `Ñandú` → `NAN`) e informa en una línea; si se lanza desde una subcarpeta de otro repositorio para sin crear nada con `Estás en una subcarpeta de <raíz>: lanza /orquestar desde la raíz.`, y en la carpeta personal, raíz de unidad o sin `requirements.md` para por falta de configuración sin crear archivos.
