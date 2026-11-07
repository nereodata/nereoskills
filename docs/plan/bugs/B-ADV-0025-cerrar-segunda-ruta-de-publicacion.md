---
id: B-ADV-0025
title: "/cerrar publica la release por una segunda ruta con validaciones propias, al margen de release_tools"
type: bug
weight: 2000
dificultad: media
version: "v1.1.0"
status: completed
origen: "T-ADV-0023; revisar-version v1.0 (docs/review/versions/v1.0-arquitectura.md), H-08 🟡"
created_at: 2026-10-27
updated_at: 2026-11-07
---

# B-ADV-0025: /cerrar publica la release por una segunda ruta con validaciones propias

## 🎯 Descripción del Fallo

**Causa raíz:** `skills/telegram_gateway/cierre_version.py` (hacia las líneas 37–135) reimplementa la merge a `main`, la comprobación de etiquetas local y remota, el changelog y el push. Su push es atómico, mejor que `--follow-tags`. Solo reutiliza `check_manifests_versions.py`, no `adevv/release_tools.py` (`validar_publicacion`, `publicar_version`).

**Comportamiento observado:** hay dos rutas de publicación con validaciones distintas. Cualquier cambio futuro en la política de publicación (RF-F05-05/06) tendrá que hacerse dos veces, en contra de la regla 3 de capas (`NO-04`), que pide las validaciones de release en un único sitio.

**Comportamiento esperado:** una única implementación de las validaciones y de la publicación, que usen tanto `adevv release` como `/cerrar`, conservando el push atómico.

## 📋 Reproducir
1. Comparar `cierre_version.publicar` con `release_tools.publicar_version` y `validar_publicacion`.

## 📋 Evidencias
- `docs/review/versions/v1.0-arquitectura.md`, hallazgo H-08.

## Triaje
- base_calidad: e7dd0c6ee7f93d88abf6a6238b1e39ed7a5bce69
- A Definición [SKIP]: refactor del contrato existente RF-F05-05/06 y /cerrar; no cambia requisitos.
- B Diseño [EXEC]: centralizar validaciones y transacción de publicación en release_tools, adaptando Telegram.
- C1 Pruebas [EXEC]: regresiones con repositorios Git temporales para publicación atómica, rollback, validaciones comunes y delegación de Telegram.
- C2 Corrección [EXEC]: release_tools y adaptador cierre_version.
- D QA [EXEC]: Hades sobre todo el delta.
- E Documentación [EXEC]: receta de publicación de /release y changelog; diseño y revisión de versión recogen la consolidación.
- F Cierre [EXEC]: estado y commit.
- Verificación al cierre: `python -m unittest tests.test_publicacion_compartida skills.telegram_gateway.test_cierre_version tests.test_install_and_release.TestInstallAndRelease.test_ca_f05_03_version_mismatch_fails_with_exact_message tests.test_install_and_release.TestInstallAndRelease.test_ca_f05_04_already_published_tag_fails_with_exact_message tests.test_install_and_release.TestInstallAndRelease.test_ca_f05_05_publicacion_correcta_y_etiqueta_anotada` ejercita ambos consumidores y la transacción compartida; `git diff --check` comprueba el delta. Sin herramientas de lint/tipado configuradas ni dependencias modificadas.

## Evidencia y decisiones
- Red: verificador sobre los 6 tests nuevos, 5 fallos y 1 error por las rutas aún separadas; Hades confirma rojo correcto.
- Hades /review-test: APROBADO, media 9.5. Hallazgo amarillo resuelto añadiendo changelog solo en el test de publicación histórico, sin alterar setUp compartido. Hallazgo azul con destino descartar aplicado.
- Hades /review-code: APROBADO, media 9.8. Dos hallazgos azules con destino descartar aplicados.
- DEC: release no urgente en release/v1.1; no se añade suborden CLI nueva. La receta de /release usa la API común.
- Calidad: formato y lint omitidos por ausencia de herramientas configuradas; no se declaran verdes ficticios. Sin manifiestos ni dependencias modificados.
