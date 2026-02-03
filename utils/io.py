# utils/io.py
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable, List, Optional, Tuple, Union

import pandas as pd


TextSource = Union[str, Path, bytes, BytesIO]


@dataclass(frozen=True)
class PVSystTextBlocks:
    header_lines: List[str]     # lines starting with '#'
    body_lines: List[str]       # the rest


def read_text_lines(source: TextSource, encoding: str = "utf-8") -> List[str]:
    """
    Read text from:
      - file path (str/Path)
      - bytes
      - BytesIO
    Returns a list of lines (without trailing newlines).
    """
    if isinstance(source, (str, Path)):
        p = Path(source)
        raw = p.read_bytes()
    elif isinstance(source, BytesIO):
        raw = source.getvalue()
    elif isinstance(source, (bytes, bytearray)):
        raw = bytes(source)
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    text = raw.decode(encoding, errors="ignore")
    return [line.rstrip("\n\r") for line in text.splitlines()]


def split_pvsyst_hash_header(lines: List[str]) -> PVSystTextBlocks:
    """
    PVSyst TMY: header lines start with '#', then CSV-like content.
    """
    header: List[str] = []
    body: List[str] = []

    in_header = True
    for line in lines:
        if in_header and line.startswith("#"):
            header.append(line)
        else:
            in_header = False
            if line.strip() != "":
                body.append(line)

    return PVSystTextBlocks(header_lines=header, body_lines=body)


def detect_separator(sample_line: str) -> str:
    # Most PVSyst uses ';'
    if sample_line.count(";") >= sample_line.count(","):
        return ";"
    return ","


def read_delimited_from_lines(lines: List[str], sep: str) -> pd.DataFrame:
    """
    Read a delimited table from in-memory lines.
    """
    buf = "\n".join(lines).encode("utf-8", errors="ignore")
    return pd.read_csv(BytesIO(buf), sep=sep, engine="python")
