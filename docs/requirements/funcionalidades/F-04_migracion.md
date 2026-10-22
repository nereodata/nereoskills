# F-04 · Migración de proyectos con submódulo
- Prioridad: Must · Ola: A · Recorridos: R3, R4 · Depende de: F-02
- Propósito: pasar un proyecto del submódulo `.agents/` a la instalación sin perder su bucle, sabiendo en todo momento qué falta; incluye el propio repositorio de Adevv y su copia congelada.

## Requisitos

- **RF-F04-01** Cuando se ejecute `adevv migrar` en la raíz de un proyecto, el sistema deberá diagnosticar sin modificar ningún archivo y listar los pendientes agrupados por archivo (máximo 20 pendientes mostrados, más «… y M más (total T).»), terminando con «Sin pendientes (N citas históricas).» o «T pendientes.». Cada pendiente es una ruta, o una ruta y una línea, y cuenta una vez aunque cumpla varios criterios; N cuenta líneas con al menos una cita.
- **RF-F04-02** El sistema deberá contar como pendiente: la entrada `.agents` en `.gitmodules`; la carpeta o enlace `.agents`; `.git/modules/.agents`; los enlaces de `.claude/`, `.codex/` y `.agent/` que apuntan a `.agents`; las claves `instructions` de `orchestration.json` que citan `.agents/`; los elementos locales que ocultan los instalados (lista y criterio de `RF-F02-07`); las copias de Adevv dentro del proyecto (carpetas distintas de la raíz con `skills/orquestar/SKILL.md`, fuera de `.agents`); y las líneas con rutas relativas que empiezan por `.agents/` en archivos en uso. Cada enlace o junction se lista con su tipo y su destino («.agents → C:\…\congelado (junction)»). El diagnóstico no deberá recorrer el contenido de enlaces ni junctions.
- **RF-F04-03** Son archivos en uso, en la raíz del proyecto: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `README.md` (salvo en el repositorio fuente de Adevv, donde documenta la migración), `orchestration.json`, `task_config.yaml`, y todo archivo de texto bajo `scripts/`, `.claude/`, `.codex/`, `.agent/` y `.github/`. Las citas en cualquier otro archivo (p. ej. `docs/review/**`, `docs/plan/**`, evidencias) son históricas: solo se cuentan, no son pendientes. El contenido de `.agents` no se recorre.
- **RF-F04-06** El README de Adevv deberá documentar los pasos de migración en este orden: parar el bucle (`/orquestar parar`) y esperar a que no exista `orquestar.pid`; diagnosticar; quitar el submódulo (`git submodule deinit -f .agents`, `git rm .agents`, borrar `.git/modules/.agents`); quitar enlaces y elementos locales; quitar o corregir `instructions`; cambiar los adaptadores propios para que usen `adevv …`; borrar copias de Adevv; diagnosticar hasta «Sin pendientes»; commit; relanzar `/orquestar`. Para cada enlace o junction deberá dar la orden que lo quita sin seguirlo (en Windows, `cmd /c rmdir <ruta>`) y advertir de que no se use `Remove-Item -Recurse` ni `rm -rf` sobre un enlace, porque borra su destino. Deberá documentar además la migración del propio repositorio de Adevv (parar el bucle que corre desde la copia congelada, instalar la versión publicada, quitar la junction `.agents` sin seguirla, relanzar con `adevv orquestar`) y que `~/.adevv/congelado` solo se borra cuando ningún proceso la usa. `branch_strategy.md §8` deberá sustituirse por un enlace a estos pasos.

_Retirados en la revisión:_ `RF-F04-04` (negarse con un bucle en marcha: el diagnóstico es de solo lectura; parar el bucle es el primer paso documentado) y `RF-F04-05` (códigos de salida que nadie consume). Ver `ciclo/revision.md`.

## Casos límite

| Caso | Comportamiento |
|---|---|
| Afinn hoy: submódulo, `AGENTS.md` con 6 citas, `orchestration.json` con `instructions` a `.agents/`, `scripts/orchestrate.py` que carga el motor por ruta, copia en `.orchestration/nereoskills-source/`, cientos de citas en evidencias | Pendientes: `.gitmodules`, `.agents`, `.git/modules/.agents`, `orchestration.json`, las 6 líneas de `AGENTS.md`, la línea de `scripts/orchestrate.py` y la copia; las evidencias, como históricas |
| Adayy: sin submódulo, citas en reportes y tareas, y en `README.md` | Pendiente: la línea de `README.md`; reportes y tareas, históricos |
| Repositorio fuente de Adevv con la junction `.agents` | Pendiente: `.agents` (junction, con su destino); la raíz no es una copia y su `README.md` no cuenta |
| Enlace `.claude/skills` → `.agents/skills` | Un pendiente (el enlace); su contenido no se recorre |
| Proyecto ya migrado | «Sin pendientes (N citas históricas).» |
| Más de 20 pendientes | Se muestran 20 y «… y M más (total T).» |
| Bucle en marcha en el proyecto | Diagnostica igual (solo lectura); el primer paso documentado es pararlo |

## Criterios de aceptación

```gherkin
@CA-F04-01 @RF-F04-01 @RF-F04-02 @RF-F04-03
Escenario: Diagnóstico de un proyecto con submódulo y adaptadores
  Dado un proyecto con la entrada ".agents" en ".gitmodules", la carpeta ".agents", "AGENTS.md" que cita ".agents/" en 6 líneas, "orchestration.json" con "instructions" a ".agents/agents/hades.md" y 300 citas a ".agents/" en 120 archivos de "docs/review/evidence/"
  Y sin enlaces, sin ".git/modules/.agents" y sin otras citas en archivos en uso
  Cuando ejecuto "adevv migrar"
  Entonces se listan ".gitmodules", ".agents", las 6 líneas de "AGENTS.md" y "orchestration.json" una sola vez
  Y la salida termina con "9 pendientes."
  Y ningún archivo de "docs/review/evidence/" aparece como pendiente
  Y ningún archivo del proyecto ha cambiado

@CA-F04-02 @RF-F04-02
Escenario: Detecta adaptadores, enlaces y copias de Adevv sin recorrer los enlaces
  Dado un proyecto con "scripts/orchestrate.py" que cita ".agents/skills/orquestar/orquestar.py" en una línea, el enlace ".claude/skills" hacia ".agents/skills" y la carpeta ".orchestration/copia/skills/orquestar/SKILL.md"
  Cuando ejecuto "adevv migrar"
  Entonces aparecen la línea de "scripts/orchestrate.py", ".claude/skills → .agents/skills (enlace)" y ".orchestration/copia"
  Y ningún archivo dentro de ".agents/skills" aparece en la salida

@CA-F04-03 @RF-F04-01 @RF-F04-03
Escenario: Proyecto migrado con citas históricas
  Dado un proyecto sin submódulo cuyas únicas citas a ".agents/" están en 3 líneas de 2 archivos de "docs/review/code_reviews/"
  Cuando ejecuto "adevv migrar"
  Entonces la salida termina con "Sin pendientes (3 citas históricas)."

@CA-F04-04 @RF-F04-02 @RF-F04-03
Escenario: El repositorio fuente de Adevv se puede migrar a sí mismo
  Dado el repositorio fuente de Adevv con la junction ".agents" hacia "C:\Users\Iván Moreno\.adevv\congelado"
  Y un "README.md" que documenta "git submodule deinit -f .agents"
  Cuando ejecuto "adevv migrar"
  Entonces el único pendiente es ".agents → C:\Users\Iván Moreno\.adevv\congelado (junction)"
  Cuando quito la junction sin seguirla y repito "adevv migrar"
  Entonces la salida termina con "Sin pendientes"
  Y "C:\Users\Iván Moreno\.adevv\congelado" conserva su contenido

@CA-F04-05 @RF-F04-01
Escenario: Salida acotada
  Dado un proyecto con 35 pendientes
  Cuando ejecuto "adevv migrar"
  Entonces se muestran 20 pendientes y "… y 15 más (total 35)."
```

**Otras verificaciones:** `RF-F04-06` por inspección del README y de `branch_strategy.md` en la revisión de versión, y por la validación funcional de migrar Afinn y el propio Adevv siguiendo los pasos (CE-2, CE-5).
