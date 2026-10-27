# Revisión de código: B-ADV-0019

- **Revisor:** Hades. **Fecha:** 2026-10-27.
- **Artefacto:** delta sin commitear obtenido mediante `git status` y `git diff`, incluidos los nuevos `tests/aislamiento_telegram.py` y `tests/test_aislamiento_telegram.py`.
- **Contrato:** descripción y triaje de B-ADV-0019; plan de plataforma. Diseño de tarea omitido expresamente en el triaje.
- **Alcance:** infraestructura de aislamiento de pruebas e integración en las suites. No hay cambios de lógica de producción. Las pruebas se leen como contexto; esta revisión no sustituye a `/review-test`. El prompt temporal no constituye código del bug.

## Veredicto: APROBADO

Media **9/10**, sin hallazgos críticos ni altos. No se identifican hallazgos que requieran corrección.

## Análisis estático y evidencia

Se reutiliza la verificación verde aportada por el invocante mediante `adevv orquestar --verificar`: suite de `tests/` y módulos de ambas skills, con y sin las variables `TELEGRAM_*`. No se relanzan pruebas ni comprobaciones cubiertas por esa evidencia.

En `orquestar_evidencias.jsonl` consta además la ejecución conjunta satisfactoria de `unittest discover -s tests` y los veinte módulos de `skills/orquestar` y `skills/telegram_gateway`, del 2026-10-27 a las 06:53:34, árbol `91f1f1e6cee2d931bf184f235ca94f524a2c62f4`, código 0. Ese registro no explicita las dos variantes ambientales: esa parte se acepta de la evidencia comunicada por el invocante. Los intentos anteriores fallidos no son la evidencia final.

No se atribuyen resultados adicionales de lint, tipado o escáner de secretos. La inspección del delta no revela secretos, comandos de shell nuevos ni dependencias añadidas; auditoría de dependencias no aplicable.

## Puntuaciones

| Criterio | Nota | Evaluación |
|---|---:|---|
| Corrección | 9 | El soporte elimina las tres credenciales al cargarse y bloquea el transporte empleado por los dos motores. |
| Seguridad | 9 | El bloqueo ocurre antes de abrir la conexión y no incluye token ni URL en el error. |
| Conformidad | 9 | Implementa el módulo común previsto por el triaje, su importación en todas las suites y la simulación explícita del envío causante. |
| Calidad | 9 | Protección centralizada, pequeña y sin duplicación de su lógica entre suites. |
| Eficiencia | 9 | Instalación una vez por proceso; comprobación constante por petición, sin procesos ni acceso a red adicionales. |
| Documentación | 9 | El soporte documenta los efectos de importación y cómo deben simular el envío sus consumidores. No cambia el contrato del producto. |
| **Media** | **9** | |

## Evaluación

`tests/aislamiento_telegram.py` elimina `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USER_IDS` y `TELEGRAM_CHAT_ID` antes de ejecutar las pruebas. Los subprocesos que heredan ese entorno reciben las credenciales eliminadas. El envoltorio de `urllib.request.urlopen` añade una segunda defensa en el proceso de pruebas frente a credenciales introducidas expresamente o leídas de un `.env`. Acepta tanto URLs como objetos con `full_url`, conserva argumentos y retorno para otros destinos y evita envolver repetidamente la función ya protegida.

Los dos puntos reales de acceso a Telegram del repositorio usan `urllib.request.urlopen`: `orquestar.enviar()` y la consulta de actualizaciones del gateway. `EnvioRealBloqueado` deriva de `BaseException`, por lo que los manejadores de `Exception` del transporte no silencian el intento de envío. Los parches explícitos de las pruebas pueden sustituir el transporte y restauran después la protección. El bloqueo del transporte es local al intérprete; no se presupone que el envoltorio se propague a procesos hijos.

Las suites existentes cargan el soporte común. En `test_autoarranque_windows.py`, el proceso hijo con `--lanzador` conserva deliberadamente las credenciales de prueba: `lanzador_ficticio()` simula `Popen` y `escuchar`, y evita la exclusión real. Esta excepción permite observar la resolución de credenciales sin lanzar el gateway ni consultar Telegram.

La prueba que originó el bug simula ahora `motor.enviar` de forma explícita, incluso con token ambiental definido. El cambio no depende únicamente de que el soporte borre el entorno. Se leen las nuevas regresiones como evidencia contextual de la integración, sin reabrir su revisión independiente de cobertura.

El cambio permanece en el soporte y los módulos de pruebas autorizados. El triaje documenta la solución aplicada y permite omitir diseño y documentación de usuario. No introduce capas ni dependencias que requieran una decisión de arquitectura.

Solo se escribe este informe; no se corrige código ni se crea commit.
