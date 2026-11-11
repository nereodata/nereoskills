# Diseño técnico: B-ADV-0034

## Contrato y cambios

DEC-ESP-0034-01 fija CLI local sin servidor. Se añade `--responder REF TEXTO`
al parser de `skills/orquestar/orquestar.py`, con identidad `local:<usuario SO>`.
La autorización Telegram continúa en el adaptador existente, sin autorizar al
operador local como usuario Telegram. Ambos entran en una única operación
`intervencion.recibir`, que conserva validación, cola y reemplazo atómico.
CLI exige referencia explícita Q/T/B; Telegram conserva su texto sin referencia.

La recepción completa se serializa con un bloqueo SO separado del bloqueo del
registro, también liberado al morir el proceso. Esto incluye incorporación y
relanzamiento y evita que dos adaptadores lancen dos bucles. La incorporación
entre pasos sigue usando el bloqueo existente; nunca se escribe el árbol con
paso activo. Tras incorporar se consultan `backlog` y `pendientes_de`: no se
anuncia elegibilidad ni se relanza por una tarea con dependencias pendientes.
Una respuesta insuficiente informa el motivo persistido; no significa reanudación.
Solo el retorno satisfactorio de `en_fondo` permite anunciar bucle lanzado.

## Mapa de impacto

- `intervencion.responder`: único consumidor `orquestar.responder_pregunta`,
  usado por `skills/telegram_gateway/gateway.py`; conserva firma y autorización.
- Nuevo `orquestar.responder_pregunta_local`: consumidor único parser CLI.
- `intervencion.bloqueo`: listar/solicitar/incorporar/restaurar conservan el
  bloqueo por defecto; recibir usa otro nombre para serializar el ciclo completo
  sin bloquear recursivamente la incorporación.
- `incorporar`: conserva sus estados y avisos existentes (compatibilidad de
  escenarios B-ADV-0026); el nuevo resultado síncrono distingue arranque real.
- Nuevos escenarios @B-ADV-0034 y tests `test_control_intervenciones.py`;
  no se retira ni modifica ningún escenario o test existente.
- Ninguna decisión documentada contradicha; no cambia el plan de plataforma.
- Aislamiento por raíz resuelta, misma identidad Q en dos proyectos independientes.
- No hay referencia temporal nueva ni camino caliente: operación manual, coste
  lineal del backlog existente, comprobado con fixtures pequeñas y sin red.

## Verificación

Repositorios Git temporales reales para rama, commits, persistencia y reinicio;
CLI en subproceso durante paso activo y llamadas al parser aisladas para estados
detenidos. Red, lanzamiento y reloj se simulan; concurrencia de dos procesos
reales sobre el bloqueo SO, sin sleeps de sincronización. Se conserva regresión
Telegram, incluyendo rechazo de remitentes no autorizados. No se añaden paquetes.

## Corrección HC-01 / HC-02

`en_fondo` publica el PID del hijo antes de retornar, aún bajo serialización de
recepción. `main` acepta su propia titularidad reservada; conserva el rechazo
para otros procesos vivos. Si Popen falla no hay reserva nueva. Los PID obsoletos
siguen siendo recuperables mediante pid_vivo. Llamantes mecánicos: CLI --fondo,
intervencion.recibir, gateway /lanzar y cierre_version al continuar; todos quieren
reserva inmediata y conservan retorno 0. Tests de integración CLI de lanzamiento
en fondo se añaden al alcance de verificación.

La incorporación notifica incorporación, incluyendo espera por otra pregunta,
no lanzamiento. Se conserva el formato de confirmación de reanudación en el punto
posterior a en_fondo. HC-02 de Hades concreta CA-5/DEC y corrige la afirmación
prematura heredada de B-ADV-0026; no cambia sus estados, persistencia ni comandos.
Nuevas regresiones: dos preguntas de tareas distintas y spawn sin publicación
por el hijo, fallo spawn sin reserva, aceptación de PID propio y avisos con
parada/dependencias. No se cambian escenarios existentes.

La regresión existente de B-ADV-0026 exige aviso de reanudación al retomar en
un bucle ya activo. Para conservarlo sin emitirlo durante incorporación,
`notificar_reanudacion` se invoca tras la ejecución real del paso retomado,
no si el arnés está ausente. La marca durable `reanudacion_avisada` evita
repetir el aviso en reintentos; se persiste antes del envío, siguiendo la política
existente de no reenviar avisos interrumpidos. El nuevo llamante es bucle tras
recibir resultado de ejecutar; los estados de preguntas no cambian.
Si publicar PID falla tras Popen, el padre termina y espera al hijo antes de
propagar el error, evitando un proceso lanzado sin reserva observable.

El hijo con PID propio vivo toma una rama específica que conserva la reserva
sin unlink ni republicación. Solo la adquisición inicial (sin PID vivo) limpia
marca obsoleta, excluye ficheros y publica titularidad. Espías de operaciones
reales sobre PID fijan la continuidad hasta entrar al bucle; cleanup final sigue
siendo del propietario. HC-01 persiste en revisión anterior únicamente por esta
transición, corregida sin cambiar contratos adicionales.

La publicación usa temporal sincronizado y os.replace (`publicar_pid`), tanto
padre como adquisición inicial del hijo. Esta última tampoco elimina la marca:
si el hijo leyó ausencia antes de que el padre publicara, su publicación posterior
sustituye atómicamente el mismo titular sin abrir otra ventana. Los temporales
usan el prefijo runtime existente adevv-intervencion- y se limpian en finally.
Llamantes de publicar_pid: en_fondo e inicialización main, ambos internos.
