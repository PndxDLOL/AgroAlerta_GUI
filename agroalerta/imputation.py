"""KNN causal adaptado de las funciones del notebook V1 del equipo.
Los donantes se limitan al origen y el ajuste precede a cada hueco.
No carga ni ejecuta notebooks durante el uso de la aplicación.
"""
import warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.impute import KNNImputer
from .data import KEY as LLAVE, ANNUAL as V_ANUALES
from .indicators import returns as retorno
V_COMERCIO=V_ANUALES[3:]
INICIO=2012  # Origen numérico del tiempo; no restringe el período del archivo.

def preparar_caso(tabla,variable,pais,producto,fechas,frecuencia,apagon=False):
    d=tabla.copy().sort_values(LLAVE+["fecha"]).reset_index(drop=True)
    fecha_inicial=min(fechas)
    consulta=d.pais.eq(pais)&d.producto.eq(producto)&d.fecha.isin(fechas)
    ocultar=consulta.copy()
    if apagon:ocultar=d.producto.eq(producto)&d.fecha.isin(fechas)
    d.loc[ocultar,variable]=np.nan
    train=d.fecha.lt(fecha_inicial)
    usd=d[variable]/d.tasa_lcu_usd if frecuencia=="mensual" else d[variable]
    log=np.log(usd.where(usd.gt(0))) if frecuencia=="mensual" else np.log1p(usd)
    d["log_objetivo"]=log
    centros=d.loc[train].groupby(LLAVE).log_objetivo.mean()
    d["centro"]=pd.MultiIndex.from_frame(d[LLAVE]).map(centros).to_numpy()
    d["z"]=d.log_objetivo-d.centro
    d["r_local"]=d.groupby(LLAVE)[variable].transform(retorno) if frecuencia=="mensual" else np.nan
    d["r_usd"]=d.groupby(LLAVE).log_objetivo.diff()*100
    ultimo=d.groupby(LLAVE).z.transform(lambda s:s.shift(1).ffill())
    ultima_fecha=d.fecha.where(d[variable].notna()).groupby([d.pais,d.producto]).transform(lambda s:s.shift(1).ffill())
    edad=(d.fecha.dt.year-ultima_fecha.dt.year)*12+d.fecha.dt.month-ultima_fecha.dt.month
    x=pd.DataFrame(index=d.index)
    x["ultimo_local"]=ultimo
    x["edad_ultimo"]=edad/(12 if frecuencia=="anual" else 1)
    x["tiempo"]=d.fecha.dt.year-INICIO+(d.fecha.dt.month-1)/12
    x["sin_mes"]=np.sin(2*np.pi*d.fecha.dt.month/12) if frecuencia=="mensual" else 0.
    x["cos_mes"]=np.cos(2*np.pi*d.fecha.dt.month/12) if frecuencia=="mensual" else 0.
    x["retorno_anterior"]=d.groupby(LLAVE).r_local.transform(lambda s:s.shift(1).ffill())
    if frecuencia=="mensual":
        fx=d.groupby(LLAVE).tasa_lcu_usd.transform(retorno)
        x["retorno_divisa"]=fx
        for v in ["produccion_t","area_ha"]+V_COMERCIO:
            x[v+"_log"]=np.log1p(d["ctx_"+v])
    else:
        for v in ["produccion_t","area_ha","rendimiento_t_ha"]:
            if v!=variable:x[v+"_log"]=np.log1p(d[v])

    # Todos los otros mercados, excluyendo explícitamente la respuesta de la fila.
    d["mercado"]=d.pais+" | "+d.producto
    w=d.pivot(index="fecha",columns="mercado",values="z").sort_index(axis=1)
    peer_cols=[]
    for j,mercado in enumerate(w.columns):
        col=f"par_{j:02d}"
        x[col]=w[mercado].reindex(d.fecha).to_numpy()
        x.loc[d.mercado.eq(mercado),col]=np.nan
        peer_cols.append(col)
    x["pares_mediana"]=x[peer_cols].median(axis=1)
    x["pares_dispersion"]=x[peer_cols].std(axis=1)
    x["pares_donantes"]=x[peer_cols].notna().sum(axis=1)
    x["rezago_log"]=d.groupby(LLAVE).z.shift(12 if frecuencia=="mensual" else 1)
    x=pd.concat([x,pd.get_dummies(d[LLAVE],prefix=LLAVE,dtype=float)],axis=1)
    ids=np.flatnonzero(consulta)
    ids=ids[np.argsort(d.loc[ids,"fecha"].to_numpy())]
    conocidos=train&d.z.notna()
    propios=train&d.pais.eq(pais)&d.producto.eq(producto)&d[variable].notna()
    referencia=float(d.loc[propios,"centro"].iloc[0]) if propios.any() else np.nan
    return dict(d=d,x=x,ids=ids,train=conocidos,propios=propios,centro=referencia,
                frecuencia=frecuencia,variable=variable,fechas=fechas,
                cobertura_donantes=float(x.loc[ids,"pares_donantes"].ge(1).mean()))

def knn_v4(c):
    d, x, ids, conocidos = c["d"], c["x"], c["ids"], c["train"]
    n = len(ids)
    if not np.isfinite(c["centro"]) or conocidos.sum() < 8:
        return np.full(n, np.nan), 0
    anteriores = d.fecha.lt(min(c["fechas"]))
    cols = x.columns[x.loc[anteriores].notna().any()]
    y = d.loc[conocidos, "z"].to_numpy()
    sd = max(float(np.std(y)), .05)
    lo, hi = float(y.min() - sd), float(y.max() + sd)
    matriz = pd.concat([d.z.rename("objetivo"), x[cols]], axis=1)
    escala = StandardScaler().fit(matriz.loc[anteriores])
    ent = escala.transform(matriz.loc[anteriores])
    consulta = escala.transform(matriz.loc[ids]); consulta[:, 0] = np.nan
    imp = KNNImputer(n_neighbors=min(5, int(conocidos.sum())), weights="distance", keep_empty_features=True)
    estimado = imp.fit(ent).transform(consulta)[:, 0] * escala.scale_[0] + escala.mean_[0]
    recortes = int(((estimado < lo) | (estimado > hi)).sum())
    estimado = np.clip(estimado, lo, hi)
    if c["frecuencia"] == "mensual":
        pred = np.exp(estimado + c["centro"]) * d.loc[ids, "tasa_lcu_usd"].to_numpy()
    else:
        pred = np.maximum(0, np.expm1(estimado + c["centro"]))
    return pred, recortes

def reconstruct_history(bundle, frequency, variable, country, product, origin,
                        preparation="KNN", hidden_dates=None, annual_lag=2):
    """Reconstruye desde originales. Nunca utiliza el preparado V4 retrospectivo.

    La anualidad rezagada es un supuesto de disponibilidad, no una fecha de
    publicación comprobada. hidden_dates solo se usa en pruebas controladas.
    """
    origin=pd.Timestamp(origin)
    a=bundle.annual[LLAVE+["fecha"]].copy()
    a["anio"]=a.fecha.dt.year
    for v in V_ANUALES:a[v]=bundle.annual[v+"__original"]
    if frequency=="mensual":
        d=bundle.monthly[LLAVE+["fecha","tasa_lcu_usd","precio_lcu_t__original"]].rename(columns={"precio_lcu_t__original":"precio_lcu_t"}).copy()
        ctx=a[LLAVE+["anio"]+V_ANUALES].rename(columns={v:"ctx_"+v for v in V_ANUALES})
        ctx["anio"]+=annual_lag
        d=d.assign(anio=d.fecha.dt.year).merge(ctx,on=LLAVE+["anio"],how="left",validate="many_to_one")
    else:
        d=a.copy()
    d=d.loc[d.fecha.le(origin)].copy()
    market=d.pais.eq(country)&d.producto.eq(product)
    if hidden_dates is not None:
        d.loc[market&d.fecha.isin(hidden_dates),variable]=np.nan
    g=d.loc[market,["fecha",variable]].sort_values("fecha").set_index("fecha")
    original=g[variable].copy()
    filled=original.ffill() if preparation=="Último observado" else original.copy()
    clips=0
    if preparation=="KNN" and len(original):
        nan=original.isna().to_numpy()
        splits=np.r_[0,np.flatnonzero(nan[1:]!=nan[:-1])+1,len(nan)]
        for lo,hi in zip(splits[:-1],splits[1:]):
            if not nan[lo]:continue
            dates=list(original.index[lo:hi])
            case=preparar_caso(d,variable,country,product,dates,frequency)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore",RuntimeWarning)
                values,nclips=knn_v4(case)
            filled.loc[dates]=values;clips+=nclips
    assert np.allclose(original.dropna(),filled.loc[original.notna()],equal_nan=True)
    result=pd.DataFrame({"original":original,"valor":filled,
                         "imputado":original.isna()&filled.notna()})
    result.attrs.update(origen=str(origin.date()),recortes=clips,preparacion=preparation,
                        fuente_maxima=str(d.fecha.max().date()) if len(d) else None,
                        rezago_anual_supuesto=annual_lag)
    return result
