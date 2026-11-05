import numpy as np
import pandas as pd
import pytest
from agroalerta.alerts import Rules,synthetic_case,confusion,evaluate_predictions,compare_common,contextual_rules

@pytest.mark.parametrize("name,state",[("Estabilidad","Sin señal estadística"),("Choque +30 %","Volatilidad alta"),("Corte de tres meses","No evaluable")])
def test_synthetic_cases(name,state):
    assert synthetic_case(name)[2]["estado"]==state

def test_undefined_metrics_not_zero():
    c=confusion([0,0],[0,0])
    assert np.isnan(c["precision"]) and np.isnan(c["sensibilidad"]) and c["TN"]==2

def test_common_cases_and_fixed_test_threshold(bundle):
    ev=evaluate_predictions(bundle)
    mt,cases=compare_common(ev,["Ingenuo","ARIMA","Holt-Winters"])
    assert mt.N.eq(144).all()
    assert cases.calibracion_fin.eq(pd.Timestamp("2022-12-01")).all()
    assert cases.groupby(["pais","producto"]).umbral.nunique().eq(1).all()
    assert mt.loc[mt.modelo.eq("Ingenuo"),["TP","FP","FN","TN"]].iloc[0].tolist()==[10,0,7,127]

def test_imputed_truth_is_excluded(bundle):
    p=bundle.predictions.iloc[:1].copy()
    p.loc[:,"frecuencia"]="mensual";p.loc[:,"variable"]="precio_lcu_t"
    p.loc[:,"pais"]="Colombia";p.loc[:,"producto"]="Arroz"
    p.loc[:,"fecha"]=pd.Timestamp("2018-06-01");p.loc[:,"origen"]=pd.Timestamp("2018-05-01")
    p.loc[:,"ventana"]="total";p.loc[:,"preparacion"]="KNN V4 por corte"
    p.loc[:,"observado"]=np.nan
    e=evaluate_predictions(bundle,p)
    assert not e.iloc[0].evaluable and pd.isna(e.iloc[0].evento_real)

def test_commercial_rules_gated(bundle):
    d=contextual_rules(bundle,"Colombia","Arroz","2024-12-01",Rules(),{})
    assert d.loc[d.regla.str.startswith(("R3","R4")),"estado"].str.startswith("No habilitada").all()
    d=contextual_rules(bundle,"Colombia","Arroz","2024-12-01",Rules(),{"Colombia|Arroz":{"validada":"false","evidencia":"nota"}})
    assert d.loc[d.regla.str.startswith(("R3","R4")),"estado"].str.startswith("No habilitada").all()
