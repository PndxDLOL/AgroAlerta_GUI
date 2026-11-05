from copy import deepcopy
import numpy as np
import pandas as pd
import pytest
from agroalerta.data import boolean,normalize,read_csv,load_bytes,DataError,quality
from agroalerta.indicators import monthly_indicators,annual_indicators

def raw(d):return d.to_csv(index=False).encode("utf-8")

def test_flags_false_string():
    assert boolean(pd.Series(["False","True","0","1"])).tolist()==[False,True,False,True]
    with pytest.raises(DataError):boolean(pd.Series(["quizás"]))

def test_duplicate_rejected(source_bytes):
    d=read_csv(source_bytes[0]);d=pd.concat([d,d.iloc[:1]])
    with pytest.raises(DataError,match="duplicadas"):normalize(raw(d),"mensual")

def test_original_preserved(source_bytes):
    d=read_csv(source_bytes[0]);idx=d.precio_lcu_t__original.first_valid_index();d.loc[idx,"precio_lcu_t"]*=1.1
    with pytest.raises(DataError,match="originales"):normalize(raw(d),"mensual")

def test_calendar_gap_remains_nan(source_bytes):
    d=read_csv(source_bytes[0]);row=d.iloc[10];d=d.drop(d.index[10]);out=normalize(raw(d),"mensual")
    x=out.loc[out.pais.eq(row.pais)&out.producto.eq(row.producto)&out.fecha.eq(pd.Timestamp(row.fecha))].iloc[0]
    assert pd.isna(x.precio_lcu_t) and x.fila_calendario_generada
    assert not x.precio_lcu_t__imputado

def test_stale_predictive_results_disabled(source_bytes):
    m,a,e=source_bytes
    b=load_bytes(m+b"\n",a,e)
    assert b.predictions.empty and "cambiaron" in b.warnings[0]

def test_pilot_counts(bundle):
    q=quality(bundle)
    assert (q["mensual"],q["anual"],q["precios_imputados"],q["faltantes_anuales"])==(936,78,130,28)
    assert q["faltantes_base"]==158 and q["celdas_base"]==1950

def test_notebook_indicator_equivalence(bundle):
    m=monthly_indicators(bundle.monthly)
    for v in ["precio_usd_nominal_t","retorno_log_pct","volatilidad_3m"]:
        assert np.allclose(m[v],bundle.monthly[v],equal_nan=True)
    a=annual_indicators(bundle.annual)
    for v in ["productividad_calculada_t_ha","oferta_parcial_candidata_t","exposicion_importadora_candidata_pct"]:
        assert np.allclose(a[v],bundle.annual[v],equal_nan=True)

def test_imputation_propagates_windows(bundle):
    d=bundle.monthly.iloc[:8].copy()
    d["precio_lcu_t"]=np.arange(100.,108.);d["precio_lcu_t__original"]=d.precio_lcu_t
    d["precio_lcu_t__imputado"]=False
    d.loc[d.index[3],"precio_lcu_t__original"]=np.nan;d.loc[d.index[3],"precio_lcu_t__imputado"]=True
    r=monthly_indicators(d)
    assert r.retorno_log_pct__usa_imputacion.tolist()==[False,False,False,True,True,False,False,False]
    assert r.volatilidad_3m__usa_imputacion.tolist()==[False,False,False,True,True,True,True,False]

def test_zero_denominators(bundle):
    a=bundle.annual.iloc[:1].copy()
    a["produccion_t"]=a["produccion_t__original"]=0
    a["area_ha"]=a["area_ha__original"]=0
    out=annual_indicators(a).iloc[0]
    assert pd.isna(out.productividad_calculada_t_ha) and pd.isna(out.exposicion_importadora_candidata_pct)
