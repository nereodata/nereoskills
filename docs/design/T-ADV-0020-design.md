# T-ADV-0020 · Informe independiente de agentes

Se conservan las capas DEC-P09/P10 y la biblioteca estándar. `informe_agentes(root, docs)` devuelve texto compartido por CLI y Telegram. Enumera roles declarados, base, dificultades, pasos, escalada y reservas heredadas, incluso en FIN/PARAR. Los perfiles efectivos siguen resolviéndose con ajustes/rol_de/escalada. Los modelos se deduplican por harness/model.

La cuota prioriza agotamiento vigente, después primary nativo de Codex y finalmente referencia de tokens de 5 h. Las fechas se comparan con zona y se muestran en hora local; resets_at es epoch UTC. Codex primary es cuota compartida de la cuenta: se aplica a todos los perfiles codex, sin atribuir tokens de una sesión a un modelo distinto. Solo eventos token_count recientes (5 h, no futuros) y reset vigente; se elige el más reciente entre sesiones de CODEX_HOME o ~/.codex. JSON incompleto o inaccesible se ignora. Se leen líneas secuencialmente sin cargar sesiones enteras en memoria y no se consultan sesiones si no hay modelos Codex.

`consumo_cuotas` centraliza lectura de métricas para el informe y el helper histórico `detalle_estado`, preservando la compatibilidad de este último. `perfiles_agentes`, `limite_cuota` y `cuota_codex` mantienen la enumeración, referencias y lectura nativa en el motor, sin duplicarlas en Telegram.

Límite opcional positivo y finito cuota_tokens_5h en perfil o reserva (heredado). Ante varios límites de un modelo se usa el menor, de forma conservadora. Referencias: Flash 20M; Argon/Pro, Opus/Sonnet 5M; GPT y desconocidos 10M. No son límites oficiales del proveedor. Se suman entrada, cache_leida, cache_escrita y salida sin duplicar razonamiento. El agotamiento no está limitado a eventos de las últimas 5 h si su plazo sigue vigente; una espera global sin modelo se presenta aparte.

## Mapa de impacto
- `parte` → gateway /estado, CLI telegram --estado y avisos: quieren estado conciso.
- `resumen` → CLI --estado y bucle: conserva resumen general, pierde detalle de agentes.
- `detalle_estado` → gateway /agentes y test_estado_agentes: se mantiene como compatibilidad para detalle previo; gateway migra a informe_agentes. Las pruebas históricas de detalle pasan a consultar directamente ese helper; nuevas pruebas comprueban limpieza en ambas superficies reales.
- `test_firma_gateway` cambia su mock al informe compartido; conserva todas las aserciones de firma.
- `main` añade salida temprana para --agentes/--agents antes de validaciones o recarga. No arranca bucle, gateway ni señales.
- SKILL.md de ambos motores: sustituir descripción anterior de /estado por consulta dedicada.
- Ninguna DEC de plataforma contradicha. CA-M-1 sustituye expresamente el contrato anterior de presentación de estado (T-ADV-0014); el detalle permanece disponible.

## Verificación
Fixtures temporales con reloj fijo, métricas y sesiones locales; ninguna prueba lee sesiones reales ni usa red. Prueba de CLI en subproceso con proyecto vacío y sin configuración garantiza salida de consulta sin lanzar procesos de trabajo. La ruta frecuente /estado deja de consultar cuotas/sesiones; /agentes escanea sesiones una sola vez por consulta.
