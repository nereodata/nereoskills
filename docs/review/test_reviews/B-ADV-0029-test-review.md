**Veredicto:** APROBADO

# B-ADV-0029 · Revisión de pruebas

Fecha: 2026-11-07. Alcance: `skills/orquestar/test_reservas_arnes.py`, el delta de `test_bucle_omite_cuota_y_respeta_harness_forzado_y_cmd` en `skills/orquestar/test_cuota_vigente.py`, los escenarios `@B-ADV-0029` y la evidencia roja `B-ADV-0029-red.md`. Revisión aislada sin inspeccionar producción ni diseño.

| Criterio | Nota |
|---|---:|
| Cobertura | 9 |
| Aserciones | 9 |
| Rojo correcto | 9 |
| Estabilidad | 9 |
| Media | 9 |

- **Cobertura:** el esquema se ejercita con `development` y `artemisa`, tanto con CLI explícita como sin ella. Se comprueban la cadena Codex → agy → Claude, modelos y esfuerzos, sesiones y métricas. Los otros dos escenarios cubren herencia y continuidad de sesión dentro de Codex, y el principal forzado distinto al configurado.
- **Selección por cuota:** se conservan los cuatro casos del método preexistente y se ajustan los dos que atribuían el modelo del principal Claude a un principal forzado Codex. El quinto caso prueba que una marca vigente `codex/predeterminado` omite ese principal efectivo y elige la reserva heredada `codex/intermedia`. Se observan tanto modelo como arnés del perfil seleccionado y ausencia de espera; la plantilla `--cmd` conserva su control anterior.
- **Aserciones:** observan argumentos reales preparados para lanzamiento, arnés usado, ausencia de sesiones ajenas y registros persistidos. La ejecución no simula `bucle`, `ejecutar` ni `comando`. El éxito final y la ausencia de espera son controles adicionales; la frontera simulada no construye el arnés ni el comando esperado.
- **Rojo correcto:** la evidencia anterior al cambio documenta tres fallos de aserción por lanzar Codex en lugar de las reservas. Los controles sin CLI y del mismo arnés pasan previamente; no se atribuye su verde a cobertura nueva discriminante.
- **Estabilidad:** configuración y métricas viven en directorios temporales; se limpia el entorno heredado y se aíslan gateway, avisos, recarga, Git y esperas. No se lanzan arneses ni solicitudes de red reales. El agotamiento simulado dura una hora y no depende de una frontera temporal inmediata.

Compilación verde aportada por quien invoca. Para la ampliación, se aportan ocho pruebas verdes de `test_cuota_vigente` y el fallo previo de los dos casos que aún esperaban el modelo incompatible: es adaptación explícita del contrato, no evidencia roja nueva del fallo de reservas. Formato y lint fueron omitidos por ausencia de herramientas en la comprobación de calidad del delta; no se consideran herramientas ejecutadas en verde. No hay configuración de tipado nueva en este alcance.

Sin hallazgos críticos o altos ni deuda nueva.
