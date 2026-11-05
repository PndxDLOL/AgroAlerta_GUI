"""Regenerar indicadores, señales, casos, exclusiones y métricas del SAT."""
from pathlib import Path
import argparse,json,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from agroalerta.data import read_directory,load_bytes,resolve_directory
from agroalerta.alerts import Rules
from agroalerta.evidence import evidence_files,recalculate_backtest,csv_bytes

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--entrada",type=Path,default=None)
    p.add_argument("--salida",type=Path,default=ROOT/"data/processed/SAT/resultados_sat_V1")
    p.add_argument("--recalcular",action="store_true",help="Ejecutar un nuevo ensayo de 3 modelos con las bases actuales")
    args=p.parse_args()
    m,a,extras=read_directory(args.entrada or resolve_directory(ROOT))
    bundle=load_bytes(m,a,extras)
    rules=Rules(**json.loads((ROOT/"config/reglas.json").read_text(encoding="utf-8"))["reglas"])
    predictions=recalculate_backtest(bundle,rules=rules) if args.recalcular else None
    files=evidence_files(bundle,rules,predictions)
    if predictions is not None:files["nuevo_ensayo_streamlit.csv"]=csv_bytes(predictions)
    args.salida.mkdir(parents=True,exist_ok=True)
    for name,raw in files.items():(args.salida/name).write_bytes(raw)
    print(f"{len(files)} archivos generados en {args.salida.resolve()}")

if __name__=="__main__":main()
