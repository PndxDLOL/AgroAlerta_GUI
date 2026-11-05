"""Diez KPI con frecuencia y propagación explícita de imputaciones."""
import numpy as np
import pandas as pd
from .data import KEY,ANNUAL

KPI = [
 ("precio_lcu_t","Precio al productor","LCU/t","mensual"),
 ("precio_usd_nominal_t","Precio en USD nominales","USD/t","mensual"),
 ("retorno_log_pct","Retorno logarítmico mensual","% log","mensual"),
 ("volatilidad_3m","Volatilidad de tres retornos","puntos porcentuales","mensual"),
 ("produccion_t","Producción","t","anual"),
 ("area_ha","Área cosechada","ha","anual"),
 ("productividad_calculada_t_ha","Productividad calculada","t/ha","anual"),
 ("exposicion_importadora_candidata_pct","Exposición importadora candidata","% de producción","anual"),
 ("exposicion_exportadora_candidata_pct","Exposición exportadora candidata","% de producción","anual"),
 ("oferta_parcial_candidata_t","Oferta parcial candidata","t","anual")]

def returns(s):
    positive=s.where(s.gt(0))
    return 100*np.log(positive/positive.shift(1))

def volatility(s):
    return returns(s).rolling(3,min_periods=3).std(ddof=1)

def monthly_indicators(frame):
    d=frame.sort_values(KEY+["fecha"]).copy()
    d["precio_usd_nominal_t"]=d.precio_lcu_t/d.tasa_lcu_usd.where(d.tasa_lcu_usd.gt(0))
    d["precio_usd_nominal_t__original"]=d.precio_lcu_t__original/d.tasa_lcu_usd.where(d.tasa_lcu_usd.gt(0))
    for field,fn,window in [("retorno_log_pct",returns,2),("volatilidad_3m",volatility,4)]:
        d[field]=d.groupby(KEY).precio_lcu_t.transform(fn)
        d[field+"__original"]=d.groupby(KEY).precio_lcu_t__original.transform(fn)
        d[field+"__usa_imputacion"] = d.groupby(KEY).precio_lcu_t__imputado.transform(lambda s:s.rolling(window,min_periods=1).max()).astype(bool)&d[field].notna()
    d["precio_usd_nominal_t__usa_imputacion"]=d.precio_lcu_t__imputado&d.precio_usd_nominal_t.notna()
    d["precio_lcu_t__usa_imputacion"]=d.precio_lcu_t__imputado
    return d

def annual_indicators(frame):
    d=frame.sort_values(KEY+["fecha"]).copy()
    for original in [False,True]:
        suffix="__original" if original else ""
        q=d["produccion_t"+suffix];area=d["area_ha"+suffix]
        m=d["importaciones_t"+suffix];x=d["exportaciones_t"+suffix]
        d["productividad_calculada_t_ha"+suffix]=q/area.where(area.gt(0))
        d["oferta_parcial_candidata_t"+suffix]=q+m-x
        d["exposicion_importadora_candidata_pct"+suffix]=100*m/q.where(q.gt(0))
        d["exposicion_exportadora_candidata_pct"+suffix]=100*x/q.where(q.gt(0))
        d["crecimiento_produccion_pct"+suffix]=d.groupby(KEY)["produccion_t"+suffix].transform(lambda s:100*s.pct_change(fill_method=None))
    dependencies={"productividad_calculada_t_ha":["produccion_t","area_ha"],
        "oferta_parcial_candidata_t":["produccion_t","importaciones_t","exportaciones_t"],
        "exposicion_importadora_candidata_pct":["produccion_t","importaciones_t"],
        "exposicion_exportadora_candidata_pct":["produccion_t","exportaciones_t"]}
    for v in ANNUAL:d[v+"__usa_imputacion"]=d[v+"__imputado"]
    for field,vs in dependencies.items():d[field+"__usa_imputacion"]=d[[v+"__imputado" for v in vs]].any(axis=1)&d[field].notna()
    d["crecimiento_produccion_pct__usa_imputacion"]=d.groupby(KEY).produccion_t__imputado.transform(lambda s:s.rolling(2,min_periods=1).max()).astype(bool)&d.crecimiento_produccion_pct.notna()
    return d

def streaks(series):
    """Longitudes de huecos originales, incluidos los que empiezan/terminan la serie."""
    missing=series.isna().to_numpy()
    boundaries=np.r_[0,np.flatnonzero(missing[1:]!=missing[:-1])+1,len(missing)]
    return [(series.index[a],series.index[b-1],int(b-a)) for a,b in zip(boundaries[:-1],boundaries[1:]) if missing[a]]

def descriptive(frame,fields):
    rows=[]
    for v in fields:
        for label,col in [("Original",v+"__original"),("Preparado",v)]:
            s=frame[col];mode=s.mode()
            rows.append(dict(variable=v,serie=label,calculables=int(s.notna().sum()),faltantes=int(s.isna().sum()),
                media=s.mean(),mediana=s.median(),moda=mode.iloc[0] if len(mode) else np.nan,
                desviacion=s.std(ddof=1),minimo=s.min(),maximo=s.max()))
    return pd.DataFrame(rows)
