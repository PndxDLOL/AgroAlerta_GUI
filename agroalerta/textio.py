"""Lectura independiente de la codificación regional de Windows."""
from pathlib import Path

def read_utf8(path):
    # utf-8-sig admite también un BOM creado por editores de Windows.
    return Path(path).read_text(encoding="utf-8-sig")
