---
id: T-ADV-0041
title: "Desarrollo autónomo guiado por política con continuidad verificable"
type: funcional
weight: 110
dificultad: dificil
version: "v1.2.0"
status: in_progress
depende_de: ["T-ADV-0039"]
created_at: 2026-11-14
updated_at: 2026-11-14
---

# T-ADV-0041 · Flujo autónomo ligero y continuidad de v1.2

Coordina la entrega integrada descrita en [v1.2.md](../versions/v1.2.md) bajo la política de [PROJECT.md](../../../PROJECT.md):
- Motor único ligero activo por defecto (política local o base embebida), presupuesto duro separado de cuota y relevo portable entre sesiones/modelos (`adevv/contexto_ejecucion.py` conectado al orquestador).
- Fin de las subfases obligatorias A–F y de las revisiones a mitad de tarea: verificación determinista rápida (`unittest` + lint/modularidad) y revisión independiente solo post-verde en superficies críticas o cierre.
- Reutilización del trabajo válido adelantado en `T-ADV-0033/34/35/37/40` y coordinación con `B-ADV-0031`, dejando `T-ADV-0038` y `B-ADV-0049` como entregas focalizadas.
