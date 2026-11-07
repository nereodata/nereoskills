# B-ADV-0029 · Evidencia roja

Comando: `python -m unittest discover -s skills/orquestar -p test_reservas_arnes.py`.

2026-11-07, antes de modificar producción: 3 pruebas, 3 fallos de aserción.

- Alias `development`, CLI `codex`: lanzamientos observados `['codex', 'codex', 'codex']`; esperados `['codex', 'agy', 'claude']`.
- Rol `artemisa`, CLI `codex`: el mismo fallo.
- Principal agy forzado a Codex: observados `['codex', 'codex']`; esperados `['codex', 'claude']`.
- Controles sin CLI y reserva del mismo arnés pasan antes de corregir.

El bucle, `ejecutar`, `comando`, selección de sesión y registro de métricas son reales. Solo se simula la frontera `lanzar`, ejecutables disponibles y servicios/estado externos. Los fallos son por el arnés efectivo incorrecto, sin errores de importación ni fixture.
