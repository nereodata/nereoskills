# Política de desarrollo de Adevv

## Autonomía para ganar agilidad
Priorizamos la agilidad con calidad mantenible. Fuera de los mínimos de abajo, **el agente decide autónomamente cómo resolver cada objetivo**: cada cambio es distinto y quien ve el código real elige mejor el camino más simple que cualquier proceso fijo. Se acepta deuda táctica razonable cuando acelera la entrega sin comprometer la corrección.

## Mínimos del proyecto (y por qué)
1. **Módulos cohesivos y dependencias mínimas (Python >= 3.11)**: agrupa cada responsabilidad en su propio módulo para evitar monolitos difíciles de adaptar; prefiere la librería estándar para mantener ligera la instalación, añadiendo dependencias externas solo si evitan reimplementar lógica compleja o frágil.
2. **Verificación real en verde**: al dar libertad en el camino, la garantía objetiva es comprobar el resultado con pruebas ejecutables (`python -m unittest <modulo>`, discriminando la causa raíz si es un bug), formato y lint (`python -m ruff format` y `python -m ruff check`) y limpieza de archivos distribuibles (`python -m unittest tests/test_instructions_cleanliness.py`).
3. **Pruebas aisladas y cambios fuera del repo solo a petición**: los tests deben simular servicios externos y directorios de usuario (como la API de Telegram o `~/.adevv`) para no enviar avisos de prueba reales ni pisar el entorno activo; no modifiques credenciales y ejecuta acciones que impacten fuera de la rama actual (`push`, `/release` o instalar en `~/.adevv`) solo cuando el usuario lo pida expresamente.
