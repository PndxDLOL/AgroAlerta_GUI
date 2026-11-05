"""Pronósticos puntuales sobre historia por corte; parámetros del piloto V1."""
import time,warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from statsmodels.tsa.holtwinters import SimpleExpSmoothing,ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from .imputation import reconstruct_history

MODELS=["Ingenuo","Ingenuo estacional","Deriva","SES","Holt amortiguado",
        "Holt-Winters","ARIMA","SARIMA","Ridge AR","Random Forest AR","MLP"]

def ineligible(model,y,observed,frequency):
    if model not in MODELS:return "El motor interactivo no implementa ese modelo."
    if len(y)==0:return "No hay historia antes del origen."
    if not np.isfinite(y).all():return "Persisten faltantes en la historia; no se aplica un relleno oculto."
    if np.any(y<0):return "Hay magnitudes negativas."
    if frequency=="anual" and model in ["Ingenuo estacional","Holt-Winters","SARIMA"]:
        return "No se supone una estacionalidad de doce años."
    minimum={"Ingenuo":1,"Ingenuo estacional":12,"Deriva":3,"SES":3,
             "Holt amortiguado":4,"Holt-Winters":36,"ARIMA":6 if frequency=="anual" else 12,"SARIMA":36}
    if model in minimum and len(y)<minimum[model]:return f"Requiere {minimum[model]} períodos; hay {len(y)}."
    if model in ["Ridge AR","Random Forest AR","MLP"]:
        lag=12 if frequency=="mensual" else 2
        n=int(np.asarray(observed)[lag:].sum());need=24 if model=="MLP" else 4
        if n<need:return f"Requiere {need} respuestas originales después de {lag} rezagos; hay {n}."
    return ""

def predict(model,history,frequency,horizon=1):
    """Ajuste único y escenario multipaso; los futuros no se vuelven etiquetas."""
    start=time.perf_counter()
    y=history.valor.to_numpy(float);obs=history.original.notna().to_numpy()
    reason=ineligible(model,y,obs,frequency)
    meta=dict(modelo=model,estado="no_elegible",motivo=reason,advertencias="",convergencia=True,
              segundos=0.,n_historia=len(y),imputadas=int(history.imputado.sum()))
    if reason:return np.full(horizon,np.nan),meta
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            z=np.log1p(y)
            if model=="Ingenuo":values=np.repeat(y[-1],horizon)
            elif model=="Ingenuo estacional":values=np.resize(y[-12:],horizon)
            elif model=="Deriva":values=y[-1]+np.arange(1,horizon+1)*(y[-1]-y[0])/(len(y)-1)
            elif model in ["SES","Holt amortiguado","Holt-Winters"]:
                if model=="SES":fit=SimpleExpSmoothing(z,initialization_method="estimated").fit(optimized=True)
                else:fit=ExponentialSmoothing(z,trend="add",damped_trend=True,
                        seasonal="add" if model=="Holt-Winters" else None,
                        seasonal_periods=12 if model=="Holt-Winters" else None,
                        initialization_method="estimated").fit(optimized=True,use_brute=False)
                values=np.expm1(np.asarray(fit.forecast(horizon)))
                meta["convergencia"]=bool(fit.mle_retvals.get("success",True))
            elif model in ["ARIMA","SARIMA"]:
                if model=="ARIMA":fit=ARIMA(z,order=(1,1,0),trend="n").fit(method_kwargs={"maxiter":80})
                else:fit=SARIMAX(z,order=(0,1,1),seasonal_order=(0,1,1,12),trend="n",
                            enforce_stationarity=False,enforce_invertibility=False).fit(disp=False,maxiter=60)
                values=np.expm1(np.asarray(fit.forecast(horizon)))
                meta["convergencia"]=bool(fit.mle_retvals.get("converged",True))
            else:
                lag=12 if frequency=="mensual" else 2
                X=np.asarray([z[i-lag:i] for i in range(lag,len(z))]);target=z[lag:]
                valid=obs[lag:];X,target=X[valid],target[valid]
                if model=="Random Forest AR":
                    fitted=RandomForestRegressor(n_estimators=60,max_depth=4,min_samples_leaf=2,random_state=42,n_jobs=1).fit(X,target)
                    def next_value(q):return fitted.predict(q)[0]
                else:
                    scale=StandardScaler().fit(X);center=target.mean();sd=max(target.std(),.05)
                    reg=Ridge(alpha=1.) if model=="Ridge AR" else MLPRegressor(hidden_layer_sizes=(16,),activation="tanh",solver="lbfgs",alpha=.1,max_iter=250,random_state=42)
                    reg.fit(scale.transform(X),(target-center)/sd)
                    def next_value(q):return reg.predict(scale.transform(q))[0]*sd+center
                path=list(z);values=[]
                for _ in range(horizon):
                    pred=float(next_value(np.asarray(path[-lag:])[None,:]));path.append(pred);values.append(np.expm1(pred))
                values=np.asarray(values)
            meta["advertencias"]=" | ".join(sorted(set(str(w.message)[:200] for w in caught)))
        if not np.isfinite(values).all():raise ValueError("Pronóstico no finito.")
        meta.update(estado="ok",motivo="",recorte_no_negativo=bool((values<0).any()))
        values=np.maximum(0,values)
    except Exception as exc:
        values=np.full(horizon,np.nan);meta.update(estado="error",motivo=f"{type(exc).__name__}: {str(exc)[:200]}")
    meta["segundos"]=time.perf_counter()-start
    return values,meta

def forecast(bundle,country,product,origin,models,frequency="mensual",variable="precio_lcu_t",
             horizon=1,window="total",preparation="KNN",hidden_dates=None):
    history=reconstruct_history(bundle,frequency,variable,country,product,origin,preparation,hidden_dates)
    if window!="total":history=history.tail(int(window))
    dates=pd.date_range(pd.Timestamp(origin),periods=horizon+1,freq="MS" if frequency=="mensual" else "YS")[1:]
    rows=[];details=[]
    for model in models:
        values,meta=predict(model,history,frequency,horizon);details.append(meta)
        for j,(date,value) in enumerate(zip(dates,values),1):
            rows.append(dict(pais=country,producto=product,origen=pd.Timestamp(origin),fecha=date,
                frecuencia=frequency,variable=variable,modelo=model,paso=j,pronostico=value,
                preparacion=preparation,ventana=str(window),estado=meta["estado"],motivo=meta["motivo"],
                n_historia=len(history),imputadas=int(history.imputado.sum()),
                huella_datos=bundle.fingerprint))
    return pd.DataFrame(rows),pd.DataFrame(details),history
