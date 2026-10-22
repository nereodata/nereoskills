"""Diagnóstico de sólo lectura para la migración de proyectos con submódulo a Adevv."""

import os
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Set, TextIO, Tuple

from adevv.store import get_active_version_dir


class Pendiente(NamedTuple):
    """Representa un elemento pendiente de migración."""
    ruta: str
    linea: Optional[int] = None
    texto: Optional[str] = None
    descripcion: Optional[str] = None


class ResultadoDiagnostico(NamedTuple):
    """Resultado estructurado del diagnóstico de migración."""
    pendientes: List[Pendiente]
    citas_historicas: int
    es_repositorio_fuente: bool


def info_enlace(path: Path) -> Tuple[bool, str, str]:
    """Determina si una ruta es enlace o junction y retorna (es_enlace, destino, tipo)."""
    try:
        if hasattr(os.path, "isjunction") and os.path.isjunction(path):
            target = os.readlink(str(path))
            if target.startswith("\\\\?\\"):
                target = target[4:]
            return True, target, "junction"
        if os.path.islink(path) or path.is_symlink():
            target = os.readlink(str(path))
            if target.startswith("\\\\?\\"):
                target = target[4:]
            return True, target, "enlace"
    except (OSError, ValueError):
        pass
    return False, "", ""


def es_repositorio_fuente_adevv(root: Path) -> bool:
    """Comprueba si el directorio raíz corresponde al repositorio de desarrollo de Adevv."""
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            txt = pyproject.read_text(encoding="utf-8")
            if 'name = "adevv"' in txt and (root / "adevv").is_dir():
                return True
        except OSError:
            pass
    return False


def _obtener_nombres_distribuidos(root: Path) -> Set[str]:
    """Obtiene los nombres canónicos de skills, agentes y workflows de la versión activa instalada."""
    version_dir = get_active_version_dir()
    if not version_dir.exists() and es_repositorio_fuente_adevv(root):
        version_dir = root

    nombres = set()
    skills_dist = version_dir / "skills"
    if skills_dist.is_dir():
        for d in skills_dist.iterdir():
            if d.is_dir() and not d.name.startswith("."):
                nombres.add(d.name)

    agents_dist = version_dir / "agents"
    if agents_dist.is_dir():
        for f in agents_dist.iterdir():
            if f.is_file() and f.suffix in (".md", ".toml"):
                nombres.add(f.stem)
        codex_dir = agents_dist / "codex"
        if codex_dir.is_dir():
            for f in codex_dir.iterdir():
                if f.is_file() and f.suffix == ".toml":
                    nombres.add(f.stem)

    wf_dist = version_dir / "workflows"
    if wf_dist.is_dir():
        for f in wf_dist.iterdir():
            if f.is_file() and f.suffix == ".md":
                nombres.add(f.stem)

    return nombres


def _buscar_copias_adevv(root: Path) -> Set[Path]:
    """Localiza carpetas del proyecto distintas de la raíz que contengan copias de Adevv."""
    copias = set()
    carpetas_omitidas = {".git", ".agents"}

    for dirpath, dirnames, filenames in os.walk(root):
        p_dir = Path(dirpath)
        if p_dir == root:
            dirnames[:] = [d for d in dirnames if d not in carpetas_omitidas and not info_enlace(root / d)[0]]
            continue

        es_link, _, _ = info_enlace(p_dir)
        if es_link:
            dirnames[:] = []
            continue

        if (p_dir / "skills" / "orquestar" / "SKILL.md").is_file():
            copias.add(p_dir.resolve())
            dirnames[:] = []
            continue

        dirnames[:] = [d for d in dirnames if d not in carpetas_omitidas and not info_enlace(p_dir / d)[0]]

    return copias


def diagnosticar_migracion(root: Path) -> ResultadoDiagnostico:
    """Diagnostica la raíz de un proyecto sin modificar archivos y recopila pendientes."""
    pendientes: List[Pendiente] = []
    rutas_pendientes: Set[str] = set()
    citas_historicas = 0

    es_fuente = es_repositorio_fuente_adevv(root)

    def agregar_pendiente(p: Pendiente) -> None:
        clave = (p.ruta, p.linea)
        if clave not in rutas_pendientes:
            rutas_pendientes.add(clave)
            pendientes.append(p)

    gitmodules = root / ".gitmodules"
    if gitmodules.is_file():
        try:
            txt_gm = gitmodules.read_text(encoding="utf-8", errors="ignore")
            if ".agents" in txt_gm:
                agregar_pendiente(Pendiente(ruta=".gitmodules"))
        except OSError:
            pass

    agents_path = root / ".agents"
    es_link_agents, dest_agents, tipo_agents = info_enlace(agents_path)
    if es_link_agents:
        norm_dest = dest_agents if (":" in dest_agents or dest_agents.startswith("\\\\")) else dest_agents.replace("\\", "/")
        agregar_pendiente(Pendiente(ruta=".agents", descripcion=f".agents → {norm_dest} ({tipo_agents})"))
    elif agents_path.exists():
        agregar_pendiente(Pendiente(ruta=".agents"))

    git_modules_agents = root / ".git" / "modules" / ".agents"
    if git_modules_agents.exists():
        agregar_pendiente(Pendiente(ruta=".git/modules/.agents"))

    carpetas_adaptadores = [".claude", ".codex", ".agent"]
    for cap in carpetas_adaptadores:
        cap_dir = root / cap
        if not cap_dir.is_dir():
            continue
        for dp, dirnames, filenames in os.walk(cap_dir):
            curr_dir = Path(dp)
            es_link_curr, dest_curr, tipo_curr = info_enlace(curr_dir)
            if es_link_curr:
                norm_dest = dest_curr.replace("\\", "/")
                if ".agents" in norm_dest:
                    rel_p = curr_dir.relative_to(root).as_posix()
                    norm_disp = dest_curr if (":" in dest_curr or dest_curr.startswith("\\\\")) else norm_dest
                    agregar_pendiente(Pendiente(ruta=rel_p, descripcion=f"{rel_p} → {norm_disp} ({tipo_curr})"))
                dirnames[:] = []
                continue

            for f_name in filenames:
                f_path = curr_dir / f_name
                es_link_f, dest_f, tipo_f = info_enlace(f_path)
                if es_link_f:
                    norm_dest_f = dest_f.replace("\\", "/")
                    if ".agents" in norm_dest_f:
                        rel_f = f_path.relative_to(root).as_posix()
                        norm_disp_f = dest_f if (":" in dest_f or dest_f.startswith("\\\\")) else norm_dest_f
                        agregar_pendiente(Pendiente(ruta=rel_f, descripcion=f"{rel_f} → {norm_disp_f} ({tipo_f})"))

            subdirs_validos = []
            for d in dirnames:
                sub_p = curr_dir / d
                es_link_sub, dest_sub, tipo_sub = info_enlace(sub_p)
                if es_link_sub:
                    norm_dest_sub = dest_sub.replace("\\", "/")
                    if ".agents" in norm_dest_sub:
                        rel_sub = sub_p.relative_to(root).as_posix()
                        norm_disp_sub = dest_sub if (":" in dest_sub or dest_sub.startswith("\\\\")) else norm_dest_sub
                        agregar_pendiente(Pendiente(ruta=rel_sub, descripcion=f"{rel_sub} → {norm_disp_sub} ({tipo_sub})"))
                else:
                    subdirs_validos.append(d)
            dirnames[:] = subdirs_validos

    orch_file = root / "orchestration.json"
    if orch_file.is_file():
        try:
            txt_orch = orch_file.read_text(encoding="utf-8", errors="ignore")
            if ".agents/" in txt_orch:
                agregar_pendiente(Pendiente(ruta="orchestration.json"))
        except OSError:
            pass

    nombres_dist = _obtener_nombres_distribuidos(root)
    candidatos_ocultamiento = [
        (root / ".claude" / "skills", True),
        (root / ".claude" / "agents", False),
        (root / ".codex" / "skills", True),
        (root / ".codex" / "agents", False),
        (root / ".agent" / "skills", True),
        (root / ".agent" / "workflows", False),
    ]
    for c_dir, es_dir in candidatos_ocultamiento:
        if c_dir.exists() and not info_enlace(c_dir)[0]:
            try:
                for item in c_dir.iterdir():
                    nombre = item.name if es_dir else item.stem
                    if nombre in nombres_dist:
                        rel_item = item.relative_to(root).as_posix()
                        es_link_it, dest_it, tipo_it = info_enlace(item)
                        if es_link_it:
                            norm_dest_it = dest_it if (":" in dest_it or dest_it.startswith("\\\\")) else dest_it.replace("\\", "/")
                            agregar_pendiente(Pendiente(ruta=rel_item, descripcion=f"{rel_item} → {norm_dest_it} ({tipo_it})"))
                        else:
                            agregar_pendiente(Pendiente(ruta=rel_item))
            except OSError:
                pass

    copias_adevv = _buscar_copias_adevv(root)
    for c_path in sorted(copias_adevv):
        rel_copia = c_path.relative_to(root.resolve()).as_posix()
        agregar_pendiente(Pendiente(ruta=rel_copia))

    archivos_raiz_en_uso = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", "task_config.yaml"}
    if not es_fuente:
        archivos_raiz_en_uso.add("README.md")

    carpetas_en_uso = {"scripts", ".claude", ".codex", ".agent", ".github"}

    for dirpath, dirnames, filenames in os.walk(root):
        p_dir = Path(dirpath)
        if p_dir.resolve() in copias_adevv or p_dir.name in (".git", ".agents"):
            dirnames[:] = []
            continue

        if info_enlace(p_dir)[0]:
            dirnames[:] = []
            continue

        dirnames[:] = [
            d for d in dirnames
            if d not in (".git", ".agents")
            and (p_dir / d).resolve() not in copias_adevv
            and not info_enlace(p_dir / d)[0]
        ]

        rel_dir = p_dir.relative_to(root).as_posix()
        primera_carpeta = rel_dir.split("/")[0] if rel_dir != "." else ""

        for f_name in filenames:
            f_path = p_dir / f_name
            if info_enlace(f_path)[0]:
                continue

            rel_f = f_path.relative_to(root).as_posix()

            if es_fuente and rel_f == "README.md":
                continue

            if rel_f == "orchestration.json":
                continue

            es_en_uso = False
            if rel_dir == ".":
                if f_name in archivos_raiz_en_uso:
                    es_en_uso = True
            elif primera_carpeta in carpetas_en_uso:
                es_en_uso = True

            try:
                lineas = f_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue

            if es_en_uso:
                for idx, line in enumerate(lineas, 1):
                    if ".agents/" in line:
                        agregar_pendiente(Pendiente(ruta=rel_f, linea=idx, texto=line.strip()))
            else:
                for line in lineas:
                    if ".agents/" in line:
                        citas_historicas += 1

    return ResultadoDiagnostico(
        pendientes=pendientes,
        citas_historicas=citas_historicas,
        es_repositorio_fuente=es_fuente,
    )


def formatear_diagnostico(resultado: ResultadoDiagnostico) -> str:
    """Formatea la salida del diagnóstico agrupada por archivo y acotada a 20 pendientes."""
    pendientes = resultado.pendientes
    total = len(pendientes)
    citas_historicas = resultado.citas_historicas

    lineas_salida: List[str] = []
    mostrados = 0

    agrupados: Dict[str, List[Pendiente]] = {}
    for p in pendientes:
        agrupados.setdefault(p.ruta, []).append(p)

    for ruta in sorted(agrupados.keys()):
        if mostrados >= 20:
            break
        items = agrupados[ruta]
        sin_linea = [it for it in items if it.linea is None]
        con_linea = [it for it in items if it.linea is not None]

        for it in sin_linea:
            if mostrados >= 20:
                break
            lineas_salida.append(it.descripcion or it.ruta)
            mostrados += 1

        if con_linea and mostrados < 20:
            lineas_salida.append(f"{ruta}:")
            for it in con_linea:
                if mostrados >= 20:
                    break
                lineas_salida.append(f"  línea {it.linea}: {it.texto}")
                mostrados += 1

    if total > 20:
        lineas_salida.append(f"… y {total - 20} más (total {total}).")

    if total == 0:
        if citas_historicas > 0:
            lineas_salida.append(f"Sin pendientes ({citas_historicas} citas históricas).")
        else:
            lineas_salida.append("Sin pendientes")
    else:
        lineas_salida.append(f"{total} pendientes.")

    return "\n".join(lineas_salida)


def ejecutar_migrar(root: Path, out: TextIO, err: TextIO) -> int:
    """Ejecuta el comando adevv migrar escribiendo en out y err."""
    res = diagnosticar_migracion(root)
    texto = formatear_diagnostico(res)
    print(texto, file=out)
    return 0
