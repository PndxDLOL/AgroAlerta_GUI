"""Exportación de resultados actuales y de su configuración reproducible."""
from io import BytesIO
from zipfile import ZipFile,ZIP_DEFLATED
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import platform
from importlib.metadata import version
import numpy as np
import pandas as pd
from .data import KEY,quality
from .indicators import monthly_indicators,annual_indicators
from .alerts import Rules,evaluate_predictions,compare_common,historical_signals,synthetic_case,default_cutoff
from .models import forecast
from . import __version__
from .regional import product_panel

def csv_bytes(d):return d.to_csv(index=False).encode("utf-8-sig")

def recalculate_backtest(bundle,models=("Ingenuo","Holt amortiguado","ARIMA"),rules=None):
    """Nuevo ensayo de un paso en los últimos 24 meses, sin elegir con la prueba."""
    rules=rules or Rules();cut=default_cutoff(bundle,rules);rows=[]
    for (c,pr),g in bundle.monthly.groupby(KEY):
        for target in g.loc[g.fecha.gt(cut),"fecha"]:
            origin=target-pd.offsets.MonthBegin(1)
            pred,_,history=forecast(bundle,c,pr,origin,models,horizon=1)
            truth=g.set_index("fecha").precio_lcu_t__original.get(target,np.nan)
            for row in pred.to_dict("records"):
                row.update(observado=truth,etapa="prueba",preparacion="KNN por corte · Streamlit",
                           version="SAT Streamlit V1 · nuevo ensayo")
                rows.append(row)
    return pd.DataFrame(rows)

def functional_checks(bundle,rules):
    checks=[]
    for f,d in [("mensual",bundle.monthly),("anual",bundle.annual)]:
        checks.append(dict(caso=f"Llaves únicas {f}",esperado=True,obtenido=not d.duplicated(KEY+["fecha"]).any(),tipo="Validación de datos"))
    for name,expected in [("Estabilidad","Sin señal estadística"),("Choque +30 %","Volatilidad alta"),("Corte de tres meses","No evaluable")]:
        _,_,sig=synthetic_case(name,rules)
        checks.append(dict(caso=name,esperado=expected,obtenido=sig["estado"],tipo="Prueba sintética de regla"))
    d=pd.DataFrame(checks);d["cumple"]=d.esperado==d.obtenido
    return d

def evidence_files(bundle,rules=None,predictions=None):
    rules=rules or Rules();m=monthly_indicators(bundle.monthly);a=annual_indicators(bundle.annual)
    evaluation=evaluate_predictions(bundle,predictions,rules)
    models=sorted(evaluation.modelo.unique()) if len(evaluation) else []
    metrics,common=compare_common(evaluation,models)
    historical=pd.concat([historical_signals(bundle,c,pr,rules) for c,pr in m[KEY].drop_duplicates().itertuples(index=False,name=None)],ignore_index=True)
    checks=functional_checks(bundle,rules)
    manifest=dict(version_app=__version__,fase_predictiva="V1; Predicción V2 pendiente de investigación",generado=datetime.now(ZoneInfo("America/Bogota")).isoformat(),
        entorno={"python":platform.python_version(),**{p:version(p) for p in ["streamlit","pandas","numpy","scikit-learn","statsmodels","plotly"]}},
        huella=bundle.fingerprint,fuentes=bundle.hashes,resultados_fuente=bundle.artifact_hashes,
        corte_datos=str(m.fecha.max().date()),calibracion_fin=str(default_cutoff(bundle,rules).date()),
        reglas=rules.to_dict(),calidad=quality(bundle),modelos_comparados=models,
        advertencias=bundle.warnings+["Evaluación retrospectiva exploratoria; los datos 2023–2024 ya habían sido consultados en el piloto.",
          "Las etiquetas se obtienen de originales. La referencia de persistencia requiere un quinto precio original.",
          "El rezago de publicación anual de dos años es un supuesto pendiente de verificar.",
          "Los escenarios sintéticos prueban lógica y no se suman al desempeño en mercados reales."])
    # Markdown sin una dependencia adicional de presentación.
    if len(metrics):
        cells=[[str(x) if isinstance(x,str) else f"{x:.4f}" if pd.notna(x) else "NaN" for x in row] for row in metrics.itertuples(index=False,name=None)]
        summary="| "+" | ".join(metrics.columns)+" |\n| "+" | ".join(["---"]*len(metrics.columns))+" |\n"
        summary+="\n".join("| "+" | ".join(row)+" |" for row in cells)
    else:summary="Sin predicciones vinculadas a estas bases; no se calcularon métricas predictivas."
    report=f"""# AgroAlerta SAT V1

Generado: {manifest['generado']}. Corte observado: {manifest['corte_datos']}.

Se evaluó un evento de volatilidad de tres retornos por encima del percentil {rules.q_high*100:.0f} de calibración.
Umbral de prueba fijo hasta {manifest['calibracion_fin']}; horizonte de un mes.
Modelos comparados en la misma intersección de casos observados elegibles. No se eligió un ganador definitivo.

## Resultados de prueba en casos comunes

{summary}

N, TP, FP, FN y TN son conteos. Las otras medidas son proporciones entre 0 y 1; NaN significa no calculable.
Las etiquetas requieren precios originales positivos. Se conservan los motivos de exclusión.
Los resultados de todos los modelos y exclusiones están en evaluacion_alertas.csv.

## Alcance de la evidencia

La tabla de pruebas funcionales verifica llaves y tres entradas artificiales de la regla. Las pruebas de interfaz
automatizadas se ejecutan aparte con pytest y AppTest. No son una validación de utilidad con usuarios.
Los indicadores comerciales son candidatos: su correspondencia física entre dominios continúa pendiente.
La aplicación muestra resultados anuales en su frecuencia y no los convierte en meses independientes.
No se validaron huecos de 36 meses ni se calibra inseguridad alimentaria.
"""
    files={"indicadores_mensuales.csv":csv_bytes(m),"indicadores_anuales.csv":csv_bytes(a),
        "alertas_historicas.csv":csv_bytes(historical),"evaluacion_alertas.csv":csv_bytes(evaluation),
        "metricas_casos_comunes.csv":csv_bytes(metrics),"casos_comunes.csv":csv_bytes(common),
        "pruebas_funcionales.csv":csv_bytes(checks),"manifest.json":json.dumps(manifest,ensure_ascii=False,indent=2).encode(),
        "RESULTADOS.md":report.encode()}
    for product in sorted(m.producto.unique()):
        long,_,_,_,summary=product_panel(m,product)
        # Un identificador evita que un nombre de producto se interprete como ruta.
        i=list(sorted(m.producto.unique())).index(product)+1
        files[f"regional_producto_{i}_detalle.csv"]=csv_bytes(long)
        files[f"regional_producto_{i}_indicador.csv"]=csv_bytes(summary)
    return files

def evidence_zip(bundle,rules=None,predictions=None):
    out=BytesIO()
    with ZipFile(out,"w",ZIP_DEFLATED) as z:
        for name,data in evidence_files(bundle,rules,predictions).items():z.writestr(name,data)
    return out.getvalue()
