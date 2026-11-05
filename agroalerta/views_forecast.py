"""Dos ejercicios distintos: reproducción V1 y escenarios multipaso."""
import numpy as np
import pandas as pd
import streamlit as st
from .data import ANNUAL,boolean
from .models import MODELS
from .v1 import registered_predictions,common_price_metrics
from .charts import forecast_plot,registered_plot
from .evidence import csv_bytes

def show_forecasts(bundle,country,product,market,year_market,chart,table,compute):
    st.subheader("Predicción: evidencia del notebook y escenarios")
    frequency=st.selectbox("Frecuencia",["mensual","anual"],key="frequency")
    base=market if frequency=="mensual" else year_market
    if base.empty:st.warning("No hay datos de esa frecuencia para el mercado.");return
    variables=["precio_lcu_t"] if frequency=="mensual" else ANNUAL
    variable=st.selectbox("Variable objetivo",variables,key=f"target_{frequency}")
    unit="LCU/t" if frequency=="mensual" else variable
    mode=st.radio("Ejercicio predictivo",["Resultados V1 del notebook","Escenarios futuros"],horizontal=True,key="forecast_mode")
    if mode=="Resultados V1 del notebook":
        show_registered(bundle,country,product,frequency,variable,unit,chart,table)
    else:
        show_future(bundle,country,product,base,frequency,variable,unit,chart,table,compute)

def show_registered(bundle,country,product,frequency,variable,unit,chart,table):
    st.caption("Se grafican los valores del CSV de predicciones V1 vinculado por SHA-256 a estas bases. Cada punto es un pronóstico de un período desde un origen anterior, contrastado con una observación original.")
    c1,c2=st.columns(2)
    with c1:stage=st.selectbox("Etapa V1",["prueba","validacion"],key="v1_stage")
    with c2:window=st.selectbox("Ventana V1",["total","12","24","36"] if frequency=="mensual" else ["total","3","5"],key=f"v1_window_{frequency}")
    d=registered_predictions(bundle,country,product,frequency,variable,window,stage)
    if d.empty:
        st.info("No hay predicciones V1 compatibles con estos filtros. Reejecute el notebook y vincule sus salidas; puede explorar escenarios con las bases actuales.");return
    history_type=st.selectbox("Tipo de historia V1",["Todas","Original completa","Con imputaciones","Mixta e incompleta original"],key="v1_history")
    if history_type=="Original completa" and "original_completa" in d:d=d.loc[boolean(d.original_completa)]
    elif history_type=="Con imputaciones" and "imputadas" in d:d=d.loc[d.imputadas.gt(0)]
    elif history_type=="Mixta e incompleta original" and "mixta_incompleta_original" in d:d=d.loc[boolean(d.mixta_incompleta_original)]
    available=sorted(d.modelo.unique())
    if not available:st.info("Ese tipo de historia no tiene resultados en este mercado y ventana.");return
    key=f"v1_models_{frequency}_{variable}"
    if key in st.session_state and not set(st.session_state[key]).issubset(available):st.session_state.pop(key)
    models=st.multiselect("Modelos del notebook",available,default=[m for m in ["Ingenuo","Holt-Winters","ARIMA"] if m in available] or available[:2],max_selections=4,key=key)
    metrics,common=common_price_metrics(d,models)
    if common.empty:st.info("Seleccione modelos que compartan fechas elegibles.");return
    chart(registered_plot(common,unit));table(metrics)
    st.caption("MAE y RMSE conservan la unidad del objetivo; nMAE y MASE usan las escalas guardadas por cada corte V1. La comparación usa fechas comunes. Una mejora de precio no demuestra anticipación de alertas.")
    cols=[x for x in ["fecha","origen","modelo","observado","pronostico","error_absoluto","imputadas","pendientes","preparacion","ventana"] if x in common]
    table(common[cols])
    st.download_button("Descargar resultados V1 seleccionados",csv_bytes(common),"predicciones_V1_seleccionadas.csv","text/csv",key="download_v1")
    st.info("2023-2024 es una prueba retrospectiva ya examinada. Sus resultados se muestran sin volver a elegir el modelo por esa puntuación. La interfaz V2 conserva la fase predictiva V1; la investigación de Predicción V2 está documentada como trabajo futuro.")

def show_future(bundle,country,product,base,frequency,variable,unit,chart,table,compute):
    st.caption("Cada escenario vuelve a los originales y reconstruye el entrenamiento usando solo períodos hasta el origen. El zoom del gráfico no modifica el entrenamiento.")
    dates=list(base.fecha.dt.strftime("%Y-%m-%d"));key=f"origin_{frequency}_{country}_{product}"
    if st.session_state.get(key) not in dates:st.session_state.pop(key,None)
    origin=st.select_slider("Origen del escenario",options=dates,value=dates[-1],key=key)
    c1,c2=st.columns(2)
    with c1:models=st.multiselect("Modelos para el escenario",MODELS,default=["Ingenuo","Holt amortiguado","ARIMA"],max_selections=4,key=f"models_{frequency}")
    with c2:
        horizon=st.slider("Períodos futuros",1,12 if frequency=="mensual" else 3,1,key=f"horizon_{frequency}")
        window=st.selectbox("Historia de entrenamiento",["total",12,24,36] if frequency=="mensual" else ["total",3,5],key=f"window_{frequency}")
    full=st.checkbox("Mostrar toda la historia en el gráfico",False,key="full_forecast_history")
    request=(bundle.fingerprint,country,product,origin,tuple(models),frequency,variable,horizon,window)
    if st.button("Calcular escenario",type="primary",key="run_forecast",disabled=not models):
        with st.spinner("Reconstruyendo por corte y ajustando modelos…"):
            result=compute(*request,_bundle=bundle)
        st.session_state["forecast_result"]=(request,result)
    saved=st.session_state.get("forecast_result")
    if saved and saved[0]==request:
        pred,details,history=saved[1]
        truth=base.set_index("fecha")[variable+"__original"].reindex(pd.to_datetime(pred.fecha.unique())).dropna()
        chart(forecast_plot(history,pred,unit,truth,recent=None if full else 24 if frequency=="mensual" else 6))
        st.caption(f"Entrenamiento: {len(history)} períodos, {int(history.imputado.sum())} imputados. La vista reciente muestra hasta {24 if frequency=='mensual' else 6} períodos históricos; active toda la historia para inspeccionar los huecos.")
        table(details);table(pred[["fecha","modelo","pronostico","paso","estado"]])
        st.download_button("Descargar escenario con procedencia",csv_bytes(pred),"escenario_agroalerta.csv","text/csv",key="download_forecast")
    else:st.info("Seleccione los modelos y pulse Calcular escenario. Cambiar parámetros invalida el resultado anterior.")
    with st.expander("Por qué una proyección puede verse plana o lineal"):
        st.markdown("**Ingenuo** repite el último precio. **SES** converge al nivel estimado. **Holt amortiguado** reduce la pendiente y ARIMA puede acercarse a un nivel en varios pasos. Una media esperada suave puede coexistir con observaciones futuras variables. No se añade ruido para simular precisión o volatilidad.")
        st.markdown("En V1 se actualizó el entrenamiento en cada corte y se evaluó un paso. Aquí se ajusta una vez y se proyectan varios pasos. Son experimentos distintos. Consulte Resultados V1 para ver la trayectoria real del notebook y su error.")
    st.info("Los escenarios multipaso no tienen intervalos calibrados ni eficacia SAT demostrada a 3 o 6 meses. Los modelos de precio usan sus rezagos; el contexto regional interviene en la imputación, no convierte esos modelos en pronosticadores con variables externas.")
