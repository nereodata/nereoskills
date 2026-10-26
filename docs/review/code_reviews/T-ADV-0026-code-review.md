# Revisión de código: T-ADV-0026

- **Revisor:** Hades. **Fecha:** 2026-10-26. **Modo:** orquestado. **Ronda:** única revisión del delta completo.
- **Artefactos:** `git diff HEAD` de `skills/telegram_gateway/gateway.py`, `skills/telegram_gateway/SKILL.md` y `CHANGELOG.md` (55 inserciones y 8 eliminaciones).
- **Referencias:** `docs/design/T-ADV-0026-design.md`, tarea T-ADV-0026 y DEC-ESP-01/02/03; seis escenarios aprobados en `skills/telegram_gateway/features/telegram_gateway.feature`; plan de plataforma, DEC-P03/P09/P10 y reglas de capas.
- **Contexto consultado:** funciones existentes del motor que consume el delta, exclusivamente para comprobar sus contratos de configuración, lanzamiento, cuota y persistencia. Sin revisión del motor completo, del WIP ni de las pruebas.

## Veredicto: APROBADO

Media **9,17/10**. Sin hallazgos críticos, altos, medios ni bajos. No hay correcciones ni impedimentos que enrutar con `para` y `destino`.

## Puntuaciones

| Criterio | Nota | Motivo |
|---|---:|---|
| Corrección | 9 | Conmutación por causas delimitadas, consulta de cuota vigente, retorno por prioridad y conservación de sesiones propias. Errores ordinarios mantienen el reintento sin sesión y su excepción. |
| Seguridad | 9 | Se conserva la autorización antes de conversar; no se añaden credenciales, dependencias, destinos de red ni construcción de órdenes mediante shell. El delta no introduce transferencia de sesiones entre usuarios o arneses. |
| Conformidad | 10 | Implementación fiel al diseño adaptado, las decisiones del especificador y las capas de plataforma. Contrato triple de invocación conservado y cambios operativos limitados al gateway existente. |
| Calidad | 9 | Excepciones específicas, recorrido único de candidatos y reutilización de los contratos del motor; separación clara entre indisponibilidad y error ordinario. |
| Eficiencia | 9 | Una consulta compartida de cuotas por mensaje, sin procesos para candidatos ya agotados y sin esperas de recuperación. Recorrido secuencial proporcional a las reservas configuradas. |
| Documentación | 9 | Skill y changelog describen conmutación, sesiones propias, retorno, diagnóstico y cuotas compartidas; las nuevas excepciones tienen docstrings. |
| **Media** | **9,17** | |

## Comprobación funcional y de conformidad

- **Configuración y orden:** se conserva la combinación Atenea/Telegram y se utiliza `motor.lista_reservas`, sin duplicar la herencia de campos ni la normalización objeto/lista. La posición original identifica cuándo la respuesta corresponde a una reserva.
- **Cuota compartida:** `invocar` detecta cuota sobre la salida cruda de una ejecución fallida, antes de extraer su texto. Registra las métricas originales junto a fecha, arnés, código, modelo y duración de agotamiento. El diagnóstico calcula la recuperación desde esa misma fecha y duración, compatible con `consumo_cuotas`; no se registra cuota por ausencia o fallo de arranque.
- **Disponibilidad:** `conversar` omite los agotamientos vigentes incluso con un único candidato, conforme a DEC-ESP-03. No duerme para recuperar cuota. Las ausencias mantienen `registrar_ausencia`; `ModeloIndisponible` permite continuar por cuota o por `OSError` del lanzador. La captura no engloba la escritura posterior de métricas, por lo que no convierte un fallo de persistencia en indisponibilidad del modelo.
- **Sesiones:** cada candidato consulta el par usuario/arnés; una reserva puede reanudar su sesión propia, conforme a DEC-ESP-01. Solo se guarda la sesión del respondedor. Cada mensaje vuelve a recorrer desde el titular y conserva las sesiones de los demás arneses.
- **Errores ordinarios y contrato de llamada:** `invocar` sigue devolviendo `(codigo, sesion_id, texto_respuesta)` en su retorno normal. Un fallo ordinario con sesión permite un reintento sin sesión; si continúa fallando, propaga `RuntimeError` y no prueba reservas. `responder` transforma únicamente `GatewayNoDisponible` en diagnóstico firmado.
- **Transparencia:** la respuesta de éxito firma el perfil efectivo y señala reserva según su posición. Si ningún candidato responde, los motivos identifican cada perfil, con recuperación ISO UTC cuando corresponde; se conserva el aviso `error`.
- **Alcance y arquitectura:** DEC-ESP-02 se respeta como decisión de recuperación de especificación sin fusionar WIP; el desarrollo posterior sigue el triaje autorizado. El delta no altera los escenarios aprobados. Usa solo stdlib (DEC-P03), conserva la lógica operativa en `skills/` (DEC-P09/P10) y reutiliza el motor sin introducir dependencias inversas ni una implementación paralela.
- **Documentación:** el texto sustituye la regla anterior de sesión siempre nueva en reservas por el contrato aprobado de sesión propia y documenta las nuevas causas de conmutación. El changelog refleja el comportamiento implementado sin anticipar el cierre de la tarea.

## Análisis estático, pruebas y evidencia reutilizada

Se comprobaron las entradas de `orquestar_evidencias.jsonl`. Las siguientes verificaciones constan con **código 0** sobre el mismo árbol **`a12d8a24761c05e4bcde9b7deb39fa1a354232c4`**, mediante `adevv orquestar --verificar`, el 2026-10-26:

| Hora del registro | Comando | Resultado |
|---|---|---|
| 21:19:09 | `python -m unittest discover -s skills/telegram_gateway -p test_*.py` | Verde; 45 pruebas según evidencia comunicada por el invocante. |
| 21:19:21 | `python -m unittest discover -s tests -p test_telegram_gateway.py` | Verde; 24 pruebas según evidencia comunicada por el invocante. |
| 21:19:22 | `python -m unittest discover -s skills/orquestar -p test_arnes_ausente.py` | Verde; 9 pruebas según evidencia comunicada por el invocante. |
| 21:19:23 | `python -m py_compile skills/telegram_gateway/gateway.py skills/telegram_gateway/test_reservas.py` | Verde. |
| 21:19:24 | `git diff --check` | Verde. |

El invocante declara que, tras verificar, solo actualizó el texto del diseño y la anotación de resolución de H-01 en el reporte de pruebas. Se reutiliza esta evidencia para el delta de producción recibido. Los registros JSONL acreditan comandos, árbol y salida correcta; no contienen los conteos de pruebas, que se atribuyen expresamente al invocante.

Para aislar las pruebas existentes del bucle, el invocante retiró `TELEGRAM_BOT_TOKEN` y `TELEGRAM_ALLOWED_USER_IDS` únicamente del entorno de comprobación. No es un cambio de producción. La revisión de pruebas previa permanece **APROBADA (8,75)** y se acepta su H-01 como resuelto según la anotación recibida; no se vuelven a auditar las pruebas.

No hay linter ni tipado configurado aplicable al delta. No cambian manifiestos ni dependencias, por lo que no procede auditoría de dependencias nuevas. La inspección del diff no muestra secretos añadidos ni cambios en la obtención de credenciales. La valoración de seguridad se limita al delta y no constituye una auditoría global del gateway o de los arneses.

## Hallazgos y enrutado

Ninguno. Sin acciones para `desarrollador`, `especificador` o `humano`; sin destinos `resolver`, `registrar` o `descartar` pendientes.

## Límites y entrega

Revisión por lectura realizada una sola vez. No se repitieron verificaciones verdes, no se ejecutaron pruebas adicionales ni suite completa y no se modificaron producción o pruebas. Solo se crea este informe, sin commit ni cambio del estado de la tarea. El cierre permanece a cargo de Artemisa conforme al flujo orquestado.
