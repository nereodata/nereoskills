# Diseño técnico: T-ADV-0022

Se conserva el motor y su invalidación de evidencia. Un módulo stdlib nuevo, `skills/orquestar/calidad.py`, concentra el cálculo de delta, resolución por etapa y ejecución. `orquestar.py` añade `--calidad --base <commit> [--aplicar]`, carga el módulo por ruta (como métricas) y le entrega `verificar` como callback. No arranca el bucle ni gateway.

## Contrato y datos

- `delta(root, base)` resuelve base a SHA y une `git diff base --name-only -z --no-renames` con los nuevos no ignorados. Filtra existentes, deduplica y ordena; errores Git son errores, no omisiones.
- `resolver(root, validation, ficheros)` valida las tres claves explícitas antes de deducir. Devuelve etapas independientes con comando, escritura opcional y motivo/aviso. Solo deduce los scripts exactos reconocidos por DEC-ESP-03; fallback ruff por etapa. Filtra extensiones solo en deducción.
- Marcador completo `{ficheros}`: parseo de argumentos y expansión en lista, sin shell. Los comandos explícitos sin marcador conservan su texto y alcance shell con aviso; nunca se interpolan nombres en ellos. Configuración inválida falla antes de ejecutar.
- `ejecutar(root, base, aplicar, verificar)` aplica escritura disponible, después verifica ambas etapas incluso si una falla. Cada comando verificable transporta JSON codificado en base64 con base SHA, objetivos y comando; un ejecutor del mismo módulo lanza argumentos sin shell. Así la clave de evidencia incorpora la identidad del delta sin alterar `verificar` ni su huella del árbol.
- Herramientas inferidas de npm usan los binarios JS locales con node cuando existen, sin npx ni instalación. Ausencia de ejecutable es rojo.

## Impacto

Solo cambia el parser `main()` del motor con una rama de consulta independiente. Sus consumidores existentes (CLI y pruebas de motor) conservan comportamiento; pruebas existentes no cambian. Los dos flujos y review-code llaman a una única regla central, documentada en orquestar. La base se registra en el triaje antes de tocar archivos y se conserva entre commits/reintentos; Hades la utiliza sin escritura.

No se contradice ninguna decisión del plan de plataforma: stdlib, motores en skills y tests junto al módulo (DEC-P09/P10). No hay unidad temporal ni conversión. El camino normal sin `--calidad` no añade trabajo; las regresiones existentes comprueban ese aislamiento. Cada invocación de calidad realiza consultas Git y lectura de manifiestos, nunca búsqueda recursiva del proyecto.

## Pruebas

Repositorios Git temporales para confirmados/preparados/pendientes/nuevos/eliminados, inyección de comandos para orden y fallos, proceso Python real para preservar nombres especiales, reutilización e invalidación con el verificador existente. Red contra funciones provisionales que lanzan NotImplementedError; implementación posterior mínima. Los escenarios de flujos/Hades combinan prueba de instrucciones obligatorias con ejecución centralizada, sin simular una IA ni atribuirles automatización completa.
