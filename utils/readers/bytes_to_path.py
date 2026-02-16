# utils/io/bytes_to_path.py
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, TypeVar, Union
import re

T = TypeVar("T")


def _sanitize_filename(name: str, default: str = "source.bin") -> str:
    """
    Make a filename safe for filesystem usage while keeping extension if present.
    """
    name = (name or "").strip()
    if not name:
        return default

    # Remove path parts if user provided something like "C:\\x\\file.pdf"
    name = name.replace("\\", "/").split("/")[-1].strip()
    if not name:
        return default

    # Replace illegal characters (Windows-friendly)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()

    # Avoid reserved names / too short
    if name in {".", ".."}:
        return default

    return name


def _ensure_suffix(filename: str, default_suffix: str) -> str:
    """
    Ensure filename has a suffix like '.pdf'. If missing, append default_suffix.
    default_suffix should include the dot.
    """
    p = Path(filename)
    if p.suffix:
        return filename
    if not default_suffix.startswith("."):
        default_suffix = "." + default_suffix
    return filename + default_suffix


def write_bytes_to_workdir(
    data: bytes,
    *,
    source_name: str,
    workdir: Union[str, Path],
    default_suffix: str = ".bin",
    prefix: str = "",
    overwrite: bool = False,
) -> Path:
    """
    Persist bytes as a file in workdir and return the created Path.

    - source_name: used to derive file name (sanitized)
    - default_suffix: used if source_name has no extension
    - prefix: optional prefix for the written file (e.g. 'ds_' or 'pan_')
    - overwrite: if False, avoid collisions by adding _1, _2, ...
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("data must be bytes")

    wd = Path(workdir)
    wd.mkdir(parents=True, exist_ok=True)

    filename = _sanitize_filename(source_name)
    filename = _ensure_suffix(filename, default_suffix)

    if prefix:
        filename = f"{prefix}{filename}"

    path = wd / filename

    if not overwrite and path.exists():
        stem = path.stem
        suf = path.suffix
        i = 1
        while True:
            candidate = wd / f"{stem}_{i}{suf}"
            if not candidate.exists():
                path = candidate
                break
            i += 1

    path.write_bytes(bytes(data))
    return path


def call_with_path(
    reader: Callable[[str], T],
    data: bytes,
    *,
    source_name: str,
    workdir: Union[str, Path],
    default_suffix: str = ".bin",
    prefix: str = "",
    overwrite: bool = False,
    cleanup: bool = False,
) -> T:
    """
    Convenience helper:
    - writes bytes to a file (in workdir)
    - calls reader(path_as_str)
    - optionally deletes the file afterwards (cleanup=True)

    The reader is expected to take a *string path* (like your datasheet readers).
    """
    p = write_bytes_to_workdir(
        data,
        source_name=source_name,
        workdir=workdir,
        default_suffix=default_suffix,
        prefix=prefix,
        overwrite=overwrite,
    )
    try:
        return reader(str(p))
    finally:
        if cleanup:
            try:
                p.unlink(missing_ok=True)  # py>=3.8 supports missing_ok
            except Exception:
                # do not fail the pipeline on cleanup issues
                pass
