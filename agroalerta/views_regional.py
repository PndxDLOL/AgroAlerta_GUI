"""Vista regional por producto, independiente del país del panel lateral."""
import numpy as np
import pandas as pd
import streamlit as st
from .regional import product_panel
from .charts import regional_price_plot,regional_vol_plot
from .evidence import csv_bytes

def show_region(monthly,product,start,end,chart,table):
    st.subheader("Un producto, todos sus mercados")
    st.caption("Este panel compara países para el producto elegido. El país del panel lateral no limita esta vista.")
    available=sorted(monthly.loc[monthly.producto.eq(product),"pais"].unique())
    key=f"region_{product}"
    if key in st.session_state and not set(st.session_state[key]).issubset(available):st.session_state.pop(key)
    selected=st.multiselect("Países de la canasta regional",available,default=available,key=key)
    if not selected:st.info("Seleccione al menos un país para comparar precios.");return
    long,wide,original,flags,summary=product_panel(monthly,product,selected)
    visible=long.loc[long.fecha.between(start,end)]
    dates=summary.loc[summary.fecha.between(start,end),"fecha"]
    if dates.empty:st.info("No hay meses en el período elegido.");return
    options=list(dates.dt.strftime("%Y-%m-%d"));key=f"regional_date_{product}"
    if st.session_state.get(key) not in options:st.session_state.pop(key,None)
    date=st.select_slider("Mes para la comparación entre países",options=options,value=options[-1],key=key)
    snap=long.loc[long.fecha.eq(pd.Timestamp(date))].copy()
    snap["estado_precio"]=np.select([snap.precio_usd_nominal_t__original.notna(),snap.precio_usd_nominal_t__usa_imputacion],["Original","Imputado"],default="Faltante")
    view=snap[["pais","precio_usd_nominal_t__original","precio_usd_nominal_t","estado_precio","retorno_usd_pct__original","volatilidad_usd_3m__original"]].rename(columns={
        "pais":"País","precio_usd_nominal_t__original":"USD/t original","precio_usd_nominal_t":"USD/t preparado",
        "estado_precio":"Estado precio","retorno_usd_pct__original":"Retorno USD original (%)","volatilidad_usd_3m__original":"Volatilidad USD original (pp)"})
    table(view,imputed_mask=view["Estado precio"].eq("Imputado"))
    st.caption("Se usa el mismo mes para todos: no se arrastra el último precio de un país a otro período.")
    prepared=st.radio("Precios regionales",["Originales","Serie preparada"],horizontal=True,key="region_series")=="Serie preparada"
    chart(regional_price_plot(visible,prepared))
    with st.expander("Tabla mensual de precios de todos los países"):
        shown=(wide if prepared else original).loc[lambda d:d.index.to_series().between(start,end)].copy()
        mask=flags.reindex(shown.index).reset_index(drop=True)
        mask.insert(0,"fecha",False)
        table(shown.rename_axis("fecha").reset_index(),imputed_mask=mask if prepared else None)
        st.caption("La tabla por mes no sustituye el registro de procedencia: descargue el detalle regional para conservar las marcas de cada valor.")
    visible_summary=summary.loc[summary.fecha.between(start,end)]
    current=summary.loc[summary.fecha.eq(pd.Timestamp(date))].iloc[0]
    c1,c2,c3=st.columns(3)
    c1.metric("Mediana regional original (pp)",f"{current.vol_regional_usd_original_pp:.2f}" if pd.notna(current.vol_regional_usd_original_pp) else "No calculable")
    c2.metric("Cambio frente al mes anterior (pp)",f"{current.variacion_vol_original_pp:+.2f}" if pd.notna(current.variacion_vol_original_pp) else "No calculable")
    c3.metric("Cobertura de volatilidades originales",f"{int(current.volatilidades_originales_disponibles)}/{len(selected)}")
    chart(regional_vol_plot(visible_summary))
    st.info("Indicador descriptivo exploratorio: mediana de las volatilidades nacionales de tres retornos en USD nominales. Se requieren al menos dos países y datos de toda la canasta fija. No es la volatilidad de una cartera ni activa una alerta SAT regional.")
    st.caption("El cambio se calcula en puntos porcentuales solo cuando existen dos meses consecutivos completos. La curva preparada conserva sus imputaciones. El SAT individual sigue usando retornos en moneda local, por lo que su volatilidad puede ser distinta.")
    table(visible_summary)
    left,right=st.columns(2)
    with left:st.download_button("Descargar detalle regional CSV",csv_bytes(visible),f"regional_{product}_detalle.csv","text/csv",key="regional_detail")
    with right:st.download_button("Descargar indicador regional CSV",csv_bytes(visible_summary),f"regional_{product}_indicador.csv","text/csv",key="regional_indicator")
