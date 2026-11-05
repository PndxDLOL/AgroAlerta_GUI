"""Resultados originales del notebook V1: un paso por corte, sin inventar curvas."""
import numpy as np
import pandas as pd

def registered_predictions(bundle,country,product,frequency,variable,window="total",stage=None):
    d=bundle.predictions
    if d.empty:return d.copy()
    d=d.loc[d.pais.eq(country)&d.producto.eq(product)&d.frecuencia.eq(frequency)&d.variable.eq(variable)].copy()
    if "preparacion" in d:d=d.loc[d.preparacion.eq("KNN V4 por corte")]
    if "ventana" in d:d=d.loc[d.ventana.astype(str).eq(str(window))]
    if stage is not None:d=d.loc[d.etapa.eq(stage)]
    if d.empty:return d
    offset=pd.offsets.MonthBegin(1) if frequency=="mensual" else pd.offsets.YearBegin(1)
    d=d.loc[d.fecha.eq(d.origen+offset)].copy()
    source=bundle.monthly if frequency=="mensual" else bundle.annual
    truth=source.loc[source.pais.eq(country)&source.producto.eq(product)].set_index("fecha")[variable+"__original"]
    actual=d.fecha.map(truth)
    d=d.loc[actual.notna()&np.isfinite(d.pronostico)&np.isclose(actual,d.observado,rtol=1e-8,atol=1e-6,equal_nan=False)].copy()
    d["error_absoluto"]=abs(d.pronostico-d.observado)
    return d.sort_values(["fecha","modelo"]).drop_duplicates(["fecha","modelo"])

def common_price_metrics(predictions,models):
    if predictions.empty or not models:return pd.DataFrame(),predictions.iloc[:0]
    d=predictions.loc[predictions.modelo.isin(models)].copy()
    keys=["pais","producto","fecha"]
    counts=d.groupby(keys).modelo.nunique()
    common=counts.loc[counts.eq(len(models))].index
    d=d.loc[pd.MultiIndex.from_frame(d[keys]).isin(common)]
    rows=[]
    for model,g in d.groupby("modelo"):
        errors=(g.pronostico-g.observado).to_numpy()
        rows.append(dict(Modelo=model,Casos=len(g),MAE=np.mean(abs(errors)),RMSE=np.sqrt(np.mean(errors**2)),
            nMAE=g.nae.mean() if "nae" in g else np.nan,MASE=g.ase.mean() if "ase" in g else np.nan))
    return pd.DataFrame(rows),d
