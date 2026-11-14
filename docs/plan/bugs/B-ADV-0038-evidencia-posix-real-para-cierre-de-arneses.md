---
id: B-ADV-0038
title: "Obtener evidencia POSIX real para terminación de descendientes de arneses"
type: bug
weight: 1001
dificultad: sencilla
version: "v1.4.0"
status: planned
created_at: 2026-11-11
updated_at: 2026-11-14
origen: "B-ADV-0032; docs/review/test_reviews/B-ADV-0032-test-review.md; RT-02"
---

# B-ADV-0038: Evidencia POSIX real del cierre de arneses

## Descripción del fallo

Hades asigna RT-02 (BAJA, registrar) a humano: el equipo actual es Windows sin
WSL instalado. La prueba de integración POSIX está conservada con skip explícito,
pero no se ha ejecutado en un sistema POSIX. Las pruebas deterministas no
acreditan por sí mismas la muerte real del descendiente ni el aislamiento.
Este registro no bloquea el dictamen APROBADO de las pruebas de B-ADV-0032.

## Reproducir y resolver

1. En un entorno POSIX con Python y el repositorio, ejecutar
   `adevv orquestar --verificar "python -m unittest tests.test_orquestar.SubprocesoColgadoTests"`.
2. Conservar evidencia de la prueba real sin skip: timeout y gracia tras JSON,
   grupo distinto del invocador y descendiente ausente o zombi.
3. Corregir cualquier fallo observado antes de declarar validación POSIX real.

## Evidencias

- Windows: 6 pruebas, 5 ejecutadas correctamente, 1 omitida por requerir POSIX.
- Informe de origen: RT-02, revisión independiente de Hades de B-ADV-0032.
