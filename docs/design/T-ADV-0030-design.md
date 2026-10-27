# Diseño Técnico: T-ADV-0030 - Respaldo ambiental de Telegram solo para avisos

## Arquitectura

La resolución de credenciales sigue centralizada en `skills/orquestar/orquestar.py::credenciales`. Los avisos y el proceso gateway leen de esa resolución compartida. El origen del token decide si la credencial autoriza escucha; los IDs conservan su resolución independiente.

## Cambios

- **[MODIFY]** `skills/orquestar/orquestar.py`: resolver token e IDs por separado con `.env` primero; adjuntar `origen` (`proyecto`, `entorno` o `ninguno`) a un objeto que conserva el desempaquetado existente `(token, usuarios)`; permitir avisos ambientales y omitir el autoarranque con un aviso deduplicado por ejecución.
- **[MODIFY]** `skills/telegram_gateway/gateway.py`: comprobar el origen del token después de las opciones de solo consulta/parada y antes de cualquier reserva de PID, escucha o proceso; rechazar el origen `entorno` con el motivo compartido.
- **[MODIFY]** `skills/telegram_gateway/test_gateway_fondo.py`: probar procedencia, avisos y fronteras de arranque sin red ni procesos reales.
- **[MODIFY]** `skills/orquestar/SKILL.md` y `skills/telegram_gateway/SKILL.md`: explicar precedencia y política de escucha.

## Mapa de impacto

- Llamantes: `telegram(root)` consume token e IDs para avisos y conserva ambos orígenes; `gateway.py::main` consume los mismos valores y rechaza escucha si el token efectivo viene del entorno. Los consumidores que desempaquetan dos valores mantienen el contrato anterior.
- Escenarios afectados: los ocho escenarios etiquetados `@T-ADV-0030` en `orquestacion.feature` y `telegram_gateway.feature`. Las regresiones de credenciales existentes conservan su desempaquetado; no se invalida ningún contrato de usuario anterior.
- Decisiones documentadas contradichas: ninguna. DEC-P09 autoriza implementar el delta en los motores de `skills/` y sus pruebas.
- Sistema de referencia: no aplica.
- Camino caliente: la consulta solo lee `.env` y el entorno, como antes; no añade operaciones de red ni persistencia.

## Patrones

La política vive en la procedencia devuelta por `credenciales()` y el motivo compartido del motor. La salida mantiene compatibilidad con el desempaquetado de dos valores. El bucle deduplica la nota en memoria por raíz y reinicia esa marca al comenzar cada bucle.

## Testeabilidad

Se aíslan `TELEGRAM_*` con valores ficticios y se restauran mediante `patch.dict`; `subprocess.run`, `subprocess.Popen`, escucha y envío se observan mediante mocks. No se requiere conexión de Telegram.
