---
id: B-ADV-0009
title: "La actualización se aplaza mientras haya bucles en marcha y la recarga automática entre pasos nunca llega a activarse"
type: bug
weight: 20
dificultad: media
version: "v1.0.0"
status: planned
depende_de: []
origen: "Hotfix v0.6.1 (B-ADV-0008): publicada la 0.6.1, no se instaló porque había bucles en marcha, y el bucle de Adevv siguió con la nota de alcance vieja de la 0.6.0"
created_at: 2026-10-27
updated_at: 2026-10-27
---

# B-ADV-0009: La actualización se aplaza mientras haya bucles en marcha y la recarga automática entre pasos nunca llega a activarse

## 🎯 Descripción del Fallo

**Causa raíz**: los requisitos de instalación y actualización prohíben instalar con bucles en marcha, y el código lo cumple:
- Comprobación automática: `adevv/updater.py:583` (y `:501` con una versión ya aplazada) guarda la versión como `aplazada` y no instala si `hay_bucles_en_marcha()` devuelve algo (CE-3, F-03 fila 7).
- `adevv actualizar X.Y.Z`: `adevv/cli.py:82` rechaza la instalación con bucles en marcha (RF-F03-11, @CA-F03-13).
- Resincronización de arneses: `adevv/cli.py:118` no resincroniza destinos `DESFASADO` con bucles en marcha (RF-F01-11).

Por otro lado, los motores del bucle y del gateway ya se recargan entre pasos cuando `active.json` apunta a otra versión (`version_activa_distinta()` / `recargar_version()`, `skills/orquestar/orquestar.py:180-215`). Pero `active.json` solo cambia al instalar, y no se instala mientras haya algún bucle. Por eso la recarga solo se activaría en el caso en que no sirve: cuando no hay bucles que recargar.

**Comportamiento observado**: tras publicar el hotfix v0.6.1 (2026-10-26), `adevv actualizar` contestó «Adevv 0.6.1 disponible; se aplicará cuando no haya bucles en marcha» porque había un bucle de otro proyecto (pid 46464). El bucle de Adevv, relanzado después, siguió con la 0.6.0 y su nota de alcance errónea. En una máquina con varios proyectos siempre hay algún bucle en marcha, así que una corrección publicada no llega nunca a los bucles, aunque sea la que necesitan para avanzar.

**Comportamiento esperado**:
1. **Instalar sin esperar**: la comprobación automática y `adevv actualizar [X.Y.Z]` instalan la versión nueva aunque haya bucles en marcha. Cada versión vive en su propia carpeta `~/.adevv/versions/<V>/`, así que instalarla no toca la que usan los bucles. La conmutación de `active.json` sigue siendo atómica.
2. **Recarga entre pasos**: cada bucle y gateway en marcha detecta el cambio de `active.json` y se recarga entre pasos con el mecanismo que ya existe, sin cortar el paso en curso. El aviso de la instalación dice que los bucles en marcha la tomarán al terminar su paso actual.
3. **Arneses sin pisar un paso en curso**: la resincronización de destinos (skills y agentes copiados a los arneses) no reescribe archivos que un paso en marcha pueda estar leyendo. El diseño decide cómo, por ejemplo resincronizando en el hueco entre pasos, al recargar el bucle. Hay que justificar la opción frente a `platform_plan.md` y registrar una `DEC` si cambia el plan.
4. **Cambio de requisitos**: actualizar CE-3, RF-F03-11 y la fila 7 de F-03, RF-F01-11 y sus escenarios Gherkin (@CA-F03-13 y los de aplazamiento y resincronización) para reflejar los puntos 1 a 3. El estado `APLAZADA` desaparece o queda solo para la resincronización, según el diseño.
5. **Pruebas**: con un bucle simulado en marcha, la instalación ocurre, `active.json` cambia y el bucle se recarga en su siguiente hueco entre pasos. Ningún paso se interrumpe.

## 🔓 Alcance (decisión humana, 2026-10-27)
El usuario ha pedido expresamente este cambio de comportamiento. Modificar los requisitos CE-3, F-01 y F-03 y sus escenarios forma parte del alcance de este bug y no es una ampliación que haya que consultar. El arreglo puede tocar cualquier ruta necesaria (`adevv/`, `skills/`, `tests/`, `docs/`).

## 📋 Reproducir
1. Tener un bucle `adevv orquestar --fondo` en marcha en cualquier proyecto.
2. Publicar una versión nueva de Adevv (etiqueta `vX.Y.Z`).
3. Ejecutar `adevv actualizar`: responde que se aplicará cuando no haya bucles en marcha, y `adevv --version` y `active.json` siguen en la versión anterior.
4. El bucle sigue con su versión y nunca se recarga.

## Resolución del bloqueo de especificación · 2026-10-27

- El rechazo inicial y el intento de desarrollo se conservan en `wip/B-ADV-0009` (`cd22e3f`); su diseño y pruebas borrador no se consideran aprobados ni se restauran en este paso.
- **H1 resuelto**: los escenarios que exigen recarga parten de motores desde v0.5.0 y el rollback elige un destino compatible. El caso antiguo distingue instalación segura de reinicio manual. Las copias de F-03 coinciden.
- **H2 resuelto**: APLICADA/FALLIDA admiten bucles; fila 7 transversal sin resultado terminal ni interrupción de la precedencia. El aviso distingue copias pendientes, recarga cooperativa y reinicio manual de motores anteriores.
- **H3 resuelto**: el esquema de copias usa un origen accesible controlado cuya última publicada es 0.2.0.
- Hades `/review-spec`: **APROBADO, 9/10**, sin hallazgos pendientes. Reporte: [B-ADV-0009-spec-review.md](../../review/spec_reviews/B-ADV-0009-spec-review.md).
- Verificación documental: `adevv orquestar --verificar "git diff --check"`. Sin cambios de producción ni pruebas ejecutables; no se atribuye a este árbol la evidencia roja del WIP. Continúa `/bug-fix` con el triaje siguiente.

## Triaje
- Subfase A: Definición [EXEC]: CE-3, F-01 y F-03 y sus escenarios de instalación con bucles, recuperación de aplazamientos antiguos y resincronización.
- Subfase B: Diseño [EXEC]: separar instalación versionada de copias globales; conservar directorios existentes e integrar la recarga ya disponible.
- Subfase C1: Pruebas [EXEC]: adaptar contratos autorizados y cubrir instalación real con bucle, puntero, destino intacto, reutilización de versión y recarga.
- Subfase C2: Corrección [EXEC]: updater, CLI y guarda común del sincronizador; sin reimplementar la recarga.
- Subfase D: QA [EXEC]: Hades sobre el delta completo.
- Subfase E: Documentación [EXEC]: README, requisitos, DEC del plan de plataforma y revisión de versión.
- Subfase F: Cierre [EXEC]: cierre y commit en release/v1.0.
- Verificación al cierre: `python -m unittest discover -s tests -p test_updater.py`, `python -m unittest discover -s tests -p test_sync.py`, `python -m unittest discover -s tests -p test_cli_commands.py`, `python -m unittest discover -s tests -p test_install_and_release.py`, `python -m unittest discover -s skills/orquestar -p test_recarga.py`, `python -m unittest discover -s skills/telegram_gateway -p test_recarga_gateway.py`; ejercitan instalación, sincronización y transferencia cooperativa sin ejecutar el resto de la suite. Estático: `git diff --check` y compilación de los módulos modificados; sin linter/tipado configurados ni cambios de dependencias.
- DEC-B09: se conserva `aplazada` solo como entrada heredada que se consume sin esperar bucles; no se producen nuevos aplazamientos de instalación. Las copias globales esperan a la primera orden sin bucles. Los mandatos del motor usan rutas absolutas al almacén activo; ninguna carpeta instalada se sobrescribe.
- Autorización: el apartado «Alcance (decisión humana)» permite sustituir los contratos anteriores y sus escenarios contradictorios; no se requiere nueva consulta.
