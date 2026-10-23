# Diseño técnico: T-ADV-0015 · Control remoto y métricas

- Modificar `skills/telegram_gateway/gateway.py`: después de autorizar y normalizar comando/alias/sufijo del bot, atender parada, lanzamiento y consulta sin pasar por el modelo. La parada usa PID/PARADA y excluir; no elimina PID. Lanzar consulta estado con docs/requirements, invoca en_fondo con argumentos vacíos y anuncia el paso previsto; si ya hay PID no arranca.
- Modificar `skills/orquestar/orquestar.py`: `en_fondo(root, argumentos=None)` conserva sys.argv para CLI (None); una lista explícita evita heredar los argumentos del gateway. Conserva cwd=root, logs y flags sin ventana.
- Modificar `skills/orquestar/metricas.py`: extraer la lectura y agregación actuales a `consultar(root, items, filtro)`, compartida por mostrar (CLI) y el gateway. No cambia esquema, cálculo, filtros, costes ni salida CLI. El gateway formatea una línea por tarea con versión, minutos reales, tokens de desarrollo/Hades separados en entrada/caché/salida y USD estimado; razonamiento no se suma otra vez. Filtro por defecto ultima; errores ValueError/OSError producen una explicación sin resultados parciales.
- Añadir `skills/telegram_gateway/test_gateway_control.py`: proyectos temporales y Popen simulado; comprobar efectos de parada, alias, autorización, lanzamiento real hasta la frontera Popen, argumentos CLI heredados, errores de arranque, resumen con cálculos reales y filtros, errores y ausencia de datos.
- Actualizar ayuda y skill del gateway. Escenarios añadidos al feature funcional existente; no se retiran escenarios.

## Mapa de impacto
- Búsqueda de `en_fondo(`: único llamante de producción actual main en orquestar.py; necesita los argumentos CLI originales. El nuevo llamante responder requiere lista vacía. Ningún test existente fija otra firma.
- Búsqueda de lectura/agregación: mostrar es el consumidor actual del bloque extraído; conserva su comportamiento y código de retorno. consultar es nueva API para el gateway.
- responder es consumido por escuchar y tests/test_telegram_gateway.py; conserva autorización, conversación, buzón y sesiones. Nuevos comandos se resuelven antes de conversación.
- Ningún escenario/test existente se invalida. Regresión acotada: gateway existente y test_metricas; las nuevas pruebas cubren ambos contratos de en_fondo. No se encontró prueba Fondo en test_orquestar; se sustituye ese selector vacío por las pruebas nuevas del arranque.
- Decisiones contradichas: ninguna; DEC-P09 permite motores y pruebas bajo skills/. Sin cambios de dependencias ni arquitectura.
- Referencias: minutos reales y USD ilustrativos se reciben del agregador existente; tokens conservan categorías de origen. Consulta local solo bajo petición, sin red ni procesos del modelo. Lectura/agregación conserva complejidad lineal en registros; las pruebas contrastan resultados reales y lectura sin modificar archivos.

## Decisiones sin preguntar
- PID existente es el criterio acordado de actividad; no se añade detección de procesos ni eliminación de PID obsoleto.
- La confirmación comunica lanzamiento solicitado y paso previsto, no garantiza que un hijo ya haya terminado su inicialización. Excepciones de lanzamiento no producen confirmación falsa; el bucle conserva su validación habitual al arrancar.
- Documentación de usuario en la skill enlazada desde README; changelog delegado a /release. HITL diferido al cierre de versión.
