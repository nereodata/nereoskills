# Diseño Técnico: B-ADV-0032 — Terminación acotada de arneses con JSON

## Cambios

- **[MODIFY]** `skills/orquestar/orquestar.py`: encapsula la captura JSON de `agy` y `claude` en lectura concurrente de ambos streams, detecta la respuesta final y termina el árbol tras una gracia limitada; propaga `timeout_s` desde el perfil y el entorno.
- **[MODIFY]** `tests/test_orquestar.py`: comprueba el cierre forzado tras JSON, el timeout previo al JSON y el `stdin` cerrado de `agy`.

## Mapa de impacto

- Llamantes: `lanzar()` es consumido por `ejecutar()` y `agente()`; ambos reciben las métricas de `timeout` y `cierre_forzado` sin cambiar su contrato de retorno.
- Pruebas: se amplía `SubprocesoColgadoTests`; ninguna prueba previa queda invalidada.
- Decisiones contradichas: ninguna.
- Camino caliente: el sondeo es de 20 ms únicamente mientras el arnés está activo; las pruebas con procesos reales verifican que no queda esperando EOF.

## Testeabilidad

Los procesos Python de prueba emiten JSON y permanecen vivos deliberadamente, permitiendo verificar el corte sin depender de un proveedor externo.
