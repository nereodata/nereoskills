# B-ADV-0042 · Revisión independiente de código

**Veredicto: APROBADO**
**Media: 9,17/10**

## Alcance

Revisión estática del delta de producción de `skills/orquestar/orquestar.py`, con el contexto adjunto de creación y terminación del grupo, captura JSON y consumidores `agy`/`claude`.

Se aplica el mandato adjunto de Hades y `/review-code`. No se modifica el checkout, no se delega ni se repiten verificaciones acreditadas.

## Evaluación

La nueva llamada a `_terminar_arbol_proceso(p)` cierra la salida que dejaba descendientes sin supervisión cuando el padre ya había terminado y ambos lectores habían finalizado.

En POSIX, la captura crea una sesión propia y el helper señala su grupo mediante el PID del líder, incluso después de su salida. La ausencia del grupo se admite mediante `ProcessLookupError`.

La limpieza sucede después de recoger el estado del padre y finalizar los lectores. No cambia `por_timeout` ni `cierre_forzado`, ni altera los buffers capturados. El código de retorno del padre se conserva: `p.poll()` ya lo ha registrado antes de la terminación residual. Windows mantiene su cierre mediante Job Object.

## Evidencia y análisis estático

Para el árbol `94251f2b45bb85630bcdb56d359a0fbab4afe372` constan en verde:

- `git diff --check`.
- Compilación de los dos archivos Python modificados.
- `SubprocesoColgadoTests`: 13 pruebas, dos omitidas en Windows.
- Regresión real en Linux: conservación del resultado JSON y terminación del descendiente con salidas redirigidas.

Formato y lint figuran omitidos por ausencia de herramientas; tipado y escáner de secretos no están configurados. Se registran como omisiones, no como comprobaciones superadas. El delta no introduce credenciales, dependencias ni configuración.

## Puntuaciones

| Criterio | Nota | Fundamento |
|---|---:|---|
| Corrección | 9/10 | Cierra el grupo en la salida normal preservando el resultado y los indicadores del padre. |
| Seguridad | 9/10 | Reutiliza la terminación del grupo aislado creado por la captura. |
| Conformidad | 10/10 | Cumple C2 del triaje y el contrato POSIX existente, sin cambios de interfaz ni arquitectura. |
| Calidad | 9/10 | Cambio mínimo, localizado y apoyado en el helper existente. |
| Eficiencia | 9/10 | Añade una única limpieza al finalizar, sin sondeos adicionales. |
| Documentación | 9/10 | El comportamiento sigue siendo compatible con el contrato documentado; no exige cambios de uso. |

## Hallazgos

El hallazgo que origina B-ADV-0042 queda **resuelto** dentro del alcance revisado. No se identifican hallazgos nuevos.

## Limitaciones

La comprobación real POSIX aportada corresponde a Linux Alpine bajo QEMU; no acredita ejecución en otros sistemas POSIX. El dictamen se limita al delta y al contexto suministrados, sin extenderse a otras rutas del motor.
