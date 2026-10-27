---
id: B-ADV-0011
title: "Un fallo del arnés que no es de cuota para el bucle sin reintentar ni usar reservas"
type: bug
weight: 15
dificultad: media
version: "v1.0.0"
status: completed
depende_de: []
origen: "Revisión humana de los puntos de parada de orquestar.py (2026-10-27): para sin necesitar al humano"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0011: Un fallo del arnés que no es de cuota para el bucle sin reintentar ni usar reservas

## 🎯 Descripción del Fallo

**Causa raíz**: en `bucle()` (`skills/orquestar/orquestar.py`, hacia la línea 2447), si el arnés termina con código distinto de 0 y no se detecta falta de cuota, el bucle para con «el arnés terminó con código N (¿autenticación, red?)». Las reservas solo se prueban si falta cuota (`espera_cuota()`) o si no se encuentra el arnés (`ArnesAusente`).

**Comportamiento observado**: un corte de red, un error 5xx de la API o un cuelgue del arnés paran el bucle desatendido entero, a menudo de noche.

**Comportamiento esperado**:
1. Reintenta el mismo perfil con espera creciente (por ejemplo, 1, 5 y 15 min), con un tope configurable.
2. Si sigue fallando, pasa a la siguiente reserva de `lista_reservas()`, igual que cuando falta cuota.
3. Solo para si fallan todas las configuraciones tras los reintentos. El aviso incluye la cola de la salida del arnés para distinguir un problema de autenticación (que sí requiere a una persona) de uno de red.
4. Se mantiene el caso actual de «paso completado en disco a pesar del retorno».
5. Pruebas con un arnés simulado que falla de forma transitoria y otro que falla de forma persistente.

## 🔓 Alcance (decisión humana, 2026-10-27)
El usuario ha pedido este cambio expresamente: el bucle solo debe pararse cuando haga falta una decisión humana. Si hay que cambiar requisitos o escenarios del bucle (orquestar), forma parte del alcance de este bug. Se puede tocar cualquier ruta necesaria.

## Triaje
- Subfase A: [EXEC] Contrato de recuperación de pasos del bucle; BDD en orquestacion.feature.
- Subfase B: [EXEC] Reintentos acotados, reservas, métricas y parada cooperativa.
- Subfase C1: [EXEC] Arnés simulado transitorio/persistente, reservas, cuota, parada y progreso en disco.
- Subfase C2: [EXEC] Solo bucle y opciones de CLI, sin extender agente() ni gateway.
- Subfase D: [EXEC] Hades sobre el delta completo.
- Subfase E: [EXEC] Guía de orquestación y skill distribuida.
- Subfase F: [EXEC] Cierre y commit.
- Verificación al cierre: `python -m unittest discover -s skills/orquestar -p test_fallos_arnes.py` y regresiones `test_arnes_ausente.py`, `test_cuota_vigente.py`, `test_recarga.py`, más `python -m unittest discover -s tests -p test_orquestar.py`; ejercitan ejecución, reservas, cuota, recarga y CLI. Estático: `git diff --check` y compilación de los Python modificados; sin linter/tipador configurado ni dependencias nuevas.

## Decisiones en modo orquestado
- DEC-11: La decisión humana del alcance sustituye para pasos del bucle el contrato antiguo de orquestacion.feature:66 y test_arnes_ausente.py::test_errores_operacionales_no_prueban_reservas. Se conserva ese contrato para agente y gateway; se adapta explícitamente su alcance, sin eliminar su escenario.
- DEC-12: `--reintentos-arnes` entero no negativo, por defecto 3 (adicionales al intento inicial), con esperas 60, 300 y 900 segundos, repitiendo 900 para límites mayores. Cero permite pasar inmediatamente a reservas. No consume el contador de pasos ni de falta de progreso.
- DEC-13: La cuota conserva su circuito y prioridad. Un fallo ajeno a cuota agota los reintentos de su perfil antes de probar reservas; al cambiar perfil se empieza sin sesión heredada de un fallo operacional. La salida final incluye los últimos 2000 caracteres del último arnés ejecutado.

## Evidencia
- Base estable: `95b3d0bd2f8daace92f9688a366fe04dab06f59b`.
- RED: `docs/review/test_reviews/B-ADV-0011-red.txt` y registro de verificación.
- Verificación dirigida: 14 pruebas del arreglo, 9 de ausencia, 8 de cuota vigente, 11 de recarga y 70 de regresión del motor (112 en total), todas verdes mediante `--verificar`.
- Estático: compilación Python del delta y `git diff --check` verdes. No hay linter ni tipador declarados; sin dependencias nuevas. La versión instalada no admite `--calidad`; se verifica su equivalente del árbol mediante `adevv orquestar --verificar "python skills/orquestar/orquestar.py --calidad --base 95b3d0bd2f8daace92f9688a366fe04dab06f59b"` (sin ejecutar suites).

- Hades código H-01/H-02: comparar cuota omitida y del paso, reconsiderar perfiles recuperados una sola vez, descontar las esperas y registrar modelo sin depender del consumo. Cuatro regresiones dirigidas añadidas al mismo test_fallos_arnes.py (14 pruebas en total).


## Cierre
- Hades: especificación, pruebas y código APROBADOS. H-01/H-02 de código corregidos y cubiertos por cuatro regresiones adicionales.
- H-03 medio de código (destino resolver): renovadas después del último cambio de producción las cuatro regresiones del triaje (9/8/11/70), con `--verificar` desde el entorno principal. Junto a los 14 casos del arreglo, 112 pruebas verdes. El entorno restringido de Hades no llegó a ejecutarlas por el bloqueo de la huella Git; la verificación principal sí terminó correctamente.
- Sin deuda ni bloqueos pendientes. Documentación y validación humana diferida registradas en `docs/review/versions/v1.0-revision.md`.
