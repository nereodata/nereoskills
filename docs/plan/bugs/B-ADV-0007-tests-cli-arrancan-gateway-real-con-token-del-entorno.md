---
id: B-ADV-0007
title: "Las pruebas de test_cli_commands arrancan un gateway de Telegram real con el token del entorno"
type: bug
weight: 30
dificultad: media
version: "v1.0.0"
status: completed
depende_de: []
created_at: 2026-10-26
updated_at: 2026-10-26
---

# B-ADV-0007: Las pruebas de test_cli_commands arrancan un gateway de Telegram real con el token del entorno

## 🔓 Alcance (decisión humana, 2026-10-26)
HC-01 queda resuelto: `tests/test_cli_commands.py` está dentro del alcance. La nota del prompt sobre "skills/", "agents/" y "workflows/" solo distinguía el árbol de trabajo de la copia instalada; no restringe rutas (B-ADV-0008, corregido en v0.6.1). Se puede modificar cualquier ruta del repositorio, incluidas `tests/` y `adevv/`.

## 🎯 Descripción del Fallo

**Causa raíz**: `tests/test_cli_commands.py` lanza `adevv orquestar` (p. ej. `--fondo`) como subproceso real heredando el entorno. Si `TELEGRAM_BOT_TOKEN` y `TELEGRAM_ALLOWED_USER_IDS` están definidos, el autoarranque de T-ADV-0016 levanta `gateway.py --gestionado` en la carpeta temporal del test. B-ADV-0003 aisló `iniciar_gateway` en los tests del bucle (`tests/test_orquestar.py`, `skills/orquestar/test_estado_agentes.py`), pero no en estas pruebas de CLI.

**Comportamiento observado**:
- 3 errores en la suite completa (`test_ca_f02_02_adevv_orquestar_fondo`, `test_ca_f02_08_new_project_auto_initialization`, `test_ca_f02_09_folders_where_nothing_is_created`): `PermissionError [WinError 32]` en `tearDown` al borrar `telegram.log`, abierto por el gateway lanzado.
- El gateway queda vivo tras la suite, haciendo long polling con el **token real del bot**, en competencia (409) con el gateway legítimo del usuario.

**Comportamiento esperado**: las pruebas de CLI no arrancan nunca un gateway real. `setUp` elimina `TELEGRAM_BOT_TOKEN` / `TELEGRAM_ALLOWED_USER_IDS` del entorno heredado por los subprocesos (o fuerza `"telegram": false`), y la suite completa pasa igual con o sin esas variables definidas.

## 📋 Reproducir
1. Definir `TELEGRAM_BOT_TOKEN` y `TELEGRAM_ALLOWED_USER_IDS` en el entorno.
2. `python -m unittest discover -s tests`.
3. Observado: `FAILED (errors=3)` y un `gateway.py --root <Temp>\...\drive_root --gestionado` vivo tras la suite. Sin esas variables, 149 pruebas OK.

## 📋 Evidencias
- Detectado al preparar `/release` de v0.6.0 (2026-10-26). El gateway huérfano se paró con `telegram.parar` en su carpeta temporal.

## Triaje (Artemisa, modo orquestado)
- **A ? Definici?n [SKIP]**: contrato existente de aislamiento de las pruebas; no cambia requisito de producto.
- **B ? Dise?o [SKIP]**: aislamiento local de dos variables con restauraci?n mediante cleanup; sin decisi?n arquitect?nica.
- **C1 ? Pruebas [EXEC]**: regresi?n del fixture CLI y un hijo Python inocuo con ambas variables ausentes, presentes y cada una presente por separado; restauraci?n del entorno tras cleanup. Rojo sin ejecutar el motor ni acceder a Telegram.
- **C2 ? Correcci?n [EXEC]**: aislar las dos variables Telegram en setUp de TestCliCommands y restaurar el entorno con addCleanup.
- **D ? QA [EXEC]**: Hades /review-test del delta completo de pruebas y /review-code de cierre (producci?n N/A).
- **E ? Documentaci?n [SKIP]**: no cambia API ni comportamiento del producto; solo aislamiento de pruebas.
- **F ? Cierre [EXEC]**: revisi?n de versi?n, estado completed al final y commit sem?ntico.
- **Verificaci?n al cierre**: `python -m unittest discover -s tests -p test_cli_commands.py`: cubre todos los consumidores del fixture y la regresi?n con credenciales ficticias presentes/ausentes; sin suite completa. Est?tico: compilaci?n del archivo y `git diff --check`; lint/tipado no configurados, dependencias sin cambios.
- **DEC-01**: release/v1.0, sin hotfix ni HITL. Se aplica el desbloqueo humano HC-01 ya registrado; tests/ est? autorizado. Se conserva el cambio de dificultad a media realizado por el bucle.
