# Diseño Técnico: T-ADV-0010 · Modelos de reserva ante agotamiento de cuota

## 1. Resumen y Contexto
El objetivo de **T-ADV-0010** es dotar a `/orquestar` de resiliencia operativa inmediata ante el agotamiento de cuota o créditos de un proveedor de IA. En lugar de detener el bucle durante horas esperando a la recuperación de cuota de un único modelo, cada rol (`atenea`, `artemisa`, `hades`, `clio`, `cronos`) o subbloque de configuración (`pasos.<paso>`, `dificultad.<nivel>`) puede definir modelos o arneses de reserva (`reserva`).

Cuando se detecta agotamiento de cuota (`espera_cuota(salida) is not None`), tanto las llamadas a subagentes (`agente()`) como las ejecuciones de pasos del bucle (`bucle()`) conmutan automáticamente a la siguiente reserva configurada, registrando cada intento en `orquestar_metricas.jsonl`. Solo cuando el modelo principal y todas sus reservas están sin cuota se entra en espera (`esperar()`).

## 2. Decisiones de Arquitectura y Diseño

- **DEC-D01 (Estructura y herencia de `reserva`):**
  - La clave `reserva` en un rol o subbloque puede ser un objeto único `{"harness": "...", "model": "...", "effort": "..."}` o una lista ordenada `[{"model": "..."}, ...]`.
  - Se implementa `lista_reservas(cfg_rol)` que normaliza cualquier formato a una lista ordenada de diccionarios.
  - Cada entrada de reserva hereda los campos `harness`, `model` y `effort` (así como `instructions` si existen) del rol base que no redefina explícitamente.
  - Los subbloques de configuración (`pasos.<paso>`, `dificultad.<nivel>`) pueden definir o sobrescribir `reserva`, respetando la jerarquía resuelta por `ajustes()`.

- **DEC-D02 (Conmutación automática en `agente()`):**
  - En `agente(root, rol, prompt)` se evalúa la secuencia `[cfg_principal] + lista_reservas(cfg)`.
  - Para cada configuración en orden:
    - Se resuelve sesión si coincide el arnés con la sesión previa del mismo ID (`buscar_sesion_agente`).
    - Si se produce un fallo con cuota (`cuota = espera_cuota(salida) is not None`) y quedan más reservas por probar:
      - Se registra el intento agotado en `orquestar_metricas.jsonl` (sin `sin_cuota: True` para no confundir al bucle).
      - Se conmuta de inmediato a la siguiente reserva.
    - Si se agotan el principal y todas las reservas por cuota:
      - Se registra el último intento en `orquestar_metricas.jsonl` con `sin_cuota: True` y `espera_s = min(cuotas_acumuladas)`.
      - Se muestra mensaje en consola y se retorna el código de salida para que el paso termine y el bucle espere.
    - Si cualquier intento finaliza sin error de cuota (éxito o rechazo normal):
      - Se registra en métricas de forma habitual y se retorna el código.

- **DEC-D03 (Conmutación automática en `bucle()`):**
  - En `bucle()`, al ejecutar el paso principal con `cfg_rol`:
  - Se obtienen las reservas del paso: `configs_a_probar = [cfg_rol] + lista_reservas(cfg_rol)`.
  - Si `ejecutar()` falla por falta de cuota propia (`espera_cuota(salida) is not None`):
    - Si quedan reservas configuradas:
      - Se registra el intento en `orquestar_metricas.jsonl`.
      - Se reintenta inmediatamente con la siguiente configuración de reserva.
      - Si el arnés cambia respecto al intento anterior, se inicia sesión nueva (`sesion=None`); si es el mismo arnés, se puede conservar la sesión.
    - Solo si se agotan el modelo principal y todas las reservas configuradas:
      - Se toma la menor espera de cuota registrada: `cuota = min(cuotas_propias)`.
      - Se entra en `esperar(root, cuota)` conforme a las políticas existentes de `--espera-max`.

- **DEC-D04 (Documentación en `/orquestar`):**
  - Se actualiza `skills/orquestar/SKILL.md` en la sección de Roles documentando la sintaxis y comportamiento de `reserva`.
  - Se actualiza la sección Sin cuota explicando la conmutación secuencial antes de entrar en reposo.

## 3. Plan de Pruebas Unitarias
1. `test_lista_reservas_normalizes_object_and_list_with_field_inheritance`:
   - Objeto único hereda `harness` y `effort` si solo define `model`.
   - Lista de objetos hereda selectivamente campos no especificados.
   - Configuración sin `reserva` devuelve lista vacía `[]`.
2. `test_agente_switches_to_reserva_on_quota_and_succeeds`:
   - El modelo principal falla con error de cuota (`out of credits`).
   - La reserva configurada responde con éxito.
   - Verifica que se registraron ambos intentos en métricas y que no se registró `sin_cuota: True`.
3. `test_agente_exhausts_all_reservas_records_min_quota_and_fails`:
   - El modelo principal y 2 reservas fallan por cuota (ej. 3600s, 1800s, 7200s).
   - Se comprueba que el registro final contiene `sin_cuota: True` y `espera_s: 1800`.
4. `test_loop_retries_immediately_with_reserva_on_quota_without_waiting`:
   - El paso principal falla por cuota propia.
   - Con reserva configurada, `bucle()` no llama a `esperar()` e invoca de inmediato `ejecutar()` con la reserva.
5. `test_loop_reserves_change_harness_starts_fresh_session`:
   - Al conmutar a reserva con arnés distinto, no reanuda la sesión previa (`sesion=None`).
