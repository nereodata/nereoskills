# Diseño técnico: T-ADV-0019

La resolución de la versión de Adevv y las utilidades comunes de formateo e idempotencia viven en `skills/orquestar/orquestar.py`; el módulo `gateway.py` las reutiliza a través de su referencia `motor`. Conforme a `DEC-P09` y `DEC-P10`, todos los cambios residen dentro de las rutas autorizadas en `skills/`.

## 1. Detección de versión del proceso
La función `version_adevv(script=None)` deduce la versión de Adevv correspondiente al proceso en ejecución mediante tres niveles jerárquicos:
1. Inspección de la ruta del script (`script` o `__file__`): si reside en `$ADEVV_HOME/versions/<ver>/` (o `~/.adevv/versions/<ver>/`), extrae el segmento de directorio de versión (`<ver>`).
2. Metadatos del paquete importable: consulta `adevv.__version__` si el paquete está en el entorno de ejecución.
3. Manifiesto del repositorio o paquete: busca `pyproject.toml` en los ancestros del script y extrae el campo `version`.
Si ninguno está disponible, aplica el valor de versión por defecto (`0.5.0`). El resultado se normaliza sin prefijos redundantes (p. ej. `0.5.0`).

## 2. Idempotencia y formato de firma
La firma de versión se añade al pie del mensaje separada por dos saltos de línea (`\n\n`):
- Comandos y avisos del bucle: `— Adevv v<ver>` (p. ej. `— Adevv v0.5.0`), utilizando guion largo (em-dash `—`, U+2014).
- Conversación libre del gateway: `— Adevv v<ver> · <harness>/<model>` (p. ej. `— Adevv v0.5.0 · agy/gemini-4-argon-medium`), separando arnés y modelo del emisor conversacional con punto medio (` · `, U+00B7).

La función `tiene_firma(texto)` comprueba mediante expresión regular `r'[—–-]\s*Adevv\s+v\S*'` si el mensaje ya contiene una firma final de versión. La función `firmar(texto, extra=None, script=None)` es idempotente: si `tiene_firma(texto)` es verdadero, devuelve el texto intacto sin duplicar la firma.

## 3. Puntos de integración
- `skills/orquestar/orquestar.py`:
  - `avisar(root, evento, texto)`: envuelve el mensaje con `firmar(f'[{root.name}] {texto}')`.
  - `enviar(token, chat, texto, markdown=False)`: aplica `texto = firmar(texto)` como salvaguarda idempotente para cualquier envío directo.
- `skills/telegram_gateway/gateway.py`:
  - `conversar(root, usuario, texto)`: extrae el arnés y el modelo efectivo configurados para el asistente (`orchestration.json` o ejecución) y devuelve la respuesta firmada con `extra=f'{harness}/{modelo}'`.
  - `responder(root, usuario, texto, autorizados)`: todas las respuestas a comandos (`/estado`, `/lanzar`, `/parar`, `/metricas`, `/tarea`, `/bug`, `/nuevo`, `/ayuda`, `/agentes`) devuelven el texto firmado con `firmar(resp)`.
  - `escuchar(...)`: en caso de excepción al procesar un mensaje, la respuesta de error enviada al chat también se firma.

## 4. Pruebas y verificación
Se crean dos suites de pruebas unitarias:
- `skills/orquestar/test_firma_telegram.py`: comprueba la resolución de versión en directorios de almacén y repositorios, el formateo básico y con parámetros extra, la idempotencia de `firmar`, y la inclusión de la firma en `avisar()` y `enviar()`.
- `skills/telegram_gateway/test_firma_gateway.py`: comprueba que todos los comandos del gateway devuelven respuestas firmadas con `— Adevv v0.5.0`, que la conversación libre incluye `— Adevv v0.5.0 · <harness>/<model>`, y que los mensajes que ya portan la firma no la duplican en `escuchar()` o `responder()`.
Verificación exclusiva mediante el comando del triaje: `python -m unittest skills/orquestar/test_firma_telegram.py skills/telegram_gateway/test_firma_gateway.py`.
