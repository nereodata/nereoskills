---
name: release
description: Gestión de lanzamientos y etiquetado de versiones (Release Management)
---

# Skill: Gestión de Lanzamientos (/release)

Esta skill formaliza el cierre de una versión del proyecto: valida pre-flight, genera/verifica CHANGELOG, hace bump y merge (`--no-ff`) a `main`, etiqueta sobre `main`, y verifica el post-tag (CI, release publicado, deploys).

La skill es **agnóstica del proyecto consumidor**. Toda la configuración específica vive en `task_config.yaml` del consumidor: manifiestos a verificar, comandos pre-flight, checks de salud cloud, flags de code signing, etc. Si el consumidor no declara estas secciones, la skill avisa al usuario y aplica el subset clásico.

## Pasos de la Skill

### 1. Validación Pre-Release

#### 1.1 Rama y versión
- **Validar rama activa**:
  - Bloque funcional: la rama debe seguir `release/vX.Y`.
  - Hotfix: la rama debe seguir `hotfix/vX.Y.Z`.
  - Si la rama es `main` o cualquier otra, **abortar** e informar al usuario.
- Verificar coherencia: el número de versión de la rama debe coincidir con `task_config.yaml::project.version`.
- Verificar que no hay cambios pendientes (staged ni unstaged).

#### 1.2 Completitud del backlog
- Determinar la versión objetivo desde `task_config.yaml` o desde la rama de trabajo.
- Ejecutar:
  ```
  python .agents/skills/release/scripts/check_release_completeness.py --version vX.Y.Z
  ```
- Si el script devuelve exit 1, **abortar** e informar al usuario de las tareas/bugs abiertas.
- Si el script reporta `WARN: 0 ficheros verificados`, advertir al usuario que los paths de `task_config.yaml::levels` probablemente no apuntan al backlog real (no abortar pero alertar).

#### 1.3 Validación de manifiestos
- Ejecutar:
  ```
  python .agents/skills/release/scripts/check_manifests_versions.py
  ```
- Si falla, abortar y pedir al usuario que ejecute `/start-version` para sincronizar (o que ajuste manualmente y reintente).
- Si la sección `release.manifests` no está declarada en `task_config.yaml`, advertir al usuario que esta versión de la skill espera la lista declarada y continuar con el subset clásico (lectura por convención).

#### 1.4 RELEASING.md
- Confirmar que `RELEASING.md` existe en la raíz del proyecto consumidor.
- Si no existe, ofrecer crearlo desde la plantilla `.agents/skills/release/templates/RELEASING.md` (rellenando placeholders desde `task_config.yaml::release.manifests` cuando esté disponible).
- No abortar si el usuario rechaza crearlo.

#### 1.5 CHANGELOG
- Confirmar que `CHANGELOG.md` está actualizado con la sección `[X.Y.Z]`.
- Si la sección no existe, ofrecer ejecutar:
  ```
  python .agents/skills/release/scripts/generate_changelog_section.py --version vX.Y.Z
  ```
  e indicar al usuario que pegue la salida en `CHANGELOG.md`, añada el resumen ejecutivo (Highlights) a mano y vuelva a invocar `/release`.
- La skill **no** modifica `CHANGELOG.md` automáticamente.

#### 1.6 Lint de workflows GitHub Actions
- Si el proyecto tiene `.github/workflows/`, ejecutar:
  ```
  actionlint .github/workflows/*.yml
  ```
- Si falla, abortar y reportar el error textual al usuario (`actionlint` suele incluir línea/columna).
- Si `actionlint` no está instalado, ofrecer al usuario el comando de instalación apropiado para su SO (binario único de https://github.com/rhysd/actionlint) y abortar.

#### 1.7 Pre-flight declarativo
- Si `task_config.yaml::release.preflight` está definido, ejecutar cada `cmd` en orden, abortando al primer exit code != 0 y reportando el comando + últimas líneas de salida.
- Si la sección no existe, ejecutar el subset clásico (lint + tests + build) usando `/review-test` y `/review-code` globales si procede, y advertir al usuario que conviene declarar `preflight` para reproducir CI localmente.

> El propósito del pre-flight es **ejercer en local el mismo path que el CI**. En proyectos con empaquetado complejo (instaladores Electron, bundles Python frozen, imágenes Docker), `build` simple no detecta errores de iconos / extraResources / firmas; el pre-flight debe incluir el comando de empaquetado completo (con flag tipo `--dir` para electron-builder o equivalente).

#### 1.8 Code signing (si aplica)
- Si `task_config.yaml::release.code_signing.enabled = true`:
  - Verificar con el usuario que todos los secretos en `secrets_required` están configurados en GitHub Actions del repo (la skill no tiene acceso al panel).
  - El workflow de CI debe contener un step de firma. Si no existe, abortar e instruir al usuario que añada el step antes de continuar.
  - Anotar el `verify_cmd` declarado o inferido del provider para usarlo en post-tag.

### 2. Identificación de la Versión
- Leer `task_config.yaml::project.version`.
- La versión está determinada por la rama:
  - `release/vX.Y` → release `vX.Y.0`
  - `hotfix/vX.Y.Z` → release `vX.Y.Z`
- Confirmar con el usuario que la versión es correcta antes de continuar.

### 3. Ejecución del Bump

En la rama `release/vX.Y` (o `hotfix/vX.Y.Z`):

1. Verificar que los manifiestos declarados ya tienen la versión correcta (paso 1.3 ya lo cubrió). Si no, abortar.
2. Crear el commit `chore(release): vX.Y.Z` con los entregables del release (CHANGELOG, RELEASING actualizados si procede, items de backlog cerrados).
3. Sincronizar (cerrar) la tarea de release `T-[PRJ]-REL-XXXX` en el backlog si existe.
4. **No crear el tag aún** — el tag se crea sobre `main` tras el squash (paso 4).

### 4. Merge y Etiquetado

> **Acción visible externamente.** Pedir confirmación explícita al usuario antes de ejecutar — modifica `main` y empuja al remoto.

#### 4.a Bloque funcional (merge --no-ff)

```
git checkout main
git pull --ff-only
git merge --no-ff release/vX.Y -m "chore(release): vX.Y.Z"
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main --follow-tags
```

El tag se crea sobre el merge commit canónico de `main`. Todos los commits individuales de `release/vX.Y` quedan **alcanzables desde `main`** a través del merge commit, preservando el histórico granular de forma permanente.

> **Por qué `--no-ff` y no `--squash`**: el squash aplasta todos los commits en uno y destruye el histórico detallado cuando se borra la rama. Con `--no-ff`, aunque se borre la rama, los commits no son *unreachable* y `git gc` nunca los elimina.

Tras el push, eliminar la rama de release: `git branch -d release/vX.Y` (y opcionalmente `git push origin --delete release/vX.Y`). **Los commits no se pierden** porque son alcanzables desde `main`.

#### 4.b Hotfix (merge commit)

```
git checkout main
git pull --ff-only
git merge --no-ff hotfix/vX.Y.Z
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin main --follow-tags
```

Tras el merge a `main`, si existe una rama `release/vA.B` activa, hacer también:
```
git checkout release/vA.B
git merge hotfix/vX.Y.Z
git push
```
para que el parche viaje al próximo bloque funcional.

### 5. Post-Tag Verification

Tras el `git push --follow-tags`, esperar y verificar:

1. **CI/CD del release** — vigilar GitHub Actions:
   ```
   gh run watch
   ```
   Todos los jobs del workflow de release deben pasar antes de continuar. Si `gh` no está disponible, instruir al usuario a abrir la URL de Actions del repo.
2. **GitHub Release publicado**:
   ```
   gh release view vX.Y.Z
   ```
   Si `task_config.yaml::release.expected_assets` declara la lista esperada, validar que los assets publicados coinciden.
3. **Deploys cloud** — para cada entrada en `task_config.yaml::release.deploy_health_checks`, ejecutar el health check correspondiente y validar la versión devuelta.
4. **Code signing (si aplica)** — ejecutar `verify_cmd` (o el comando inferido del provider, p.ej. `signtool verify /pa /v <exe>` en Windows + Trusted Signing, `codesign --verify --deep --strict <app>` en macOS).
5. **Smoke test del entregable** — instrucción al humano: "Descarga el artefacto principal e intenta el flujo principal del producto". La skill no automatiza esto; sólo recuerda hacerlo.

Si cualquiera de estos pasos falla, **el release no se considera completado**. Ofrecer al humano el procedimiento de rescate (paso 6).

### 6. Rescate del tag (CI falla por errata pequeña antes de cualquier distribución)

Si el CI dispara y falla al instante por una errata reparable (fichero faltante, sintaxis YAML), **y nadie ha descargado el artefacto** (verificable con `gh release view vX.Y.Z` mostrando 0 download counts):

1. Crear rama `hotfix/vX.Y.Z-ci-fix` desde `main` (no desde el tag, para no inflar la versión):
   ```
   git checkout -b hotfix/vX.Y.Z-ci-fix main
   ```
2. Aplicar el fix mínimo y commitear.
3. Fast-forward merge a `main`.
4. Mover el tag:
   ```
   git tag -fa vX.Y.Z -m "Release vX.Y.Z"
   ```
5. Push de `main` (commit normal):
   ```
   git push origin main
   ```
6. Push del tag con `--force` (sólo el tag se mueve; nada upstream se reescribe):
   ```
   git push origin vX.Y.Z --force
   ```
7. Borrar la rama hotfix.

> Esto es preferible a crear un `vX.Y.(Z+1)` simbólico **porque la versión no llegó a existir como release distribuido**. Si **alguien ya descargó** el artefacto roto, no se mueve el tag: se hace un `vX.Y.(Z+1)` canónico.

### 7. Notificación

- Extraer la sección `[X.Y.Z]` de `CHANGELOG.md` (incluyendo Highlights).
- Si el proyecto usa GitHub Releases con `generate_release_notes: true`, **complementar** las notas auto-generadas pegando el contenido del CHANGELOG en el cuerpo del Release tras la publicación:
  ```
  gh release edit vX.Y.Z --notes-file <(seccion-extraida)
  ```
- Formatear la sección para los canales de comunicación correspondientes (Slack, email, etc. — la skill no envía mensajes, sólo prepara el texto).

---

## Esquema esperado en `task_config.yaml`

La skill consulta las siguientes secciones (todas opcionales — la skill avisa si faltan):

```yaml
project:
  prefix: ABC
  name: Foo
  version: "v0.3.0"

# Opcional: prefijos de tipo de tarea (default: T para feature, B para bug)
task_types:
  feature: T
  bug: B

release:
  # Manifiestos a verificar/bumpear
  manifests:
    - path: package.json
      type: json
      key: version
    - path: services/api/pyproject.toml
      type: toml
      key: project.version
    - path: task_config.yaml
      type: yaml
      key: project.version

  # Comandos pre-flight (orden importa, primero falla aborta)
  preflight:
    - description: "Lint workflows"
      cmd: "actionlint .github/workflows/*.yml"
    - description: "Lint code"
      cmd: "ruff check . && cd app && npm run lint"
    - description: "Type check"
      cmd: "pyright && cd app && npm run typecheck"
    - description: "Tests"
      cmd: "python scripts/run_tests.py"
    - description: "Full build (mirror of CI)"
      cmd: "cd app && npm run dist:hybrid -- --dir"

  # Lista esperada de assets en GitHub Release
  expected_assets:
    - "Foo-Setup-{version}.exe"
    - "Foo-{version}.dmg"

  # Health checks post-deploy
  deploy_health_checks:
    - name: "API prod"
      url: "https://api.example.com/health"
      expect_version_at: "$.version"

  # Code signing
  code_signing:
    enabled: false
    provider: azure_trusted_signing
    secrets_required:
      - AZURE_TENANT_ID
      - AZURE_CLIENT_ID
      - AZURE_CLIENT_SECRET
      - AZURE_TRUSTED_SIGNING_ACCOUNT_NAME
      - AZURE_TRUSTED_SIGNING_CERT_PROFILE
    verify_cmd: "signtool verify /pa /v dist/Foo-Setup-{version}.exe"
```
