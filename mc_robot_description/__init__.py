"""Single source of truth for the MC robot URDF.

Every consumer — ROS nodes, the Isaac simulation, offline tools — must obtain
the model through this package instead of keeping its own copy.

Works in two situations:
- installed as an ament package (resolved via ament_index);
- imported straight from a repo checkout (resolved relative to this file),
  which is how non-ROS consumers (e.g. mc_simulation) use it.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

_PACKAGE = "mc_robot_description"
_URI_RE = re.compile(r"package://mc_robot_description/")


def get_description_path() -> Path:
    """Root directory that contains urdf/ and meshes/."""
    try:
        from ament_index_python.packages import get_package_share_directory

        return Path(get_package_share_directory(_PACKAGE))
    except Exception:
        # Repo checkout: this file lives at <repo>/mc_robot_description/__init__.py
        return Path(__file__).resolve().parent.parent


def get_urdf_path() -> Path:
    """Canonical URDF (mesh URIs use package:// — needs ROS-aware loaders)."""
    return get_description_path() / "urdf" / "mc1.urdf"


def export_resolved_urdf(dst: str | os.PathLike | None = None) -> Path:
    """Write a URDF variant with package:// mesh URIs rewritten to absolute
    filesystem paths, for loaders without package resolution (Isaac Lab's
    UrdfConverter, Pinocchio without ROS, ...). Returns the written path.

    If dst is None a stable per-user temp file is used and rewritten on each
    call, so repeated callers pick up model updates.
    """
    root = get_description_path()
    text = get_urdf_path().read_text()
    text = _URI_RE.sub(f"{root.as_posix()}/", text)
    if dst is None:
        dst = Path(tempfile.gettempdir()) / f"mc1_resolved_{os.getuid()}.urdf"
    dst = Path(dst)
    dst.write_text(text)
    return dst
