# Diseño técnico: B-ADV-0012

Se conserva el selector y la promoción existentes. Solo la rama sin progreso de `bucle()` cambia: tras agotar la promoción, task-dev/bug-fix persisten un bloqueo humano y continúan con contador reiniciado. Los errores operacionales del arnés conservan su recuperación y parada propias.

## Cambios
- [MODIFY] skills/orquestar/orquestar.py: helper de bloqueo local; escribe frontmatter, motivo y revisión humana, confirma únicamente esos dos documentos y avisa por el canal respuesta. El motivo incluye intentos, dificultad y últimos 2000 caracteres indentados para que la salida no altere el Markdown/frontmatter.
- [MODIFY] tests/test_orquestar.py: integración con Git/backlog reales y arnés/Telegram aislados; task-dev/bug-fix difíciles y promoción media previa.
- [MODIFY] skills/orquestar/SKILL.md, docs/orquestacion.md y CHANGELOG.md: contrato operativo del bloqueo local.

## Mapa de impacto
`bucle()` es consumido por main() y las pruebas del motor: ambos adoptan la continuidad solo para desarrollo sin progreso. El helper nuevo solo se llama desde esa rama. `estado()`, `pendientes_de()`, `promover_dificultad()` y `registrar_fallo_suite()` mantienen firma y semántica. Los tests previos no se modifican; SuiteRecoveryTests y DificultadTests comprueban las reglas conservadas. Los dos escenarios @B-ADV-0012 son la especificación aprobada.

La frase de parada general en skills/orquestar/SKILL.md:111 queda sustituida por la excepción autorizada en el bug. No se contradice ninguna decisión de arquitectura: motor Python stdlib y backlog Markdown/Git existentes. No hay unidades ni fronteras temporales nuevas. El camino normal no añade operaciones: las escrituras/commit solo ocurren al agotar los intentos. La integración comprueba que el siguiente arnés recibe un árbol limpio y que las dependientes siguen pendientes.

DEC-12-D1: commit acotado a bug/tarea y revisión de versión antes de continuar, siguiendo el precedente de registrar_fallo_suite; no se confirma trabajo ajeno. Si falla la persistencia/Git se propaga el error, sin fingir continuidad.
