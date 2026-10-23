# Diseño técnico: T-ADV-0016 · Gateway en segundo plano

- [MODIFY] `skills/telegram_gateway/gateway.py`: constantes PID/LOG/PARADA; detección de PID vivo con API Windows (sin señales destructivas) o kill(pid, 0) POSIX. La CLI admite --fondo/--parar mutuamente excluyentes con --estado. --parar funciona sin credenciales, señala parada cooperativa y no toca orquestar.pid.
- El lanzador reserva telegram.pid con creación exclusiva y su PID antes de Popen; rechaza reservas vivas y recupera marcas inválidas/muertas. Lanza explícitamente gateway.py --root <root> --gestionado, sin credenciales en argumentos, con stdin cerrado, log y flags sin ventana/sesión nueva. Publica el PID hijo antes de devolver; si falla elimina su reserva. El hijo gestionado espera brevemente a que se publique su PID antes de escuchar. La escucha en primer plano también reserva PID y evita duplicados. Solo el dueño limpia PID y parada en finally.
- Escuchar comprueba telegram.parar antes del polling y entre mensajes; no interrumpe una conversación en curso. La parada puede tardar el timeout del polling (35 segundos) o la operación actual. El gateway sigue vivo al parar el bucle.
- [MODIFY] `skills/orquestar/orquestar.py`: PROPIOS incluye las tres marcas de Telegram. Nueva función iniciar_gateway(root) consulta telegram(root), lanza gateway.py --fondo con subprocess.run y timeout acotado; el gateway centraliza la detección de duplicados. Fallos se registran por tipo sin exponer token ni abortar. Se llama desde en_fondo y al entrar en bucle solo si no a.estado. No cambia telegram ni credenciales.
- [NEW] `skills/telegram_gateway/test_gateway_fondo.py`: fronteras SO/proceso/red simuladas y proyectos temporales; incluye ambos puntos de autoarranque y consultas sin efectos.
- [MODIFY] Skills de gateway y orquestar: comandos, logs, parada, autoarranque opcional y telegram:false.

## Mapa de impacto

- Búsqueda de en_fondo: main del motor y responder del gateway; ambos reciben autoarranque, el segundo encuentra su propio PID y no duplica. Se mantienen argumentos opcionales y retorno. Los tests de control anteriores no tienen credenciales en su proyecto temporal.
- Búsqueda de bucle: main y tests/test_orquestar.py. --estado no autoarranca. Los tests de avisos inyectan credenciales falsas: su fixture ahora simula iniciar_gateway para no lanzar procesos. Se conservan todas sus aserciones y se ejecuta solo esa clase de regresión. El delta cubre la integración con pruebas nuevas aisladas. No se modifica ni retira ningún escenario anterior.
- Búsqueda de escuchar: main del gateway y tests/test_telegram_gateway.py; mantiene firma y vueltas, añade condición cooperativa. main recibe opciones nuevas, la escucha normal conserva credenciales y respuestas.
- PROPIOS alimenta excluir y captura del árbol: añade solo los tres archivos de operación. Las pruebas verifican exclusión real en un repositorio temporal.
- Decisiones contradichas: ninguna; DEC-P09 permite código/pruebas en skills y gateway.py ya se clasifica correctamente. Sin cambio de arquitectura ni dependencias.
- Camino frecuente: una comprobación de archivo por polling/mensaje; no enumera procesos por mensaje. Autoarranque una vez por entrada; timeout de 10 segundos para el lanzador, escucha desacoplada. Pruebas con proceso simulado comprueban límite y argumentos.

## Decisiones sin preguntar

Parada cooperativa, sin matar procesos por PID. PID vivo tiene el significado solicitado de proceso vivo; la parada no envía señales destructivas a un PID reutilizado. HITL diferido a revisión de versión; changelog delegado a /release.
