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
