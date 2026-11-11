---
id: B-ADV-0042
title: "Un descendiente POSIX puede sobrevivir al EOF de la captura JSON"
type: bug
weight: 20
dificultad: dificil
version: "v1.1.2"
status: completed
depende_de: []
created_at: 2026-11-11
updated_at: 2026-11-11
origen: "B-ADV-0032 y B-ADV-0041, revisión transversal de v1.1.2, hallazgo 1"
---

# B-ADV-0042 · Descendiente POSIX vivo tras el cierre del arnés

Hades identificó por lectura del código de `1bab7c5` una salida de `_ejecutar_captura_json` que deja de supervisar el grupo. Cuando el padre termina y ambos lectores reciben EOF, la captura devuelve el resultado. En POSIX, `_proceso_agrupado` espera al padre y el hijo puede seguir ejecutándose.

## Reproducción y criterio de aceptación

1. En POSIX, lanzar mediante la captura JSON un arnés que cree un descendiente de larga duración en su mismo grupo, con stdout y stderr redirigidos.
2. Hacer que el padre emita un resultado JSON válido y termine. Recoger el PID del hijo para comprobar su estado después de que la captura retorne.
3. Verificar que se conserva el resultado válido del padre y que el hijo ha terminado. El grupo debe quedar limpio también cuando ambos lectores reciben EOF antes de vencer el timeout o la gracia.

El dictamen se basa en inspección estática. La evidencia dirigida de Windows incluye una omisión POSIX. [Dictamen transversal](../../review/versions/v1.1.2-arquitectura.md).

## Hallazgo de Hades enrutado
- Destino: `artemisa`
- Decisión: reanudar desarrollo
- Evidencia: Hades H1, alta, resolver en v1.1.2. Terminar el grupo POSIX cuando la captura recibe EOF tras salir el padre, conservando el resultado JSON válido. Acreditar el caso de un descendiente con salidas redirigidas.

## Triaje

- `base_calidad`: `1e1426865200c9abdd3666eb8c45a35387df9f9a`, rama activa `hotfix/v1.1.2`.
- A [SKIP] El criterio de reproducción ya fija el contrato de la captura.
- B [SKIP] B-ADV-0032 ya define la sesión POSIX propia y la terminación del grupo por el PID del líder.
- C1 [EXEC] Cubrir el retorno normal con EOF en ambos lectores, JSON válido y un hijo real de larga duración con sus dos salidas redirigidas.
- C2 [EXEC] Limpiar el grupo en la salida normal de la captura POSIX preservando el código, el JSON y los indicadores del padre.
- D [EXEC] Hades revisa las pruebas y el delta de producción.
- E [SKIP] El arreglo cumple el contrato existente sin cambios de uso ni configuración.
- F [EXEC] Registrar evidencia y dictámenes en la revisión de versión y cerrar mediante commit.
- Verificación dirigida con `adevv orquestar --verificar`: `python -m unittest tests.test_orquestar.SubprocesoColgadoTests` en el anfitrión, y `tests.test_orquestar.SubprocesoColgadoTests.test_posix_eof_con_hijo_redirigido` en Linux para acreditar el caso real. Compilación de los dos Python modificados, `git diff --check` y calidad del delta.

## Resultado

La regresión reprodujo el hijo vivo en Linux y pasó tras limpiar el grupo en la rama de EOF. Hades dio por resuelto el hallazgo. Los comandos, resultados y dictámenes están en la [revisión de versión](../../review/versions/v1.1.2-revision.md#resolución-y-validación-de-b-adv-0042).
