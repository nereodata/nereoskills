# Política de desarrollo de Adevv

Adevv prioriza la agilidad con calidad suficiente y mantenible: **invariantes duros en los bordes y autonomía total en el centro**. El objetivo vigente está en `docs/plan/versions/v1.2.md`.

## 1. Autonomía y único flujo
- **El agente decide el camino:** Artemisa asume el objetivo completo en perfil `dificil` (salvo elección expresa del usuario). Decide libremente si implementa directo, divide trabajo o delega en perfiles `sencilla`/`media`/`dificil`, sin subfases obligatorias (A–F), Gherkin ni documentos intermedios ceremoniales.
- **Las fichas son objetivos, no fronteras de diseño:** Pueden agruparse o reorganizarse preservando requisitos y dejando nota breve de cambios materiales.
- **Un solo motor hacia delante:** Este flujo autónomo es el camino por defecto. Si un proyecto consumidor aún no tiene `PROJECT.md`, aplica una política mínima por defecto; se mantiene compatibilidad de lectura con artefactos anteriores sin sostener dos flujos de ejecución paralelos.

## 2. Guardarraíles deterministas (bordes duros)
- **Pruebas directas:** `unittest` ejecutable por entradas reales con proveedores simulados. Los tests de bugs deben discriminar el fallo original. Gherkin es opcional y solo cuenta si está enlazado al runner sin omisiones silenciosas.
- **Mantenibilidad automática:** Chequeos rápidos de formato, lint (`ruff`) y modularidad estructural pesan más que instrucciones largas en prosa. Evitar seguir engordando monolitos.
- **Cero efectos laterales en verificación:** Prohibido enviar mensajes reales a Telegram, publicar, instalar globalmente o tocar credenciales durante pruebas.

## 3. Revisión post-verde y gestión pragmática de la deuda
- **Nunca bloquear a mitad de tarea:** No existen revisiones previas de spec ni de tests en rojo. Hades solo entra con el cambio **ya en verde**, revisando conjuntamente código y pruebas.
- **Disparador proporcional:** Revisión independiente obligatoria solo al tocar superficies críticas (permisos, persistencia/recuperación, cuotas, publicación) o al cerrar un bloque/versión. Si los revisores están sin cuota, queda anotado como pendiente de cierre sin paralizar tareas independientes.
- **Agilidad hoy, poda al cierre:** Se acepta deuda táctica razonable para avanzar rápido; antes de cerrar bloque o versión, con la suite en verde como red de seguridad, se hace un pase corto de simplificación (eliminar código muerto, duplicados y exceso de tamaño).

## 4. Continuidad y cierre
- **Motor mínimo:** El motor solo gobierna presupuestos duros (separando cuota de fallo real), memoria de relevo en Git/disco entre sesiones o modelos, métricas reales y puertas objetivas de salida. Cambiar de modelo no reinicia presupuestos.
- **Cierre honesto:** Evidencia vigente vinculada al árbol actual y suite completa en verde. La publicación (`/release`) es siempre explícita y humana.
