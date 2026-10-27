# Diseño técnico: B-ADV-0020

Se conserva el motor Python y el registro JSONL append-only de la plataforma.

## Cambios y política común
- MODIFY `skills/orquestar/orquestar.py`: clasificar fallos con `cuota_tipo` (real/supuesta) y `cuota_origen` (hora en la respuesta/sin hora en la respuesta/sin créditos). El parser público `espera_cuota` conserva su fallback 1800 por compatibilidad; acepta `sin_hora=None` para detectar ausencia de hora. La ejecución usa `cuota_reintento_s` positivo finito, 300 por defecto, para sospechas y créditos.
- Un plegado común de métricas calcula marcas, recuperaciones y consumo sin alterar tokens. Las marcas históricas sin clasificación de 1800 segundos son supuestas; las demás mantienen su recuperación, incluidos 3540 segundos restantes del escenario histórico.
- NEW evento `cuota_recuperada`, arnés/modelo, invalida marcas anteriores del par. Éxito y `--cuota-reset [harness[/modelo]]` añaden este evento. El reset resuelve los pares existentes y no afecta ajenos.
- Sondeos por raíz/par en memoria del proceso: sin sondeo previo se permite comprobar una sospecha al relanzar; después se respeta el intervalo. El sondeo ejecuta una vez el trabajo pendiente y aprovecha el resultado.
- La espera de cuota comprueba recuperaciones cada 30 segundos y respeta parada. La espera de red conserva su comportamiento.
- Créditos: aviso Telegram específico una vez por episodio persistido, incluso entre procesos; éxito/reset lo rearma. Suprimir aviso genérico de cuota al esperar por créditos.
- NEW `test_cuota_supuesta.py`; MODIFY pruebas existentes cuyo contrato de espera en ejecución pasa de 1800 a 300. MODIFY README, manual y guía de orquestación.

## Mapa de impacto
- `configuraciones_con_cuota`: llamantes `agente` y `bucle`; ambos quieren la política nueva. La selección puede quedar vacía: los consumidores ya conservan la señal de espera mediante `cuota_descartada`. Se eliminan las excepciones de configuración única y última reserva agotada para respetar tanto el reinicio real como el límite de sondeo supuesto. Se actualizan esos dos tests de `test_cuota_vigente`, conservando el escenario de espera y añadiendo ausencia de lanzamientos; el contrato nuevo exige no probar una marca real antes de tiempo.
- `consumo_cuotas`: llamantes selección, `cuota_descartada`, `informe_agentes`, pruebas e integración Telegram. Conserva `(uso, deadlines)`; plegado común incorpora recuperación sin alterar consumo.
- `espera_cuota`: agente, reanudación, bucle y tests del parser; conservan firma compatible y valor de compatibilidad. La clasificación de ejecución se centraliza aparte.
- `esperar`: bucle para cuota y red; solo cuota observa reset.
- C1: selección e informe reciben las mismas filas para plegar cuotas y detalle; `consumo_cuotas` acepta una instantánea opcional sin cambiar el retorno ni la llamada antigua.
- C2: `esperar(..., cuotas_esperadas=None)` recibe del bucle el índice del JSONL anterior a seleccionar y los pares del paso. Revalida recuperaciones desde ese índice, incluyendo pares de fallos de subagentes del mismo paso. Así detecta el reset anterior a entrar en espera y durante ella; las esperas de red no usan contexto. La prioridad de parada permanece. Las pruebas que simulan `esperar` aceptan el contexto y avanzan el reloj cuando corresponde.
- C3: el aviso genérico se suprime únicamente por créditos vigentes del perfil que motivó la espera o del subagente que acaba de comunicar ese mismo plazo. Los antecedentes ajenos no intervienen.
- `main`: despachador de CLI y pruebas; añade opción de recuperación antes de arrancar bucle, sin gateway. `resumen` e `informe_agentes` comparten formato de certeza/origen y hora.
- Contrato modificado: aserciones de espera en `tests.test_orquestar` y `test_fallos_arnes` que fijan 1800 pasan a 300 para ejecución sin hora. Parser 1800 y marcas históricas 3600 quedan intactos. No se elimina ningún escenario.
- `test_estado_agentes` conserva los escenarios de persistencia con el nuevo intervalo 300. `test_arnes_ausente.test_cuota_se_conserva_si_ultima_reserva_ausente` sustituye el fixture de créditos y parser simulado por una respuesta real «usage limit resets in 58 minutes» (3480 + margen 120 = 3600), manteniendo las aserciones de recuperación a las 18:00 UTC. Los créditos se verifican como supuestos en el test nuevo.
- Decisión contradicha: `skills/orquestar/SKILL.md:113` prescribe fallback de 30 min; reemplazado por la decisión humana explícita del bug. Ninguna decisión arquitectónica cambia.
- Referencia temporal: fechas ISO normalizadas con `fecha_estado`, segundos para intervalos; el sondeo compara el reloj de estado, inyectable por pruebas, dentro del proceso.
- Camino frecuente: plegado lineal del JSONL como antes; comprobar mediante regresiones de selección y conteo de lanzamientos, sin consultas externas ni esperas reales. El reset solo escribe recuperaciones calculadas desde marcas, nunca desde el consumo de tokens.

## Verificación
Comandos exclusivos del triaje. JSONL real en temporales, reloj/arneses/Telegram simulados, fase roja previa, revisiones independientes de Hades y evidencia con `--verificar`. Sin dependencias ni herramientas de lint/tipado configuradas en el proyecto; compilación y `git diff --check` aplicables.
