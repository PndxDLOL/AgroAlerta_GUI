import importlib.util
from pathlib import Path
import pytest
from agroalerta.data import load_bytes,read_directory,MONTH_FILE

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("update",ROOT/"scripts/actualizar_datos.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_update_roundtrip_and_rejection(tmp_path):
    destination=tmp_path/"current"
    result=module.update(ROOT/"data/demo",destination)
    b=load_bytes(*read_directory(destination))
    assert len(b.predictions)>0 and result["fuentes"]==b.hashes
    before=(destination/MONTH_FILE).read_bytes()
    bad=tmp_path/"bad";bad.mkdir();(bad/MONTH_FILE).write_text("archivo incorrecto")
    with pytest.raises(ValueError):module.update(bad,destination)
    assert (destination/MONTH_FILE).read_bytes()==before
