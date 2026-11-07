# Diseño B-ADV-0025

La política y transacción viven en `adevv/release_tools.py`. `validar_publicacion` acepta configuración opcional y valida manifiestos declarados, changelog y etiquetas; conserva el diagnóstico de versión del paquete para Adevv y soporta proyectos sin pyproject mediante sus manifiestos. Errores de publicación heredan ValueError para conservar el manejo del gateway.

`publicar_version` recibe rama y configuración opcionales, prepara merge y preflight en worktree separado, publica main y etiqueta mediante push atómico y solo después actualiza main local. Antes del push conserva rama, HEAD, main y etiquetas ante error. Limpieza de rama es responsabilidad de Telegram; la API histórica conserva la rama release.

## Mapa de impacto
- Búsqueda de consumidores: `tests/test_install_and_release.py` es el único llamante existente de las API release_tools; conserva firmas posicionales y mensajes de versión. Su fixture de publicación incorpora changelog requerido por la política común.
- `skills/telegram_gateway/cierre_version.py`: validar delega política de release y publicar delega transacción; conserva guardas del bucle, revisión final y borrado de release tras éxito.
- No existe suborden CLI de publicación: `adevv release` despacha scripts de manifiestos, completitud y changelog; no se añade una nueva interfaz.
- No se contradice ninguna decisión de plataforma: se cumple regla de capas 3 / NO-04. No hay camino caliente ni conversión de unidades.

## Pruebas
Repositorios locales temporales con remoto bare, sin red. Éxito: tag anotado y main remoto en mismo commit; fallo de preflight o rechazo de push: referencias y árbol originales intactos y sin tag nuevo. Validación de manifiestos, changelog, etiquetas y errores remotos; adaptador Telegram invoca la misma API.

## Impacto documental y pruebas existentes
La skill `skills/release/SKILL.md` todavía prescribe merge/tag/push manuales. Se cambia esa receta para invocar `publicar_version` y eliminar la duplicación operativa. El CLI `adevv release` conserva sus tres subórdenes auxiliares.

Se incluyen las pruebas existentes `skills.telegram_gateway.test_cierre_version` en la verificación del triaje. El diagnóstico remoto pasa de «etiqueta remota ya existe» al mensaje canónico «ya está publicada» (se adapta únicamente ese fragmento esperado). La API conserva el mensaje exacto histórico de paquete y publicación duplicada. El adaptador añade contexto de validación de manifiestos para conservar el diagnóstico de ese caso.
