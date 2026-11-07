# B-ADV-0029 · Perfil efectivo de pasos y reservas

Resolver `--harness` una sola vez sobre una copia del principal de cada paso. Si cambia su arnés, retirar modelo y esfuerzo del principal original, igual que el constructor de comandos anterior ya evitaba aplicarlos a otro arnés. Expandir las reservas desde ese principal efectivo: cada campo explícito de reserva prevalece y los omitidos se heredan. Ejecutar el paso con una copia de argumentos sin el override global. Usar esos mismos argumentos y perfiles para cuotas, continuidad de sesión y métricas; no mutar argumentos originales ni `orchestration.json`.

## Impacto

- `bucle`: único consumidor de la resolución nueva; los pasos de desarrollo y análisis usan la misma ruta. `--harness` elige el principal de cada vuelta/paso, también al avanzar en la cadena de análisis sin progreso. La garantía nueva de arnés propio alcanza las reservas de ese principal dentro del intento; no cambia la precedencia sobre el principal seleccionado en otras vueltas.
- `arnes`, `comando` y `ejecutar`: firmas y semántica fuera del bucle intactas. El test `RolesTests.test_each_role_launches_its_own_harness_and_model` conserva su override directo.
- `lista_reservas`: sin cambios; recibe el principal efectivo para heredar correctamente.
- Sesiones: la comparación existente usa ahora el arnés realmente ejecutado. Un cambio de arnés inicia sesión nueva; dentro del mismo arnés se conserva la reanudación por cuota.
- Cuotas: se filtran los pares efectivos incluso con `--harness`; los errores y métricas usan esos mismos pares.
- `--cmd`: no se normaliza; conserva la plantilla explícita y el comportamiento anterior.
- Contrato ajustado por la petición del usuario: precedencia global de `--harness` sobre reservas, documentada ambiguamente en `skills/orquestar/SKILL.md:27` y `:120`, y ayuda de CLI en `orquestar.py:2655`. Actualizar ayuda y manual. Sin cambios de arquitectura, capas, dependencias ni esquema de métricas.
- Pruebas existentes: no se elimina ninguna. `test_cuota_vigente.CuotaVigenteTests.test_bucle_omite_cuota_y_respeta_harness_forzado_y_cmd` fijaba el metadato anterior del modelo incompatible tras un override: se actualiza al principal efectivo con modelo predeterminado, conserva sus cuatro casos y añade una marca vigente sobre ese par efectivo que debe saltar a reserva. Añadir regresiones en `test_reservas_arnes.py` que atraviesan el constructor de comandos real, con y sin override, ambos nombres de rol, herencia y sesiones.
- Camino frecuente: una copia pequeña de argumentos y un diccionario por paso; sin procesos, I/O ni consultas adicionales. Verificación acotada de bucle/reservas y cuotas. No hay unidades ni conversiones nuevas.
