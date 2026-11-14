---
id: T-ADV-0043
title: "Aligerar las suites heredadas de integración Git y CLI para bajar la batería total a ~10-15s"
type: infra
weight: 90
dificultad: media
version: "v1.4.0"
status: planned
depende_de: []
created_at: 2026-11-14
updated_at: 2026-11-14
---

# T-ADV-0043: Aligerar las suites heredadas de integración Git y CLI para bajar la batería total a ~10-15s

## 🎯 Objetivo de Negocio
Tras reducir el motor en `T-ADV-0042` (`test_orquestar.py` en `1.0s`, batería total de `501s` a `~45s`), los `~39s` restantes provienen de 5 suites heredadas (`test_updater.py`, `test_revision_release.py`, `test_install_and_release.py`, `test_cli_commands.py` y `test_conversacion_telegram_lectura.py`) que crean ~200 subprocesos `git.exe`/`python.exe`/`.cmd` reales en Windows y copian repositorios completos para validar variantes de mensajes o ramas de lógica pura. Sustituir esa repetición pesada por pruebas unitarias en memoria dejando solo 1-2 pruebas de humo reales por subsistema reducirá la batería completa a `~10-15s` en Windows sin perder cobertura real.

## 📋 Criterios de Aceptación (Nivel Máster)
- [ ] **CA-M-1 (Integración acotada a humo real):** `test_updater.py`, `test_revision_release.py`, `test_install_and_release.py`, `test_cli_commands.py` y `test_conversacion_telegram_lectura.py` conservan 1-2 pruebas reales de integración (`git archive`/`push`/`--fondo`/wrapper CLI) por capacidad crítica y trasladan las permutaciones de mensajes, errores y tablas de decisión a pruebas unitarias sin subprocesos redundantes.
- [ ] **CA-M-2 (Cero llamadas accidentales a WMI/red en tests):** Ninguna prueba invoca `Get-CimInstance Win32_Process` ni `git ls-remote` remoto salvo las pruebas unitarias específicas de `test_processes.py` (simuladas).
- [ ] **CA-M-3 (Tiempo objetivo en Windows):** La ejecución completa `python -m unittest discover -s tests` pasa al 100% en verde en `<= 15s` en Windows manteniendo `ruff check` limpio.
