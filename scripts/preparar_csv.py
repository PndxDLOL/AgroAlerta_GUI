"""Convertir la plantilla Excel a bases compatibles, sin cambiar originales."""
from pathlib import Path
import argparse,json,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from agroalerta.templates import excel_to_csv
from agroalerta.data import sha

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--excel",type=Path,required=True)
    parser.add_argument("--salida",type=Path,default=ROOT/"data/importacion_csv")
    args=parser.parse_args()
    try:files=excel_to_csv(args.excel.read_bytes())
    except (ValueError,KeyError,OSError) as exc:parser.error(str(exc))
    args.salida.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():(args.salida/name).write_bytes(raw)
    manifest=dict(origen="Plantilla Excel del equipo",sha256={n:sha(v) for n,v in files.items()},
        nota="Compatible con el contrato de columnas V4. No ejecuta imputación ni modelado.")
    (args.salida/"conversion.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Dos bases CSV generadas en {args.salida.resolve()}")

if __name__=="__main__":main()
