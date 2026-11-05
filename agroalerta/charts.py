"""Gráficas con leyenda textual, símbolos y resaltado de las imputaciones."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

GREEN="#1c6650";AMBER="#d98623";INK="#183f35";BLUE="#457f9d"

def base(fig,title,ylabel=""):
    fig.update_layout(title=dict(text=title,font=dict(size=17,color=INK)),height=390,
        paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#ffffff",margin=dict(l=15,r=15,t=52,b=20),
        font=dict(family="Arial",size=12,color=INK),legend=dict(orientation="h",y=1.03,x=0),
        hovermode="x unified",yaxis_title=ylabel,xaxis_title=None)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#e8efea",zerolinecolor="#e8efea")
    return fig

def timeline(d,field,title,unit):
    original=field+"__original";flag=field+"__usa_imputacion"
    f=go.Figure()
    f.add_trace(go.Scatter(x=d.fecha,y=d[field],mode="lines",line=dict(color="#9cafaa",width=1.5),name="Serie preparada",connectgaps=False))
    if original in d:
        f.add_trace(go.Scatter(x=d.fecha,y=d[original],mode="lines+markers",line=dict(color=GREEN,width=2),marker=dict(size=4),name="Original",connectgaps=False))
    if flag in d:
        selected=d.loc[d[flag].fillna(False)]
        f.add_trace(go.Scatter(x=selected.fecha,y=selected[field],mode="markers",marker=dict(color=AMBER,size=8,symbol="diamond"),name="Imputado / usa imputación"))
    return base(f,title,unit)

def forecast_plot(history,predictions,unit,truth=None,recent=24):
    history=history.tail(recent) if recent else history
    f=go.Figure()
    f.add_trace(go.Scatter(x=history.index,y=history.valor,mode="lines",line=dict(color="#9cafaa"),name="Historia preparada"))
    f.add_trace(go.Scatter(x=history.index,y=history.original,mode="lines+markers",line=dict(color=GREEN),marker=dict(size=4),name="Original de entrenamiento",connectgaps=False))
    g=history.loc[history.imputado]
    f.add_trace(go.Scatter(x=g.index,y=g.valor,mode="markers",marker=dict(color=AMBER,size=8,symbol="diamond"),name="Imputado dentro del corte"))
    for model,g in predictions.groupby("modelo",sort=False):
        f.add_trace(go.Scatter(x=g.fecha,y=g.pronostico,mode="lines+markers",line=dict(dash="dash"),name=model))
    if truth is not None and len(truth):
        f.add_trace(go.Scatter(x=truth.index,y=truth,mode="markers",marker=dict(symbol="x",size=9,color="#3d5a70"),name="Original posterior retenido"))
    return base(f,"Escenario posterior al origen seleccionado",unit)

def registered_plot(predictions,unit):
    f=go.Figure()
    if predictions.empty:return base(f,"Sin predicciones V1 elegibles",unit)
    truth=predictions.drop_duplicates("fecha").sort_values("fecha")
    f.add_trace(go.Scatter(x=truth.fecha,y=truth.observado,mode="lines+markers",line=dict(color=GREEN,width=3),name="Original observado"))
    for model,g in predictions.groupby("modelo",sort=False):
        f.add_trace(go.Scatter(x=g.fecha,y=g.pronostico,mode="lines+markers",line=dict(dash="dash",width=2),name=model))
    return base(f,"V1: un pronóstico por mes o año, con origen anterior",unit)

def regional_price_plot(long,prepared=False):
    f=go.Figure();field="precio_usd_nominal_t" if prepared else "precio_usd_nominal_t__original"
    for country,g in long.groupby("pais"):
        f.add_trace(go.Scatter(x=g.fecha,y=g[field],mode="lines",name=country,connectgaps=False))
        if prepared:
            imputed=g.loc[g.precio_usd_nominal_t__usa_imputacion]
            f.add_trace(go.Scatter(x=imputed.fecha,y=imputed[field],mode="markers",name=country+" · imputado",marker=dict(color=AMBER,symbol="diamond",size=8)))
    return base(f,"Precios del mismo producto entre países","USD nominales/t")

def regional_vol_plot(summary):
    f=go.Figure()
    f.add_trace(go.Scatter(x=summary.fecha,y=summary.vol_regional_usd_original_pp,name="Mediana regional desde originales",line=dict(color=GREEN,width=3),connectgaps=False))
    f.add_trace(go.Scatter(x=summary.fecha,y=summary.vol_regional_usd_preparada_pp,name="Mediana regional preparada",line=dict(color="#9cafaa",dash="dot"),connectgaps=False))
    g=summary.loc[summary.vol_regional_usa_imputacion]
    f.add_trace(go.Scatter(x=g.fecha,y=g.vol_regional_usd_preparada_pp,mode="markers",name="Usa imputación",marker=dict(color=AMBER,symbol="diamond",size=7)))
    return base(f,"Volatilidad por producto en una canasta fija de países","Puntos porcentuales de retornos USD")

def synthetic_plot(series):
    return base(go.Figure(go.Scatter(x=series.index,y=series,name="Historia sintética",line=dict(color=GREEN))),"Prueba artificial de la regla","Unidades sintéticas")

def sat_plot(signals):
    f=go.Figure()
    f.add_trace(go.Scatter(x=signals.fecha,y=signals.volatilidad_original,name="Volatilidad original",line=dict(color=GREEN),connectgaps=False))
    for col,name,color in [("umbral_vigilancia","Percentil 75",AMBER),("umbral_alta","Percentil 90","#b85749")]:
        f.add_trace(go.Scatter(x=signals.fecha,y=signals[col],name=name,line=dict(color=color,dash="dot")))
    g=signals.loc[signals.estado.eq("Volatilidad alta")]
    f.add_trace(go.Scatter(x=g.fecha,y=g.volatilidad_original,name="Episodio observado alto",mode="markers",marker=dict(symbol="diamond",size=9,color="#b85749")))
    return base(f,"Señales históricas con umbrales calculados con información anterior","Puntos porcentuales")

def correlation_plot(monthly):
    x=monthly.copy();x["mercado"]=x.pais+" · "+x.producto
    x["usd_original"]=x.precio_lcu_t__original/x.tasa_lcu_usd
    panel=x.pivot(index="fecha",columns="mercado",values="usd_original")
    corr=panel.corr(min_periods=12);counts=panel.notna().astype(int).T.dot(panel.notna().astype(int))
    f=go.Figure(go.Heatmap(z=corr.to_numpy(),x=corr.columns,y=corr.index,zmin=-1,zmax=1,
        colorscale="RdBu_r",text=np.round(corr.to_numpy(),2),texttemplate="%{text:.2f}",
        hovertemplate="%{y}<br>%{x}<br>Correlación: %{z:.3f}<extra></extra>"))
    base(f,"Correlación de precios originales en USD nominales")
    f.update_layout(height=max(420,len(corr)*45),hovermode="closest")
    return f,counts
