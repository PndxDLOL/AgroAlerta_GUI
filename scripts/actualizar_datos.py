"""Importar las salidas de notebooks sin modificar originales ni ejecutar código ajeno."""
from pathlib import Path
import argparse,json,shutil,sys,tempfile
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from agroalerta.data import read_directory,load_bytes,MONTH_FILE,YEAR_FILE,quality

MANAGED={MONTH_FILE,YEAR_FILE,"configuracion.json","predicciones_evaluadas.csv",
         "ranking_escala_completa_casos_comunes.csv","manifest_actualizacion.json"}

def update(source,destination):
    source=Path(source).resolve();destination=Path(destination).resolve()
    if source==destination:raise ValueError("La fuente y el destino deben ser distintos.")
    m,a,extras=read_directory(source)
    bundle=load_bytes(m,a,extras,"Bases actualizadas")  # Validar antes de tocar el destino.
    if destination.exists():
        unknown={p.name for p in destination.iterdir()}-MANAGED
        if unknown:raise ValueError(f"El destino contiene archivos ajenos: {sorted(unknown)}. Elija una carpeta vacía.")
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix=".agroalerta-carga-",dir=destination.parent))
    backup=stage.with_name(stage.name+"-anterior")
    try:
        (stage/MONTH_FILE).write_bytes(m);(stage/YEAR_FILE).write_bytes(a)
        if bundle.config.get("fuentes")==bundle.hashes:
            for name,raw in extras.items():(stage/name).write_bytes(raw)
        manifest=dict(generado_utc=datetime.now(timezone.utc).isoformat(),fuentes=bundle.hashes,
            resultados_vinculados=len(bundle.predictions),calidad=quality(bundle),advertencias=bundle.warnings)
        (stage/"manifest_actualizacion.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
        if destination.exists():destination.rename(backup)
        try:stage.rename(destination)
        except Exception:
            if backup.exists():backup.rename(destination)
            raise
        if backup.exists():shutil.rmtree(backup)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument("--proyecto",type=Path,help="Carpeta raíz Proyecto_Precios_Agricolas")
    group.add_argument("--entrada",type=Path,help="Carpeta que contiene ambas bases V4")
    p.add_argument("--destino",type=Path,default=ROOT/"data/current")
    args=p.parse_args()
    source=args.entrada or args.proyecto/"data/processed/Imputacion/resultados_imputacion_V4"
    result=update(source,args.destino)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print("Actualización terminada. En AgroAlerta pulse Actualizar lectura.")

if __name__=="__main__":main()
