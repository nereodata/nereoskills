# Revisión de Pruebas (`review-test`): T-ADV-0001 (Ronda 2)

- **Tarea**: T-ADV-0001 — Publicación de versiones sin contenido interno
- **Especificación BDD**: `tests/features/publicacion.feature`
- **Archivos auditados**:
  - `tests/test_package_and_instructions.py`
  - `tests/test_install_and_release.py`
- **Veredicto**: **APROBADO**

## Puntuaciones

| Criterio | Puntuación | Resumen |
| :--- | :---: | :--- |
| **Cobertura** | 9.5 / 10 | Los 5 escenarios (`@CA-F05-01` a `@CA-F05-05`) están completamente cubiertos, incluyendo la lista blanca del wheel, la exclusión de `.agents`, la inspección del árbol real y el flujo completo de publicación con etiqueta anotada en `origin/main`. |
| **Aserciones** | 9.5 / 10 | Aserciones específicas y discriminantes sobre el contenido obligatorio y prohibido del `.whl`, mensajes exactos de error, ausencia de etiquetas tras fallo, tipo de objeto Git (`tag`), alcanzabilidad en `main` y consulta de versiones publicadas. |
| **Rojo correcto** | 9.5 / 10 | Los 6 tests fallan limpiamente por ausencia de la implementación (`NotImplementedError` en funciones stub y fallo en `check_manifests_versions.py`), con `py_compile` limpio. |
| **Estabilidad** | 9.5 / 10 | Tests deterministas y aislados mediante `tempfile.TemporaryDirectory()` y repositorios Git locales (`--bare`), sin red ni dependencias temporales. |
| **Media** | **9.50 / 10** | **APROBADO** (media > 8, sin hallazgos 🔴 ni 🟠) |

---

## Estado de Hallazgos Anteriores (Ronda 1)

- **H-01 [CRÍTICO]** (`test_ca_f05_05_publicacion_correcta_y_etiqueta_anotada`): **`resuelto`**. Se cubre la rama `release/v0.1`, la validación de manifiestos (`check_manifests_versions.py`), la publicación con `publicar_version`, la verificación de etiqueta anotada (`cat-file -t v0.1.0 == "tag"`), su pertenencia al historial de `main` en `origin` y el reconocimiento de `0.1.0` mediante `obtener_versiones_publicadas`.
- **H-02 [ALTA]** (`test_ca_f05_01_package_contains_only_whitelisted_files`): **`resuelto`**. Se incluye `.agents` en el fixture `setUp`, se afirma la presencia explícita de archivos representativos de cada categoría de la lista blanca en el `.whl`, se verifica la exclusión de `.agents/` y demás rutas internas, y se invoca `inspect_distribution_cleanliness(self.root)`.
- **H-03 [ALTA]** (`test_ca_f05_03_version_mismatch_fails_with_exact_message`): **`resuelto`**. Tras capturar `ReleaseValidationError`, se comprueba mediante `git tag -l` que no existe ninguna etiqueta ni en `self.repo_dir` ni en `self.origin_dir`.
- **H-04 [MEDIA]** (`test_ca_f05_02_real_repo_distribution_is_clean`): **`resuelto`**. Se añadió la prueba que ejecuta `inspect_distribution_cleanliness` contra la raíz real del repositorio.

## Nuevos Hallazgos (Ronda 2)

Sin hallazgos nuevos.
