---
id: B-ADV-0035
title: "La limpieza del test de orquestador en fondo oculta fallos de taskkill"
type: bug
weight: 10
dificultad: media
version: "v1.1.1"
status: completed
created_at: 2026-11-10
updated_at: 2026-11-10
---

# B-ADV-0035: Limpieza del proceso temporal de orquestación

## Descripción y reproducción

En Windows, `test_ca_f02_02_adevv_orquestar_fondo` falla con `WinError 32` al borrar `orquestar.log` cuando el sandbox impide terminar el proceso temporal. `_kill_pid_tree` ignora el código de `taskkill` y espera un tiempo fijo de 0,5 s antes de limpiar. La prueba original pasa fuera del sandbox: no se ha demostrado un defecto de producción del orquestador.

Reproducir: `python -m unittest tests.test_cli_commands.TestCliCommands.test_ca_f02_02_adevv_orquestar_fondo` en un entorno que permita iniciar procesos pero restrinja `taskkill`.

## Criterios de aceptación

1. Una denegación al terminar un proceso vivo informa el motivo de `taskkill`.
2. La limpieza confirma la salida con una espera acotada, en vez de un retardo fijo.
3. El test de fondo pasa con permisos adecuados y no se omite.

## Triaje

- base_calidad: `314f3d8df8660f4057e2723a41f9c992e76c0c05`.
- A [SKIP]: se mantiene el contrato funcional existente de la CLI.
- B [SKIP]: corrección localizada del helper de pruebas, sin cambios de API de producción.
- C1 [EXEC]: regresiones deterministas de denegación y cierre diferido.
- C2 [EXEC]: comprobar resultado y esperar con plazo máximo de 5 s; taskkill tiene timeout de 10 s.
- D [EXEC]: revisión aislada del delta.
- E [EXEC]: ficha y changelog.
- F [EXEC]: calidad y commit.
- Verificación: `python -m unittest tests.test_cli_commands`, fuera del sandbox para permitir terminar el árbol temporal.

## Evidencia inicial

- Antes de corregir: test de fondo falla dos veces en sandbox al limpiar `orquestar.log` con WinError 32.
- Mismo test original fuera del sandbox: 1 prueba OK (8,278 s).
- Pruebas nuevas: validan la denegación y la espera de cierre real sin tiempos de reloj externos.

## Resolución

Comprobación explícita del resultado de taskkill, espera de salida con límite de cinco segundos y tres regresiones deterministas (permisos, salida diferida y timeout). Revisión aislada aprobada; módulo CLI: 12 pruebas OK en 47,338 s antes de añadir la regresión de timeout. El lanzamiento en sandbox restringido requiere elevar permisos para terminar los procesos de prueba.
