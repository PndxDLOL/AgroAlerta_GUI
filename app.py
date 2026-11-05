"""Ejecutar: python -m streamlit run app.py"""
from pathlib import Path
from io import BytesIO
import html,json
import numpy as np
import pandas as pd
import streamlit as st
from agroalerta import __version__
from agroalerta.data import load_bytes,read_directory,resolve_directory,DataError,quality,KEY,ANNUAL
from agroalerta.indicators import KPI,monthly_indicators,annual_indicators,descriptive,streaks
from agroalerta.models import MODELS,forecast
from agroalerta.alerts import Rules,historical_signals,forecast_signal,raw_market,evaluate_predictions,compare_common,contextual_rules,synthetic_case,default_cutoff
from agroalerta.charts import timeline,forecast_plot,sat_plot,correlation_plot
from agroalerta.evidence import evidence_zip,csv_bytes,recalculate_backtest
from agroalerta.textio import read_utf8
from agroalerta.appearance import css,palette,theme_figure
from agroalerta.views_regional import show_region
from agroalerta.views_forecast import show_forecasts
from agroalerta.views_help import download_guides,show_help
from agroalerta.charts import synthetic_plot

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title="AgroAlerta · Piloto SAT",page_icon="🌱",layout="wide")
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode="oscuro" if st.query_params.get("tema")=="oscuro" else "claro"

def toggle_theme():
    st.session_state.theme_mode="claro" if st.session_state.theme_mode=="oscuro" else "oscuro"
    st.query_params["tema"]=st.session_state.theme_mode

with st.sidebar:
    st.markdown("### AgroAlerta")
    st.caption("Monitoreo agrícola · interfaz V2")
    st.button("Cambiar a modo oscuro" if st.session_state.theme_mode=="claro" else "Cambiar a modo claro",on_click=toggle_theme,key="toggle_theme")
    with st.expander("Instructivo y plantillas"):
        download_guides(ROOT)
st.markdown(css(st.session_state.theme_mode),unsafe_allow_html=True)

def chart(fig):
    st.plotly_chart(theme_figure(fig,st.session_state.theme_mode),width="stretch",theme=None)

def table(frame,imputed_mask=None,**kwargs):
    p=palette(st.session_state.theme_mode)
    if isinstance(frame,pd.DataFrame):
        style=frame.style.set_properties(**{"background-color":p["panel"],"color":p["text"]})
        if imputed_mask is not None:
            paint=pd.DataFrame("",index=frame.index,columns=frame.columns)
            color="background-color:#ffe2ad;color:#703e00;font-weight:600" if st.session_state.theme_mode=="claro" else "background-color:#5b401d;color:#ffdda4;font-weight:600"
            if isinstance(imputed_mask,pd.Series):paint.loc[imputed_mask]=color
            else:paint=paint.mask(imputed_mask,color)
            style=style.apply(lambda _:paint,axis=None)
        frame=style
    st.dataframe(frame,hide_index=True,width="stretch",**kwargs)

def fmt(x,digits=2):
    if not np.isfinite(x):return "No calculable"
    if abs(x)>=1e6:return f"{x/1e6:,.2f} M".replace(",","_").replace(".",",").replace("_",".")
    return f"{x:,.{digits}f}".replace(",","_").replace(".",",").replace("_",".")

@st.cache_data(max_entries=4,show_spinner=False)
def cached_bundle(month,year,extras,label):return load_bytes(month,year,extras,label)

@st.cache_data(max_entries=16,show_spinner=False)
def cached_forecast(fingerprint,country,product,origin,models,frequency,variable,horizon,window,_bundle):
    return forecast(_bundle,country,product,origin,list(models),frequency,variable,horizon,window)

@st.cache_data(max_entries=4,show_spinner=False)
def cached_evaluation(fingerprint,rules_dict,_bundle):
    return evaluate_predictions(_bundle,rules=Rules(**rules_dict))

with st.sidebar:
    source=st.selectbox("Fuente de datos",["Carpeta configurada","Cargar dos CSV"],key="source")
    try:
        if source=="Cargar dos CSV":
            fm=st.file_uploader("Base mensual V4",type="csv",key="upload_m")
            fa=st.file_uploader("Base anual V4",type="csv",key="upload_a")
            if not fm or not fa:
                st.info("Cargue ambas bases V4 con sus columnas originales y marcas de imputación.");st.stop()
            bundle=cached_bundle(fm.getvalue(),fa.getvalue(),{},"Archivos cargados")
        else:
            directory=resolve_directory(ROOT);mraw,araw,extras=read_directory(directory)
            bundle=cached_bundle(mraw,araw,extras,"Piloto incluido" if directory.name=="demo" else "Carpeta actualizada")
    except (DataError,ValueError,OSError) as exc:
        st.error(str(exc));st.stop()
    if st.button("Actualizar lectura",key="refresh"):
        st.cache_data.clear();st.rerun()
    st.divider()
    countries=sorted(bundle.monthly.pais.unique())
    if st.session_state.get("country") not in countries:st.session_state.pop("country",None)
    country=st.selectbox("País",countries,key="country")
    products=sorted(bundle.monthly.loc[bundle.monthly.pais.eq(country),"producto"].unique())
    if st.session_state.get("product") not in products:st.session_state.pop("product",None)
    product=st.selectbox("Producto",products,key="product")
    if st.session_state.get("dates_fp")!=bundle.fingerprint:
        for key in list(st.session_state):
            if key=="period" or key.startswith(("origin_","sat_origin_","region_","regional_date_")):
                st.session_state.pop(key,None)
        st.session_state["dates_fp"]=bundle.fingerprint
    period=st.date_input("Período descriptivo",value=(bundle.monthly.fecha.min().date(),bundle.monthly.fecha.max().date()),
                        min_value=bundle.monthly.fecha.min().date(),max_value=bundle.monthly.fecha.max().date(),key="period")
    st.caption("Los colores naranja y los rombos identifican estimaciones o indicadores que las usan.")
    st.caption(f"Versión {__version__} · {bundle.label}")

rules_data=json.loads(read_utf8(ROOT/"config/reglas.json"))
rules=Rules(**rules_data["reglas"])
monthly=monthly_indicators(bundle.monthly);annual=annual_indicators(bundle.annual)
market=monthly.loc[monthly.pais.eq(country)&monthly.producto.eq(product)].copy()
year_market=annual.loc[annual.pais.eq(country)&annual.producto.eq(product)].copy()
if isinstance(period,(tuple,list)) and len(period)==2:
    start,end=map(pd.Timestamp,period)
else:
    st.info("Seleccione las dos fechas del período.");st.stop()
visible=market.loc[market.fecha.between(start,end)]
years=year_market.loc[year_market.fecha.dt.year.between(start.year,end.year)]
if visible.empty:st.warning("No hay registros para los filtros seleccionados.");st.stop()
st.markdown('<div class="eyebrow">OBSERVATORIO AGRÍCOLA / PILOTO 02</div>',unsafe_allow_html=True)
st.title("AgroAlerta")
st.markdown('<div class="intro">Monitoreo regional, procedencia de los datos y escenarios de precios.</div>',unsafe_allow_html=True)
st.markdown(f'<span class="pill">{html.escape(country)} · {html.escape(product)}</span><span class="pill">Corte observado: {bundle.monthly.fecha.max():%Y-%m}</span><span class="pill">SAT experimental</span>',unsafe_allow_html=True)
for warning in bundle.warnings:st.warning(warning)
page=st.radio("Explorar",["Panorama","Comparación regional","Calidad e imputación","Modelos y escenarios","SAT y evaluación","Trazabilidad","Ayuda y mejoras V2"],horizontal=True,key="page",label_visibility="collapsed")

def flagged_table(frame,fields):
    fields=[v for v in fields if v in frame]
    view=frame[["fecha"]+fields].copy()
    styles=pd.DataFrame("",index=view.index,columns=view.columns)
    for v in fields:
        flag=v+"__usa_imputacion" if v+"__usa_imputacion" in frame else v+"__imputado"
        if flag in frame:styles.loc[frame[flag].fillna(False),v]="background-color:#ffe2ad;color:#703e00;font-weight:600"
    p=palette(st.session_state.theme_mode)
    table(view.style.set_properties(**{"background-color":p["panel"],"color":p["text"]}).apply(lambda _:styles,axis=None))

def metrics_table(metrics):
    labels={"modelo":"Modelo","N":"Casos","eventos":"Eventos","precision":"Precisión",
        "sensibilidad":"Sensibilidad","falsas_alarmas_entre_alertas":"Falsas alarmas",
        "tasa_falsos_positivos":"FPR","omisiones":"Omisión"}
    view=metrics.rename(columns=labels)
    config={v:st.column_config.NumberColumn(format="%.3f") for v in ["Precisión","Sensibilidad","F1","Falsas alarmas","FPR","Omisión"]}
    config["Modelo"]=st.column_config.TextColumn(width="medium")
    table(view,column_config=config)

if page=="Panorama":
    st.subheader("Diez indicadores para leer el mercado")
    latest=visible.iloc[-1];latest_year=years.iloc[-1] if len(years) else None
    for row in [KPI[:5],KPI[5:]]:
        cols=st.columns(5)
        for col,(field,label,unit,freq) in zip(cols,row):
            item=latest if freq=="mensual" else latest_year
            value=float(item[field]) if item is not None else np.nan
            flag=bool(item.get(field+"__usa_imputacion",False)) if item is not None else False
            with col:
                st.metric(label,fmt(value));st.caption(unit)
                stamp=f"{item.fecha:%Y-%m}" if freq=="mensual" and item is not None else str(item.fecha.year) if item is not None else "Sin año"
                st.caption(f"🟠 Usa imputación · {stamp}" if flag else f"Original / calculado desde originales · {stamp}" if np.isfinite(value) else "Sin datos suficientes")
    st.caption("KPI anuales: vista descriptiva del último año del filtro. Las reglas SAT usan un contexto rezagado distinto, explícito en su panel. Oferta y exposiciones son candidatas; falta verificar equivalencia física, especialmente en arroz.")
    unit=st.radio("Unidad del precio",["Moneda local","USD nominales"],horizontal=True,key="price_unit")
    field="precio_lcu_t" if unit=="Moneda local" else "precio_usd_nominal_t"
    chart(timeline(visible,field,"Trayectoria mensual del precio",unit+" / t"))
    left,right=st.columns(2)
    with left:chart(timeline(visible,"retorno_log_pct","Retorno logarítmico","% log"))
    with right:chart(timeline(visible,"volatilidad_3m","Volatilidad de tres retornos","Puntos porcentuales"))
    st.subheader("Contexto productivo y comercial anual")
    options={**{name:(field,unit) for field,name,unit,f in KPI if f=="anual"},"Importaciones (t)":("importaciones_t","t"),"Exportaciones (t)":("exportaciones_t","t"),"Importaciones (USD)":("importaciones_usd","USD"),"Exportaciones (USD)":("exportaciones_usd","USD")}
    chosen=st.selectbox("Indicador anual",list(options),key="annual_indicator")
    field,unit=options[chosen]
    if len(years):chart(timeline(years,field,chosen,unit))
    flagged_table(visible,["precio_lcu_t","precio_usd_nominal_t","retorno_log_pct","volatilidad_3m"])

elif page=="Calidad e imputación":
    q=quality(bundle);cols=st.columns(4)
    for col,label,value in zip(cols,["Precios originales","Precios imputados","Celdas anuales ausentes originales","Ausencia global de base"],[str(q["precios_originales"]),str(q["precios_imputados"]),str(q["faltantes_anuales"]),fmt(q["porcentaje_global"])+" %"]):col.metric(label,value)
    st.caption(f"Global: {q['faltantes_base']} / {q['celdas_base']} celdas, contando divisa una vez por país-mes y anual una vez por año. Sin divisa: {q['porcentaje_agricola']:.2f} %. El criterio de 20 % del proyecto no garantiza la recuperación de huecos largos.")
    gaps=streaks(market.set_index("fecha").precio_lcu_t__original)
    st.subheader("Huecos originales del mercado")
    table(pd.DataFrame(gaps,columns=["Inicio","Fin","Meses"]))
    chart(timeline(visible,"precio_lcu_t","Original y reconstruido, conservados por separado","LCU/t"))
    table(descriptive(visible,["precio_lcu_t","retorno_log_pct","volatilidad_3m"]))
    st.subheader("Registros con procedencia")
    flagged_table(visible,["precio_lcu_t","precio_usd_nominal_t","retorno_log_pct","volatilidad_3m"])
    if len(years):flagged_table(years,ANNUAL)
    with st.expander("Comparación regional de precios originales en USD"):
        fig,counts=correlation_plot(monthly);chart(fig)
        st.caption("Todos los países-productos juntos, usando meses originales coincidentes por par. El color es correlación, no alerta; no decide la agrupación ni el método de imputación.")
        table(counts.rename_axis("mercado").reset_index())

elif page=="Comparación regional":
    show_region(monthly,product,start,end,chart,table)

elif page=="Modelos y escenarios":
    show_forecasts(bundle,country,product,market,year_market,chart,table,cached_forecast)

elif page=="SAT y evaluación":
    st.subheader("Señal experimental del próximo mes")
    origin=st.select_slider("Corte de información del SAT",options=list(market.fecha.dt.strftime("%Y-%m-%d")),value=market.fecha.max().strftime("%Y-%m-%d"),key=f"sat_origin_{country}_{product}")
    sat_models=st.multiselect("Modelos de la señal",["Ingenuo","Holt amortiguado","ARIMA","Holt-Winters","Ridge AR"],default=["Ingenuo","ARIMA"],max_selections=3,key="sat_models")
    with st.spinner("Calculando la señal con información hasta el corte…"):
        pred,details,hist=cached_forecast(bundle.fingerprint,country,product,origin,tuple(sat_models),"mensual","precio_lcu_t",1,"total",_bundle=bundle)
    raw=raw_market(bundle,country,product);signals=[]
    for row in pred.to_dict("records"):
        sig=forecast_signal(raw,origin,row["pronostico"],rules)
        sig.update(modelo=row["modelo"],precio_previsto_lcu_t=row["pronostico"],imputadas_historia=int(hist.imputado.sum()))
        signals.append(sig)
    table(pd.DataFrame(signals))
    st.caption("R1: volatilidad implícita del retorno previsto y dos retornos anteriores, comparada con percentiles de historia original. Sin tres precios recientes originales o calibración suficiente, la señal es No evaluable. No clasifica crisis alimentaria.")
    st.caption(f"La historia de entrenamiento contiene {int(hist.imputado.sum())} precios imputados dentro del corte; las entradas recientes y los umbrales de R1 proceden de originales.")
    table(contextual_rules(bundle,country,product,origin,rules,rules_data.get("comparabilidad",{})))
    st.caption(f"Contexto anual SAT: hasta año del origen menos {rules.annual_lag}. Es un supuesto de disponibilidad, pendiente de verificar con fechas de publicación. Las exposiciones comerciales no activan reglas sin equivalencia física documentada.")
    historical=historical_signals(bundle,country,product,rules)
    chart(sat_plot(historical))
    with st.expander("Episodios observados y cortes no evaluables"):
        table(historical.loc[historical.estado.ne("Sin señal estadística")])
    st.subheader("Falsas alarmas y omisiones en datos originales")
    if len(bundle.predictions):
        with st.spinner("Contrastando señales con episodios originales…"):
            evaluation=cached_evaluation(bundle.fingerprint,rules.to_dict(),_bundle=bundle)
        scope=st.radio("Ámbito de evaluación",["Todos los mercados","Mercado seleccionado"],horizontal=True,key="eval_scope")
        if scope=="Mercado seleccionado":evaluation=evaluation.loc[evaluation.pais.eq(country)&evaluation.producto.eq(product)]
        available=sorted(evaluation.modelo.unique())
        chosen=st.multiselect("Modelos para comparar en casos comunes",available,default=[x for x in ["Ingenuo","Holt-Winters","ARIMA"] if x in available],key="eval_models")
        stage=st.selectbox("Etapa",["prueba","validacion"],key="eval_stage")
        metrics,common=compare_common(evaluation,chosen,stage)
        metrics_table(metrics)
        st.caption(f"Calibración fija de prueba: {default_cutoff(bundle,rules):%Y-%m}. Casos comunes entre modelos seleccionados y persistencia. N es conteo; precisión, sensibilidad y F1 son proporciones. No calculable se muestra vacío. Estos resultados son exploratorios; 2023–2024 ya se había examinado en V1.")
        with st.expander("Casos evaluados y exclusiones"):
            table(evaluation)
        st.download_button("Descargar evaluación de alertas",csv_bytes(evaluation),"evaluacion_alertas.csv","text/csv")
    else:
        st.info("No hay predicciones vinculadas a estas bases. Puede generar un nuevo ensayo de tres modelos y un paso; no reemplaza el notebook V1.")
        if st.button("Recalcular prueba con bases actuales",key="new_backtest"):
            with st.spinner("Ejecutando cortes cronológicos; puede tardar unos minutos…"):
                new=recalculate_backtest(bundle,rules=rules)
                ev=evaluate_predictions(bundle,new,rules);mt,_=compare_common(ev,["Ingenuo","Holt amortiguado","ARIMA"])
            metrics_table(mt)
            st.download_button("Descargar nuevo ensayo",csv_bytes(new),"nuevo_ensayo_streamlit.csv","text/csv")
    with st.expander("Laboratorio de pruebas sintéticas",expanded=False):
        st.caption("Entradas artificiales para demostrar la regla. No se mezclan con los mercados ni con las métricas anteriores.")
        case=st.selectbox("Escenario de prueba",["Estabilidad","Choque +30 %","Corte de tres meses"],key="synthetic")
        synthetic,candidate,sig=synthetic_case(case,rules)
        st.write(f"Resultado esperado de la regla: **{sig['estado']}**")
        table(pd.DataFrame([sig]))
        chart(synthetic_plot(synthetic))
        st.caption(f"Precio hipotético de prueba: {candidate:.2f}. No es un pronóstico generado por un modelo.")

elif page=="Trazabilidad":
    st.subheader("Datos, reglas y reproducción")
    st.write("La aplicación recalcula los KPI desde las medidas base y conserva los originales. Una modificación en las bases o en los resultados cambia la huella de lectura e invalida la caché.")
    table(pd.DataFrame([dict(archivo=k,sha256=v) for k,v in bundle.hashes.items()]))
    st.json(rules_data)
    st.markdown(read_utf8(ROOT/"docs/REGLAS_Y_KPI.md"))
    st.download_button("Descargar base mensual filtrada",csv_bytes(visible),"base_mensual_filtrada.csv","text/csv")
    st.download_button("Descargar base anual filtrada",csv_bytes(years),"base_anual_filtrada.csv","text/csv")
    if st.button("Preparar paquete de evidencias",key="evidence"):
        with st.spinner("Reuniendo indicadores, señales, métricas y configuración…"):
            archive=evidence_zip(bundle,rules)
        st.download_button("Descargar evidencias actuales",archive,"agroalerta_evidencias.zip","application/zip")
elif page=="Ayuda y mejoras V2":
    show_help(ROOT)
st.divider()
st.caption("AgroAlerta · proyecto de aula de Ingeniería en Ciencia de Datos · fuentes FAOSTAT y Banco Mundial. Las estimaciones se conservan como estimaciones. Los indicadores de mercado no equivalen a diagnósticos de inseguridad alimentaria.")
