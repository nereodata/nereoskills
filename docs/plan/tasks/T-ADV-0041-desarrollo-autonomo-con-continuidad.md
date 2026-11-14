---
id: T-ADV-0041
title: "Desarrollo autónomo guiado por política con continuidad verificable"
type: funcional
weight: 110
dificultad: dificil
version: "v1.2.0"
status: completed
depende_de: ["T-ADV-0039"]
created_at: 2026-11-14
updated_at: 2026-11-14
---

# T-ADV-0041 · Flujo autónomo ligero y continuidad de v1.2

Coordina la entrega integrada descrita en [v1.2.md](../versions/v1.2.md) bajo la política de [PROJECT.md](../../../PROJECT.md):
- Motor único ligero activo por defecto (política local o base embebida), presupuesto duro separado de cuota y relevo portable entre sesiones/modelos (`adevv/contexto_ejecucion.py` conectado al orquestador).
- Fin de las subfases obligatorias A–F y de las revisiones a mitad de tarea: verificación determinista rápida (`unittest` + lint/modularidad) y revisión independiente solo post-verde en superficies críticas o cierre.
- Reutilización del trabajo válido adelantado en `T-ADV-0033/34/35/37/40` y coordinación con `B-ADV-0031`, dejando `T-ADV-0038` y `B-ADV-0049` como entregas focalizadas.

## Ejecución y verificación

- `base_calidad`: `1205bf0`
- Entregables implementados:
  - `adevv/contexto_ejecucion.py`: política ligera activa por defecto (`PROJECT.md` o política base embebida), superficies críticas (`toca_superficie_critica`), memoria de relevo portable en `.git/adevv-contexto/` (`guardar_checkpoint`, `contexto`) y contadores duros de intentos reales separados de esperas de cuota (`registrar_intento`).
  - `adevv/decision_item.py` + `skills/orquestar/intervencion.py` + `skills/orquestar/orquestar.py`: soporte CLI/bucle de `--checkpoint`, `--decision` y `DECISION_ITEM {...}`, aislamiento/restauración de WIP por ítem, esperas técnicas no bloqueantes (`cuota`, `ejecutable`, `suscripcion`, `servicio`), deduplicación de preguntas humanas por `clave` estable y soporte de `superseded` en `CERRADO`.
  - `adevv/revisiones.py`: acreditación determinista de revisión `N/A` proporcional cuando el delta Git del ítem queda fuera de superficies críticas.
  - `pyproject.toml` + `agents/{artemisa,hades}.md` + `skills/{task-dev,bug-fix,review-code,orquestar}/SKILL.md`: configuración `ruff` para `--calidad` y simplificación de instrucciones hacia el flujo autónomo post-verde.
- Verificación ejecutada en verde (`--verificar` y `--calidad --base 1205bf0`): `tests/test_politica_y_continuidad.py`, `tests/test_decision_item.py`, `tests/test_instructions_cleanliness.py`, `tests/test_package_and_instructions.py`, `tests/test_revision_release.py`, `tests/test_llamadas.py`, `tests/test_control_intervenciones.py`, `skills/orquestar/test_calidad.py` y `skills/orquestar/test_intervencion_humana.py` (89 pruebas `OK`, `ruff` sin errores, `git diff --check` limpio).
