"""Comparación por producto. Canasta fija y cobertura explícita, sin rellenar huecos."""
import numpy as np
import pandas as pd
from .indicators import monthly_indicators,returns,volatility

def product_panel(monthly,product,countries=None):
    data=monthly_indicators(monthly)
    data=data.loc[data.producto.eq(product)].copy()
    countries=sorted(countries if countries is not None else data.pais.unique())
    if not countries or data.empty:raise ValueError("No hay mercados para el producto seleccionado.")
    if set(countries)-set(data.pais):raise ValueError("Hay países que no tienen este producto.")
    dates=pd.date_range(data.fecha.min(),data.fecha.max(),freq="MS")
    data=data.set_index(["fecha","pais"]).reindex(pd.MultiIndex.from_product([dates,countries],names=["fecha","pais"])).reset_index()
    data["producto"]=product
    data=data.sort_values(["pais","fecha"])
    data["precio_usd_nominal_t__usa_imputacion"]=data.precio_usd_nominal_t__usa_imputacion.fillna(False).astype(bool)
    for suffix in ["","__original"]:
        col="precio_usd_nominal_t"+suffix
        data["retorno_usd_pct"+suffix]=data.groupby("pais")[col].transform(returns)
        data["volatilidad_usd_3m"+suffix]=data.groupby("pais")[col].transform(volatility)
    data["volatilidad_usd_3m__usa_imputacion"]=data.groupby("pais").precio_usd_nominal_t__usa_imputacion.transform(lambda x:x.rolling(4,min_periods=1).max()).astype(bool)&data.volatilidad_usd_3m.notna()
    wide=data.pivot(index="fecha",columns="pais",values="precio_usd_nominal_t").reindex(columns=countries)
    originals=data.pivot(index="fecha",columns="pais",values="precio_usd_nominal_t__original").reindex(columns=countries)
    flags=data.pivot(index="fecha",columns="pais",values="precio_usd_nominal_t__usa_imputacion").reindex(columns=countries).fillna(False)
    sigma=data.pivot(index="fecha",columns="pais",values="volatilidad_usd_3m__original").reindex(columns=countries)
    prepared_sigma=data.pivot(index="fecha",columns="pais",values="volatilidad_usd_3m").reindex(columns=countries)
    summary=pd.DataFrame(index=dates)
    summary.index.name="fecha"
    summary["mercados_canasta"]=len(countries)
    summary["precios_originales_disponibles"]=originals.notna().sum(axis=1)
    summary["volatilidades_originales_disponibles"]=sigma.notna().sum(axis=1)
    summary["cobertura_vol_original_pct"]=100*summary.volatilidades_originales_disponibles/len(countries)
    complete=sigma.notna().all(axis=1)&(len(countries)>=2)
    summary["vol_regional_usd_original_pp"]=sigma.median(axis=1).where(complete)
    summary["vol_regional_usd_preparada_pp"]=prepared_sigma.median(axis=1).where(prepared_sigma.notna().all(axis=1)&(len(countries)>=2))
    imputed=data.pivot(index="fecha",columns="pais",values="volatilidad_usd_3m__usa_imputacion").reindex(columns=countries).fillna(False)
    summary["vol_regional_usa_imputacion"]=imputed.any(axis=1)&summary.vol_regional_usd_preparada_pp.notna()
    summary["variacion_vol_original_pp"]=summary.vol_regional_usd_original_pp.diff()
    summary["variacion_vol_preparada_pp"]=summary.vol_regional_usd_preparada_pp.diff()
    summary["producto"]=product
    summary["canasta_paises"]=" | ".join(countries)
    return data,wide,originals,flags,summary.reset_index()
