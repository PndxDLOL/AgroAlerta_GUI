"""Contrato mínimo compartido por la plantilla, el conversor y la interfaz."""
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED
import csv,io
import pandas as pd
from .data import ANNUAL,load_bytes,MONTH_FILE,YEAR_FILE

MONTH_COLUMNS=["pais","producto","fecha","precio_lcu_t","precio_lcu_t__original","tasa_lcu_usd"]
YEAR_COLUMNS=["pais","producto","fecha"]+ANNUAL+[v+"__original" for v in ANNUAL]

def csv_templates():
    files={}
    for name,cols in [(MONTH_FILE,MONTH_COLUMNS),(YEAR_FILE,YEAR_COLUMNS)]:
        output=io.StringIO();csv.writer(output,lineterminator="\n").writerow(cols)
        files[name]=output.getvalue().encode("utf-8-sig")
    return files

def csv_template_zip():
    out=BytesIO()
    with ZipFile(out,"w",ZIP_DEFLATED) as z:
        for name,raw in csv_templates().items():z.writestr(name,raw)
    return out.getvalue()

def excel_to_csv(raw):
    """Solo lee XLSX; no ejecuta macros ni inventa valores ausentes."""
    book=pd.ExcelFile(BytesIO(raw),engine="openpyxl")
    if not {"mensual","anual"}.issubset(book.sheet_names):
        raise ValueError("El Excel debe contener las hojas mensual y anual.")
    files=[]
    for name in ["mensual","anual"]:
        frame=pd.read_excel(book,sheet_name=name).dropna(how="all")
        if frame.empty:raise ValueError(f"La hoja {name} está vacía. Complete los datos antes de convertir.")
        files.append(frame.to_csv(index=False,date_format="%Y-%m-%d").encode("utf-8-sig"))
    bundle=load_bytes(*files,label="Excel convertido")
    result={}
    for filename,frame in [(MONTH_FILE,bundle.monthly),(YEAR_FILE,bundle.annual)]:
        result[filename]=frame.to_csv(index=False,date_format="%Y-%m-%d").encode("utf-8-sig")
    return result
