"""Punto de entrada de línea de comandos para adevv."""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

from adevv import __version__
from adevv.processes import formatear_proceso_ui, hay_bucles_en_marcha
from adevv.release_tools import obtener_versiones_publicadas
from adevv.store import (
    get_active_info,
    get_active_version_dir,
    get_adevv_home,
    get_config,
    get_sync_registry,
    get_update_state,
    set_active_info,
    set_update_state,
)
from adevv.sync import (
    DESTINOS,
    EstadoDestino,
    planificar_sincronizacion,
    sincronizar_destinos,
)


def _version_es_mayor(v1: str, v2: str) -> bool:
    """Compara si la versión v1 es estrictamente mayor que v2 numéricamente."""
    try:
        p1 = [int(x) for x in v1.split(".")]
        p2 = [int(x) for x in v2.split(".")]
        return p1 > p2
    except ValueError:
        return v1 > v2


def _comprobar_actualizacion_en_instalacion(err: TextIO) -> None:
    """Comprueba si hay una versión publicada superior y la instala lado a lado."""
    config = get_config()
    if not config.get("auto_update", True):
        return

    if hay_bucles_en_marcha():
        return

    origin_url = os.environ.get("ADEVV_ORIGIN_URL")
    if not origin_url:
        return

    try:
        versiones = obtener_versiones_publicadas(origin_url)
    except Exception:
        return

    if not versiones:
        return

    act = get_active_info()
    version_actual = act.get("version", __version__) if act else __version__

    versiones_ordenadas = sorted(versiones, key=lambda v: [int(x) for x in v.split(".") if x.isdigit()])
    mayor_publicada = versiones_ordenadas[-1]

    if _version_es_mayor(mayor_publicada, version_actual):
        adevv_home = get_adevv_home()
        nueva_version_dir = adevv_home / "versions" / mayor_publicada
        nueva_version_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Extraer archivos del commit de la etiqueta vX.Y.Z
            tag_name = f"v{mayor_publicada}"
            tar_proc = subprocess.run(
                ["git", "archive", "--format=tar", tag_name],
                cwd=origin_url if Path(origin_url).is_dir() else None,
                capture_output=True,
                check=True,
            )
            import io
            import tarfile

            with tarfile.open(fileobj=io.BytesIO(tar_proc.stdout), mode="r:") as tar:
                if hasattr(tarfile, "data_filter"):
                    tar.extractall(path=nueva_version_dir, filter="data")
                else:
                    tar.extractall(path=nueva_version_dir)

            set_active_info({
                "version": mayor_publicada,
                "id": mayor_publicada,
                "origen": "publicada",
            })
        except Exception:
            pass


def _resincronizar_desfasados_al_arrancar(out: TextIO, err: TextIO) -> None:
    """Resincroniza destinos desfasados si no hay bucles en marcha, o avisa en 24h."""
    if os.environ.get("ORQUESTAR_PASO"):
        return

    act = get_active_info()
    version_activa = act.get("version", __version__) if act else __version__
    origen_dir = get_active_version_dir()

    bucles_vivos = hay_bucles_en_marcha()

    desfasados = []
    for target_key in DESTINOS.keys():
        plan = planificar_sincronizacion(target_key, origen_dir, version_activa)
        if plan["estado"] == EstadoDestino.DESFASADO:
            registro = get_sync_registry(target_key)
            v_reg = (registro.get("version") if registro else None) or "anterior"
            desfasados.append((target_key, plan["nombre"], v_reg))

    if not desfasados:
        return

    if bucles_vivos:
        lista_bucles = ", ".join(formatear_proceso_ui(b) for b in bucles_vivos)
        for _, nombre, v_reg in desfasados:
            msg = f"{nombre} sigue con la {v_reg}; se sincronizará cuando no haya bucles en marcha: {lista_bucles}."
            print(msg, file=err)
    else:
        sincronizar_destinos(origen_dir=origen_dir, version=version_activa)
        for _, nombre, _ in desfasados:
            msg = f"{nombre} sincronizado con la {version_activa}."
            print(msg, file=out)


def _describir_escritos_destino(destino_key: str, origen_dir: Path) -> str:
    """Genera la descripción del contenido escrito en un destino (ej. 24 skills, 5 agentes)."""
    skills_dir = origen_dir / "skills"
    agents_dir = origen_dir / "agents"
    workflows_dir = origen_dir / "workflows"

    num_skills = 0
    if skills_dir.exists() and skills_dir.is_dir():
        num_skills = sum(1 for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith("."))

    if destino_key in ("claude", "codex"):
        num_agentes = 0
        if destino_key == "claude" and agents_dir.exists():
            num_agentes = sum(1 for f in agents_dir.iterdir() if f.is_file() and f.suffix == ".md")
        elif destino_key == "codex" and (agents_dir / "codex").exists():
            num_agentes = sum(1 for f in (agents_dir / "codex").iterdir() if f.is_file() and f.suffix == ".toml")

        partes = []
        if num_skills > 0:
            partes.append(f"{num_skills} skills")
        if num_agentes > 0:
            partes.append(f"{num_agentes} agentes")
        return ", ".join(partes) or "sin contenido"

    elif destino_key == "agy":
        num_wf = 0
        if workflows_dir.exists():
            num_wf = sum(1 for f in workflows_dir.iterdir() if f.is_file() and f.suffix == ".md")

        partes = []
        if num_skills > 0:
            partes.append(f"{num_skills} skills")
        if num_wf > 0:
            partes.append(f"{num_wf} workflows")
        return ", ".join(partes) or "sin contenido"

    return "sincronizado"


def comando_instalar(forzar: bool, out: TextIO, err: TextIO) -> int:
    """Ejecuta la orden adevv instalar [--forzar]."""
    _comprobar_actualizacion_en_instalacion(err)

    act = get_active_info()
    version = act.get("version", __version__) if act else __version__
    origen_dir = get_active_version_dir()

    resultados = sincronizar_destinos(origen_dir=origen_dir, version=version, forzar=forzar)

    for destino_key, res in resultados.items():
        nombre = res["nombre"]
        estado = res["estado"]
        detalle = res.get("detalle")
        sin_cambios = res.get("sin_cambios", False)
        conflictos = res.get("conflictos", [])

        if estado == EstadoDestino.NO_DETECTADO:
            print(f"{nombre}: {detalle or 'no detectado'}", file=out)
        elif estado == EstadoDestino.DESACTIVADO:
            print(f"{nombre}: desactivado", file=out)
        elif sin_cambios:
            print(f"{nombre}: sin cambios", file=out)
        elif estado == EstadoDestino.INCOMPLETO:
            desc = _describir_escritos_destino(destino_key, origen_dir)
            print(f"{nombre}: {desc} ({len(conflictos)} conflictos)", file=out)
            for c in conflictos[:20]:
                print(f"  conflicto: {c}", file=out)
            if len(conflictos) > 20:
                print(f"  ... y {len(conflictos) - 20} más (total {len(conflictos)})", file=out)
        else:
            desc = _describir_escritos_destino(destino_key, origen_dir)
            print(f"{nombre}: {desc}", file=out)

    return 0


def comando_version(out: TextIO) -> int:
    """Muestra la versión de Adevv, estado de cada arnés y metadatos de actualización."""
    act = get_active_info()
    version = act.get("version", __version__) if act else __version__
    origen = act.get("origen", "publicada") if act else "publicada"

    if origen == "desarrollo":
        print(f"Adevv {version} (desarrollo)", file=out)
    else:
        print(f"Adevv {version}", file=out)

    for target_key in DESTINOS.keys():
        cfg = DESTINOS[target_key]
        nombre = cfg.get("nombre", target_key)
        plan = planificar_sincronizacion(target_key, get_active_version_dir(), version)
        estado = plan["estado"]
        detalle = plan.get("detalle")
        conflictos = plan.get("conflictos", [])

        registro = get_sync_registry(target_key)
        version_reg = (registro.get("version") if registro else None) or version

        if estado == EstadoDestino.NO_DETECTADO:
            print(f"{nombre}: {detalle or 'no detectado'}", file=out)
        elif estado == EstadoDestino.DESACTIVADO:
            print(f"{nombre}: desactivado", file=out)
        elif estado == EstadoDestino.DESFASADO:
            print(f"{nombre} {version_reg} (pendiente de sincronizar)", file=out)
        elif estado == EstadoDestino.INCOMPLETO:
            print(f"{nombre} {version_reg} ({len(conflictos)} conflictos)", file=out)
        else:
            print(f"{nombre} {version_reg}", file=out)

    config = get_config()
    auto_update = "sí" if config.get("auto_update", True) else "no"
    print(f"actualización automática: {auto_update}", file=out)

    update_state = get_update_state()
    last_check_at = update_state.get("last_checked_at")
    last_check_status = update_state.get("last_checked_status")
    if last_check_at and last_check_status:
        print(f"última comprobación: {last_check_at} ({last_check_status})", file=out)

    last_applied_at = update_state.get("last_applied_at")
    last_applied_ver = update_state.get("last_applied_version")
    if last_applied_at and last_applied_ver:
        print(f"actualizado a {last_applied_ver} {last_applied_at}", file=out)

    return 0


def main_cli(args: Optional[List[str]] = None, out: Optional[TextIO] = None, err: Optional[TextIO] = None) -> int:
    """Punto de entrada de adevv."""
    out_stream = out if out is not None else sys.stdout
    err_stream = err if err is not None else sys.stderr

    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(prog="adevv", description="Adevv: herramientas globales para agentes de IA")
    parser.add_argument("-v", "--version", action="store_true", help="muestra la versión y el estado de los arneses")

    subparsers = parser.add_subparsers(dest="subcommand")
    instalar_parser = subparsers.add_parser("instalar", help="sincroniza las carpetas de los arneses")
    instalar_parser.add_argument("--forzar", action="store_true", help="sobrescribe archivos del registro editados a mano")

    parsed, remaining = parser.parse_known_args(args)

    _resincronizar_desfasados_al_arrancar(out_stream, err_stream)

    if parsed.version:
        return comando_version(out_stream)

    if parsed.subcommand == "instalar":
        return comando_instalar(parsed.forzar, out_stream, err_stream)

    if not parsed.subcommand:
        return comando_version(out_stream)

    return 0


def main() -> None:
    sys.exit(main_cli(sys.argv[1:]))


if __name__ == "__main__":
    main()
