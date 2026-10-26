# Revisión de código — T-ADV-0023

**Veredicto: APROBADO**

Fecha: 2026-10-27. Revisor: Hades. Skill aplicada: `/review-code` de Adevv 0.6.0. Segunda revisión.

## Alcance

Reevaluación del delta que corrige H-01, H-02 y H-03 de la primera revisión, que aprobó con una media de 8,5/10 y sin hallazgos altos. El delta toca:

- `skills/telegram_gateway/cierre_version.py`: `ejecutar` con timeout propio, YAML a través de `motor.yaml` y entorno sin `GIT_ASKPASS`;
- `skills/orquestar/orquestar.py`: `cargar_cierre_version` y su uso en `avisar`;
- `skills/telegram_gateway/gateway.py`: `/cerrar` a través de ese mismo punto de carga;
- las guías de ambas skills y el diseño (`release.preflight_timeout`).

La corrección no toca otros módulos ni interfaces, así que no se ha ampliado la revisión. No se ha ejecutado ninguna release real ni se ha usado el transporte de Telegram.

## Análisis estático

Todo lo que sigue está en verde en `orquestar_evidencias.jsonl` sobre el árbol `065b3d69f3`, y no se ha relanzado:

- compilación de los cuatro módulos;
- `git diff --check`;
- `python -m unittest skills.telegram_gateway.test_cierre_version tests.test_telegram_gateway tests.test_orquestar` (código 0; 105 pruebas OK).

No hay linter, tipado ni detector de secretos configurados. No cambian dependencias ni manifiestos.

## Puntuaciones

| Criterio | Nota | Evaluación |
| --- | ---: | --- |
| Corrección | 9/10 | **Timeout:** el preflight tiene su propio límite, validado: se rechazan los booleanos, lo que no es numérico, los valores no positivos y los infinitos. Un valor no válido da un error controlado dentro del `try`, que limpia el worktree, y nunca llega a publicarse. **YAML:** si falta el parser, el cierre se rechaza de forma controlada en lugar de romper el bucle. La transacción y la recuperación no cambian respecto a la versión aprobada. |
| Seguridad | 9/10 | Ya no se usa `GIT_ASKPASS=echo`, así que no hay intentos de credenciales falsos. Se mantienen `GIT_TERMINAL_PROMPT=0` y `GCM_INTERACTIVE=never`. El resto no cambia. |
| Conformidad | 9/10 | El diseño documenta la carga bajo demanda, el parser del motor y el timeout configurable. Coincide con lo implementado y no añade dependencias al bucle. |
| Calidad | 9/10 | Un único punto de carga (`cargar_cierre_version`) que reutilizan el gateway y el aviso. Ya no hay acoplamiento con `adevv` al importar el motor. |
| Eficiencia | 9/10 | El módulo se carga solo al atender `/cerrar` o el aviso final de versión, sin coste para el resto del bucle. |
| Documentación | 9/10 | Ambas guías y el diseño citan los 600 s por defecto, la clave de configuración, su validación y el límite independiente de Git (120 s). |

**Media: 9/10.** Supera 8 y no hay hallazgos críticos ni altos.

## Reevaluación de hallazgos anteriores

### H-01 — 🟡 MEDIA — Resuelto

`ejecutar` acepta `timeout`. El preflight usa `release.preflight_timeout` (600 s por defecto, positivo y finito) y Git conserva los 120 s. Está documentado en `skills/telegram_gateway/SKILL.md`, `skills/orquestar/SKILL.md` y el diseño. Queda un límite que no se puede resolver sin complicar el código: en Windows, un timeout con `shell=True` no termina los procesos nietos. No se registra.

### H-02 — 🟡 MEDIA — Resuelto

`cierre_version.py` no importa `adevv`. Lee `task_config.yaml` con `motor.yaml` (PyYAML con `safe_load`, o `yaml_lite` con `load_yaml`) y rechaza el cierre si no hay parser. El motor carga el módulo bajo demanda con `cargar_cierre_version`, que reutilizan `avisar` y `/cerrar`.

### H-03 — 🔵 BAJA — Resuelto

El entorno que construye `ejecutar` ya no incluye `GIT_ASKPASS`.

### H-04 y H-05 — 🔵 BAJA — Descartados

Mantienen el destino de la primera revisión.

## Hallazgos nuevos

### H-06 — 🔵 BAJA — `task_config.yaml` vacío produce `AttributeError`

Con PyYAML, `safe_load` de un archivo vacío devuelve `None`, y `cfg.get` lanza `AttributeError`, que `cerrar` no captura: el error llegaría al gateway. El proyecto siempre tiene esa configuración, porque la exige el resto del flujo de release.

- **Destino:** descartar.

### H-07 — 🔵 BAJA — Validación tardía del timeout y espaciado

`release.preflight_timeout` se valida después de preparar el merge en el worktree. Es correcto, pero podría rechazarse antes, en `validar`. Además, entre los imports y `resumen` queda una sola línea en blanco.

- **Destino:** descartar. Es cosmético y no tiene efecto, porque el worktree se limpia igualmente.

## Destinatarios

- **Desarrollador / especificador / humano:** nada pendiente. Las comprobaciones de CI y smoke posteriores a la etiqueta siguen siendo humanas, como dice DEC-T23-04.
