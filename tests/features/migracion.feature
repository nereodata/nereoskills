# language: es
Característica: Migración de proyectos con submódulo

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
