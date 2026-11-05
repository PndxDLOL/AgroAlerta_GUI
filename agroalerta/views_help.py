"""Ayuda y descargas disponibles también antes de cargar bases propias."""
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED
import streamlit as st
from .templates import csv_template_zip,excel_to_csv
from .textio import read_utf8

def download_guides(root,where="sidebar"):
    manual=root/"docs/Instructivo_AgroAlerta_V2.pdf"
    template=root/"assets/Plantilla_AgroAlerta.xlsx"
    if manual.exists():st.download_button("Descargar instructivo PDF",manual.read_bytes(),manual.name,"application/pdf",key=f"manual_{where}")
    if template.exists():st.download_button("Descargar plantilla Excel",template.read_bytes(),template.name,"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",key=f"xlsx_{where}")
    st.download_button("Descargar plantillas CSV",csv_template_zip(),"Plantillas_CSV_AgroAlerta.zip","application/zip",key=f"csv_templates_{where}")

def show_help(root):
    st.subheader("Instructivo y preparación de archivos")
    st.write("Descargue la guía y complete las hojas mensual y anual de la plantilla. Cada fila representa un país, producto y período. Las celdas vacías siguen siendo faltantes; cero representa una cantidad observada igual a cero.")
    download_guides(root,"help")
    st.markdown("### Convertir la plantilla Excel a dos CSV")
    file=st.file_uploader("Excel con hojas mensual y anual",type=["xlsx"],key="convert_excel")
    if file:
        try:
            files=excel_to_csv(file.getvalue())
        except (ValueError,KeyError,OSError) as exc:st.error(str(exc))
        else:
            out=BytesIO()
            with ZipFile(out,"w",ZIP_DEFLATED) as z:
                for name,raw in files.items():z.writestr(name,raw)
            st.success("Contrato validado. Descargue los CSV y guárdelos en la carpeta de entrada o cárguelos desde el panel lateral.")
            st.download_button("Descargar las dos bases CSV validadas",out.getvalue(),"Bases_AgroAlerta_CSV.zip","application/zip",key="converted_files")
    st.caption("La conversión exporta UTF-8, separador coma, punto decimal y fecha ISO. Reconoce originales e imputados por sus dos columnas, sin ejecutar una nueva imputación. Un escenario predictivo exportado no se acepta automáticamente como una nueva observación original.")
    st.markdown("### Mejoras de la fase predictiva")
    st.markdown(read_utf8(root/"docs/PLAN_PREDICCION_V2.md"))
