# Adevv: instalación, actualización y distribución

## Petición original

Hoy Adevv se incorpora a cada proyecto como submódulo de git (`.agents/`). Quiero sustituirlo por un sistema de empaquetado e instalación de Adevv con despliegue y actualización automáticos, de forma que el propio Adevv pueda desarrollarse como un proyecto Adevv (con su backlog) sin que eso afecte a los proyectos que lo usan.

## Encuadre

**Problema.**
- Cada proyecto se trae el repositorio entero de Adevv como submódulo (tests, documentación y, a partir de ahora, su backlog) y hay que actualizarlo a mano en cada uno.
- Las rutas a las skills, los agentes y los scripts (`.agents/skills/orquestar/orquestar.py`, `.agents/agents/hades.md`…) dependen de dónde esté el submódulo en cada proyecto.
- Si `/orquestar` trabaja sobre el propio repositorio de Adevv, el bucle ejecuta el mismo motor y las mismas skills que está modificando.

**Objetivo.** Instalar Adevv una vez por máquina, usarlo en cualquier proyecto con cualquiera de los arneses que uso, y recibir versiones nuevas sin tocar cada proyecto.

**Peticiones explícitas** (literales):
1. Un sistema de empaquetado de skills y despliegue automático que sustituya al submódulo.
2. Que el propio Adevv sea un proyecto Adevv, con su backlog, sin que el backlog llegue a los proyectos que lo usan.
3. Que la herramienta busque actualizaciones al lanzarse y se actualice si es necesario.

**Tamaño del producto.** Herramienta interna: un único usuario (el autor), en su propia máquina, con una docena de proyectos.

**Decisiones previas del usuario** (orientativas; `/platform-plan` puede afinarlas con motivo):
- Distribución preferida: paquete Python instalable como herramienta de línea de órdenes (p. ej. `uv tool install adevv` o `pipx`), con una orden `adevv`. El motor ya es Python.
- Órdenes previstas: instalar o sincronizar las skills, los agentes y los workflows donde los busca cada arnés; lanzar el orquestador y el gateway de Telegram sin rutas al submódulo; comprobar y aplicar actualizaciones.
- Actualización: solo desde versiones publicadas (nunca desde `main`); nunca con un bucle de `/orquestar` en marcha en ningún proyecto; si no hay red, sigue con la versión instalada; como mucho una comprobación al día; desactivable por configuración de usuario.
- En Windows, un ejecutable en uso no se puede sustituir: la actualización no puede reemplazar el proceso que la lanza.
- Las skills, preferiblemente instaladas en las rutas globales de cada arnés, para que una actualización no deje cambios sin commitear en los proyectos.
- Un plugin de Claude Code, como mucho, es un destino más de la sincronización, no el mecanismo principal (Codex y Antigravity no lo usan).

**No-objetivos.**
- NO-01: El script de arranque con la sesión de Windows que lanza los bots de Telegram configurados (versión posterior; se apoyará en la orden `adevv`).
- NO-02: Conversar con el arnés configurado desde Telegram con texto libre (versión posterior).
- NO-03: Distribuir Adevv a otros usuarios u organizaciones (soporte, documentación pública, registro de usuarios).
- NO-04: Rediseñar el bucle de `/orquestar` o las skills más allá de lo necesario para que funcionen instalados.

**Criterios de éxito.**
- CE-1: En una máquina sin Adevv, se instala con una sola orden y un proyecto nuevo puede lanzar `/orquestar` con Claude Code, Codex y Antigravity sin submódulo.
- CE-2: Un proyecto existente que usa el submódulo se migra siguiendo unos pasos documentados y su bucle sigue funcionando (incluidos los proyectos con adaptadores propios que citan rutas de `.agents/`).
- CE-3: Publicada una versión nueva de Adevv, la siguiente vez que se lanza la herramienta (sin bucles en marcha) queda actualizada sin intervención.
- CE-4: El backlog, los tests y la documentación interna de Adevv no aparecen en lo que se instala.
- CE-5: `/orquestar` puede ejecutarse sobre el repositorio de Adevv usando la versión instalada, sin que los cambios del árbol de trabajo afecten al bucle en curso.

**Presupuesto de complejidad.** Una sola versión (v0.1) de 3 a 5 tareas maestras. Sin olas adicionales.

## Entorno

- Sistema principal: Windows 11. Que no rompa en Linux o macOS es deseable, no obligatorio.
- Arneses en uso: Claude Code (`claude`), Codex (`codex`) y Antigravity (`agy`).
- Proyectos que hoy usan el submódulo: Adataxx, Adayy, Adoxx, Afinn y Aprexx (en `C:\Users\Iván Moreno\SW\`).
- Repositorio de Adevv: `github.com/nereodata/nereoskills` (rama `main`).
