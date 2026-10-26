# Diseño técnico: B-ADV-0006

## Cambios
- `verificar(root, cmd)` conserva su retorno entero y caché verde. Redirige stdout+stderr a un fichero temporal para acotar memoria; almacena y muestra una cola UTF-8 de 32 KiB en evidencia, junto a árbol/comando/código.
- `registrar_fallo_suite(root, version, cmd)` busca un bug por `suite_cierre`, versión normalizada y SHA-256 del comando UTF-8 (`suite_clave`). El hash hexadecimal evita escapes de comandos en el parser YAML ligero, sin modificar ese parser compartido. El comando completo queda en el cuerpo con la evidencia. Crea el ID mediante `siguiente_id`, en `backlog_dirs`, con dificultad media, planned y depende_de vacío. Guarda última evidencia en el cuerpo sin perder triaje ni contenido del desarrollador.
- Reabre solo completed: aumenta `suite_intentos` persistente, separado de ejecuciones del arnés para no contar dos veces el mismo intento. `suite_dificultad` detecta promociones del mecanismo ordinario y reinicia ese contador. Al tercer fallo invoca `promover_dificultad`; en dificil bloquea para humano y devuelve motivo con ID y última salida. Bloqueados/cancelados no se reabren. El helper commitea solo el bug con check=True antes de lanzar agentes.
- El bucle resuelve y cambia a la rama release seleccionada antes de verificar el cierre (también en estados PARAR), con guardia de árbol sucio. Tras registrar el fallo recalcula estado para ejecutar bug-fix en esa misma iteración. Nunca lanza revisar-version con la suite roja.

## Mapa de impacto
- Llamantes de verificar: main (--verificar), bucle (cierre), y tests: quieren retorno/caché anteriores más salida conservada; no cambia la firma.
- `parar` conserva avisos de consola/Telegram; se reutiliza al agotar intentos o encontrar bloqueo.
- `promover_dificultad` y `comprobar_promocion` conservan contratos y perfiles; el helper utiliza la promoción existente, sin duplicar selección de modelos.
- Se sustituye explícitamente `OrquestarRegressionTests.test_red_suite_at_version_close_stops_before_review`: fijaba la parada inmediata que este bug pide cambiar. Los escenarios Gherkin existentes se conservan.
- Contrato operativo sustituido: skills/orquestar/SKILL.md, parada con suite roja (§Estado) y paso 0 de Revisión de versión. Es el comportamiento anterior descrito expresamente como defecto por B-ADV-0006. Ninguna decisión de arquitectura se contradice: stdlib y archivos locales como en platform_plan.
- Camino caliente: solo el cierre; tests verifican que el fallo inicial registra una vez y el siguiente paso es bug-fix, y que un verde retoma revisar-version; la caché verde sigue evitando ejecuciones repetidas.
- Sin conversión de unidades; versiones se comparan con vkey, fechas locales como el backlog existente.
- Los motivos de parada contienen ID y los últimos 1200 caracteres de salida: caben con prefijo y firma en Telegram, también con caracteres suplementarios UTF-16. La cola completa capturada permanece en el bug y la evidencia. No se modifica el transporte compartido.

## Validación
Regresiones de captura real stdout/stderr y cola acotada, reutilización verde, configuración personalizada de backlog/prefijo, reapertura idempotente con contenido preservado, tres recaídas y promoción, tres fallos en dificil con parada/aviso, bloqueo humano y ruta integrada rojo/bug-fix/verde/revisión. También parser ligero sin PyYAML con comillas y barras invertidas; aviso final largo con transporte simulado y medida UTF-16; checkout previo al cierre PASO/PARAR y guardia de árbol sucio. Se ejecuta solo test_orquestar.py y controles estáticos del delta mediante --verificar.
