# B-ADV-0009 · Evidencia roja

Árbol de desarrollo en release/v1.0, sin cambios de producción. Ejecuciones mediante `adevv orquestar --verificar`; detalles y huellas en `orquestar_evidencias.jsonl`.

- `python -m unittest discover -s tests -p test_updater.py`: 28 pruebas, 9 fallos. APLAZADA en vez de APLICADA, CLI devuelve 1 con bucle, instalación real no informa copias pendientes y `instalar` escribe el destino. Dos fallos corresponden a los subcasos de recuperación heredada con bucle. El caso de carpeta inválida se repitió tras corregir su aserción textual: falla por descargar cuando debe validar primero el destino existente (call_count 1, esperado 0).
- `python -m unittest discover -s tests -p test_sync.py`: 14 pruebas, 2 fallos en el nuevo caso (con/sin forzar): SINCRONIZADO en vez de DESFASADO mientras hay bucle.
- `python -m unittest tests.test_updater.TestUpdaterIntegrationAndCli.test_version_existente_invalida_no_se_borra_ni_activa`: 1 prueba, 1 fallo por call_count 1, esperado 0; sin fallo de sintaxis ni fixture.
- `python -m py_compile tests/test_updater.py tests/test_sync.py` y `git diff --check`: código 0. Sin linter ni tipado configurados.

La integración usa versiones compatibles 0.5.0 → 0.6.1, origen Git local y hogares temporales. Se conserva la cobertura de recarga cooperativa y gateway del triaje, sin reimplementar esos motores. No se ejecuta la suite completa. Esta evidencia es de este intento, no la del WIP.

## Correcciones tras review-test

H1: las aserciones de avisos nuevos se trasladan a stderr y se exige su ausencia en stdout. H2: nuevo caso CA-F03-13 con CLI real, destino 0.5.0 ya instalado, bucle 0.6.1 simulado, configuración automática desactivada, copias y registros intactos y transferencia al motor 0.5.0. H3: se observa también el archivo preparado para sobrescritura, antes y después de terminar el bucle.

Ampliación dentro de los mismos módulos del triaje: `ORQUESTAR_PASO` protege copias aunque el detector excluya al bucle ancestro; materialización local conserva carpetas existentes y `instalar --forzar` mantiene la versión activa. El diseño documenta ambas rutas de escritura.

Verificación focalizada de los tres casos nuevos: rollback falla por código CLI 1 en vez de 0; paso ancestro falla por bytes nuevos en vez de anteriores; materialización local, tras normalizar los alias de rutas cortas de Windows, falla porque desaparece el archivo en uso (`FileNotFoundError`). Son fallos de comportamiento, no de importación ni fixtures.

## Regresión H1 de review-code

Se añade `test_instalar_reutiliza_version_sin_puntero_y_no_la_limpia`: usa la orden CLI real con la versión local existente, actualización automática desactivada y `active.json` ausente. Exige puntero a la versión reutilizada y archivo marcador intacto después de la limpieza. Rojo mediante `adevv orquestar --verificar "python -m unittest tests.test_updater.TestUpdaterIntegrationAndCli.test_instalar_reutiliza_version_sin_puntero_y_no_la_limpia"`: 1 prueba, 1 fallo por puntero `None`, esperado no nulo. No se simula ni la activación ni la limpieza.
