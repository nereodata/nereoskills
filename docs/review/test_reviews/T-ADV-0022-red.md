# Rojo de T-ADV-0022

Comando: `adevv orquestar --verificar "python -m unittest discover -s skills/orquestar -p test_calidad.py"`.

Rojo inicial: 17 pruebas; 3 fallos de contrato en instrucciones y 37 errores incluyendo subtests. Tras reforzar H-01/H-02 de review-test y actualizar instrucciones: 19 pruebas, 39 errores incluyendo subtests, sin fallos textuales. La lógica de delta/resolución/ejecución falla con NotImplementedError en funciones provisionales, no por imports, sintaxis ni fixtures. El parser rechaza las opciones aún no implementadas. La salida completa actual queda en `.git/T-ADV-0022-red.log` (captura directa de stdout/stderr del comando autorizado). El primer intento de extraerla del JSONL produjo un archivo vacío; se corrigió con esa captura, sin atribuir salida ausente al registro.

Extracto: `NotImplementedError: delta de calidad pendiente`; `NotImplementedError: resolución de calidad pendiente`; `NotImplementedError: ejecución de calidad pendiente`; `unrecognized arguments: --calidad --base ...`; falta `--calidad --base` en instrucciones de los dos flujos y Hades.

Compilación de las pruebas mediante `--verificar`; no hay linter ni tipador configurado en este proyecto. No suite completa ni herramientas externas instaladas.
