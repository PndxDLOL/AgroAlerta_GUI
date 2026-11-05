from pathlib import Path
from copy import deepcopy
import numpy as np
import pandas as pd
import pytest
from agroalerta.textio import read_utf8
from agroalerta.regional import product_panel
from agroalerta.v1 import registered_predictions,common_price_metrics
from agroalerta.templates import excel_to_csv,csv_templates
from agroalerta.data import load_bytes,MONTH_FILE,YEAR_FILE
from agroalerta.appearance import theme_figure
from agroalerta.charts import registered_plot

ROOT=Path(__file__).resolve().parents[1]

def test_windows_utf8_reading(tmp_path):
    value="ÁREA, producción e imputación"
    raw=value.encode("utf-8")
    with pytest.raises(UnicodeDecodeError):raw.decode("cp1252")
    p=tmp_path/"reglas.md";p.write_bytes(raw)
    assert read_utf8(p)==value
    p.write_bytes(b"\xef\xbb\xbf"+raw);assert read_utf8(p)==value

def test_regional_median_independent_calculation(bundle):
    long,_,_,_,summary=product_panel(bundle.monthly,"Arroz")
    raw=long.pivot(index="fecha",columns="pais",values="precio_usd_nominal_t__original")
    r=100*np.log(raw/raw.shift())
    sigma=r.rolling(3,min_periods=3).std(ddof=1)
    expected=sigma.median(axis=1).where(sigma.notna().all(axis=1))
    assert np.allclose(summary.vol_regional_usd_original_pp,expected,equal_nan=True)
    assert summary.iloc[-1].vol_regional_usd_original_pp==pytest.approx(2.468620,abs=1e-6)

def test_fixed_basket_does_not_hide_missing_country(bundle):
    changed=deepcopy(bundle.monthly)
    mask=changed.pais.eq("Perú")&changed.producto.eq("Arroz")&changed.fecha.eq(pd.Timestamp("2024-11-01"))
    changed.loc[mask,"precio_lcu_t__original"]=np.nan
    changed.loc[mask,"precio_lcu_t__imputado"]=True
    _,_,_,_,s=product_panel(changed,"Arroz")
    row=s.loc[s.fecha.eq(pd.Timestamp("2024-12-01"))].iloc[0]
    assert row.volatilidades_originales_disponibles==2
    assert pd.isna(row.vol_regional_usd_original_pp)
    assert row.vol_regional_usa_imputacion

def test_regional_no_jump_across_missing_month(bundle):
    _,_,_,_,s=product_panel(bundle.monthly,"Arroz")
    for i in range(1,len(s)):
        if pd.isna(s.iloc[i-1].vol_regional_usd_original_pp):assert pd.isna(s.iloc[i].variacion_vol_original_pp)

def test_single_country_is_not_regional_index(bundle):
    _,_,_,_,s=product_panel(bundle.monthly,"Arroz",["Perú"])
    assert s.vol_regional_usd_original_pp.isna().all()

def test_v1_values_are_not_rebuilt_or_smoothed(bundle):
    d=registered_predictions(bundle,"Colombia","Arroz","mensual","precio_lcu_t",stage="prueba")
    metrics,common=common_price_metrics(d,["Ingenuo","ARIMA"])
    assert metrics.Casos.eq(24).all()
    keys=["pais","producto","fecha","modelo","pronostico"]
    merged=common[keys].merge(bundle.predictions,on=keys,how="inner")
    assert len(merged)>=len(common)
    fig=theme_figure(registered_plot(common,"LCU/t"),"oscuro")
    assert fig.layout.plot_bgcolor=="#152222"

def test_blank_excel_is_rejected():
    with pytest.raises(ValueError,match="vacía"):
        excel_to_csv((ROOT/"assets/Plantilla_AgroAlerta.xlsx").read_bytes())

def test_excel_conversion_preserves_originals_and_flags():
    files=excel_to_csv((ROOT/"tests/fixtures/plantilla_prueba.xlsx").read_bytes())
    bundle=load_bytes(files[MONTH_FILE],files[YEAR_FILE])
    assert len(bundle.monthly)==3 and bundle.monthly.precio_lcu_t__imputado.sum()==1
    assert bundle.monthly.iloc[0].precio_lcu_t__original==100
    assert pd.isna(bundle.monthly.iloc[1].precio_lcu_t__original)
    assert bundle.monthly.iloc[1].precio_lcu_t==110

def test_csv_headers_match_contract():
    files=csv_templates()
    assert set(files)=={MONTH_FILE,YEAR_FILE}
    assert "precio_lcu_t__original" in files[MONTH_FILE].decode("utf-8-sig")
