from copy import deepcopy
import numpy as np
import pandas as pd
from agroalerta.imputation import reconstruct_history
from agroalerta.models import forecast,predict

def test_future_values_cannot_change_training(bundle):
    origin=pd.Timestamp("2019-12-01")
    baseline=reconstruct_history(bundle,"mensual","precio_lcu_t","Colombia","Arroz",origin)
    altered=deepcopy(bundle)
    future=altered.monthly.fecha.gt(origin)
    altered.monthly.loc[future,"precio_lcu_t__original"]*=100
    altered.annual.loc[altered.annual.fecha.gt(origin),"produccion_t__original"]*=100
    candidate=reconstruct_history(altered,"mensual","precio_lcu_t","Colombia","Arroz",origin)
    pd.testing.assert_frame_equal(baseline,candidate)

def test_prepared_prices_are_not_training_source(bundle):
    changed=deepcopy(bundle);changed.monthly["precio_lcu_t"]*=100
    a=reconstruct_history(bundle,"mensual","precio_lcu_t","Colombia","Maíz","2024-12-01")
    b=reconstruct_history(changed,"mensual","precio_lcu_t","Colombia","Maíz","2024-12-01")
    pd.testing.assert_frame_equal(a,b)
    assert np.allclose(a.original.dropna(),a.loc[a.original.notna(),"valor"])

def test_forecast_matches_registered_naive_case(bundle):
    p=bundle.predictions
    row=p.loc[p.pais.eq("Colombia")&p.producto.eq("Arroz")&p.fecha.eq(pd.Timestamp("2024-12-01"))&
              p.modelo.eq("Ingenuo")&p.ventana.astype(str).eq("total")&p.preparacion.eq("KNN V4 por corte")&p.frecuencia.eq("mensual")].iloc[0]
    result,details,_=forecast(bundle,"Colombia","Arroz",row.origen,["Ingenuo"],horizon=1)
    assert details.iloc[0].estado=="ok" and np.isclose(result.iloc[0].pronostico,row.pronostico)

def test_annual_neural_and_seasonal_ineligible(bundle):
    _,details,_=forecast(bundle,"Colombia","Arroz","2024-01-01",["MLP","SARIMA"],"anual","produccion_t",1)
    assert details.estado.eq("no_elegible").all()

def test_missing_history_not_silently_filled():
    h=pd.DataFrame({"original":[np.nan,2.,3.],"valor":[np.nan,2.,3.],"imputado":[False]*3})
    p,meta=predict("Ingenuo",h,"mensual",1)
    assert np.isnan(p[0]) and meta["estado"]=="no_elegible"
