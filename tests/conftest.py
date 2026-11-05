from pathlib import Path
import pytest
from agroalerta.data import load_bytes,read_directory

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope="session")
def source_bytes():return read_directory(ROOT/"data/demo")

@pytest.fixture(scope="session")
def bundle(source_bytes):return load_bytes(*source_bytes)
