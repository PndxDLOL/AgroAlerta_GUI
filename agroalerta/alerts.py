"""Reglas SAT V1. Señales experimentales, nunca etiquetas de crisis alimentaria."""
from dataclasses import dataclass,asdict
import numpy as np
import pandas as pd
from .indicators import volatility,returns,annual_indicators

@dataclass(frozen=True)
class Rules:
    q_high: float=.90
    q_watch: float=.75
    min_vols: int=24
    test_months: int=24
    annual_lag: int=2
    production_drop: float=-10.
    local_coverage_warning: float=80.

    def __post_init__(self):
        if not 0<self.q_watch<self.q_high<1:raise ValueError("Los percentiles deben cumplir 0 < vigilancia < alta < 1.")
        if self.min_vols<4 or self.test_months<1 or self.annual_lag<0:raise ValueError("Reglas de historia o rezago inválidas.")

    def to_dict(self):return asdict(self)

def default_cutoff(bundle,rules):
    return bundle.monthly.fecha.max()-pd.DateOffset(months=rules.test_months)

def raw_market(bundle,country,product):
    g=bundle.monthly.loc[bundle.monthly.pais.eq(country)&bundle.monthly.producto.eq(product)]
    return g.sort_values("fecha").set_index("fecha").precio_lcu_t__original

def thresholds(raw,cutoff,rules):
    sigma=volatility(raw.loc[raw.index<=pd.Timestamp(cutoff)]).dropna()
    if len(sigma)<rules.min_vols:
        return np.nan,np.nan,len(sigma)
    return float(sigma.quantile(rules.q_watch)),float(sigma.quantile(rules.q_high)),len(sigma)

def level(value,watch,high):
    if not np.isfinite([value,watch,high]).all():return "No evaluable"
    if value>high:return "Volatilidad alta"
    if value>watch:return "Vigilancia"
    return "Sin señal estadística"

def forecast_signal(raw,origin,price,rules,calibration_end=None):
    """R1: desviación del retorno previsto y los dos retornos previos originales."""
    origin=pd.Timestamp(origin);limit=min(origin,pd.Timestamp(calibration_end)) if calibration_end is not None else origin
    watch,high,n=thresholds(raw,limit,rules)
    prior=raw.reindex(pd.date_range(origin-pd.DateOffset(months=2),origin,freq="MS"))
    result=dict(estado="No evaluable",motivo="",volatilidad_prevista=np.nan,umbral_alta=high,
                umbral_vigilancia=watch,n_calibracion=n,calibracion_fin=limit,
                origen=origin,fecha=origin+pd.offsets.MonthBegin(1))
    if n<rules.min_vols:
        result["motivo"]=f"Solo hay {n} volatilidades originales; se requieren {rules.min_vols}.";return result
    if prior.isna().any() or prior.le(0).any():
        result["motivo"]="Los tres precios recientes necesarios no son originales positivos y consecutivos.";return result
    if not np.isfinite(price) or price<=0:
        result["motivo"]="El pronóstico no es positivo y finito.";return result
    sequence=pd.Series([*prior.to_numpy(),price])
    sigma=float(volatility(sequence).iloc[-1])
    result.update(estado=level(sigma,watch,high),volatilidad_prevista=sigma)
    return result

def historical_signals(bundle,country,product,rules):
    raw=raw_market(bundle,country,product);sig=volatility(raw);rows=[]
    for date,value in sig.items():
        cutoff=date-pd.offsets.MonthBegin(1)
        watch,high,n=thresholds(raw,cutoff,rules)
        state=level(value,watch,high)
        reason="" if state!="No evaluable" else ("Sin cuatro precios originales consecutivos." if not np.isfinite(value) else "Calibración original insuficiente.")
        rows.append(dict(pais=country,producto=product,fecha=date,volatilidad_original=value,
            umbral_vigilancia=watch,umbral_alta=high,n_calibracion=n,estado=state,motivo=reason,
            tipo="Detección histórica, no anticipación"))
    return pd.DataFrame(rows)

def evaluate_predictions(bundle,predictions=None,rules=None,calibration_end=None):
    """Usa solo objetivos originales y cinco precios para comparar con persistencia.

    La etiqueta necesita cuatro precios; el quinto permite medir s_t como referencia.
    Cada fila conserva el motivo de exclusión y no se rellena una verdad ausente.
    """
    rules=rules or Rules();cutoff=pd.Timestamp(calibration_end) if calibration_end is not None else default_cutoff(bundle,rules)
    p=bundle.predictions if predictions is None else predictions
    if p.empty:return pd.DataFrame()
    p=p.loc[p.frecuencia.eq("mensual")&p.variable.eq("precio_lcu_t")].copy()
    if "ventana" in p:p=p.loc[p.ventana.astype(str).eq("total")]
    if "preparacion" in p:
        p=p.loc[p.preparacion.isin(["KNN V4 por corte","KNN","KNN por corte · Streamlit"])]
    p=p.drop_duplicates(["pais","producto","fecha","modelo"])
    markets={(c,pr):raw_market(bundle,c,pr) for c,pr in p[["pais","producto"]].drop_duplicates().itertuples(index=False,name=None)}
    rows=[]
    for row in p.to_dict("records"):
        raw=markets[(row["pais"],row["producto"])];date=pd.Timestamp(row["fecha"]);origin=pd.Timestamp(row["origen"])
        stage="prueba" if date>cutoff else "validacion"
        signal=forecast_signal(raw,origin,float(row["pronostico"]),rules,cutoff if stage=="prueba" else origin)
        last=raw.reindex(pd.date_range(date-pd.DateOffset(months=4),date,freq="MS"))
        reason=signal["motivo"]
        if date!=origin+pd.offsets.MonthBegin(1):reason="No es un pronóstico mensual de un paso."
        if last.isna().any() or last.le(0).any():reason="Comparación común: se requieren cinco precios originales positivos consecutivos."
        if "observado" in row and np.isfinite(row["observado"]):
            truth=raw.get(date,np.nan)
            if not np.isclose(truth,row["observado"],rtol=1e-8,atol=1e-6,equal_nan=False):reason="El objetivo del archivo predictivo no coincide con el original actual."
        eligible=not reason and signal["estado"]!="No evaluable"
        true_sigma=float(volatility(last).iloc[-1]) if eligible else np.nan
        baseline_sigma=float(volatility(last.iloc[:-1]).iloc[-1]) if eligible else np.nan
        rows.append(dict(pais=row["pais"],producto=row["producto"],fecha=date,origen=origin,
            modelo=row["modelo"],etapa=stage,evaluable=eligible,motivo=reason,
            volatilidad_observada=true_sigma,volatilidad_prevista=signal["volatilidad_prevista"],
            volatilidad_persistencia=baseline_sigma,umbral=signal["umbral_alta"],
            evento_real=int(true_sigma>signal["umbral_alta"]) if eligible else np.nan,
            alerta_modelo=int(signal["volatilidad_prevista"]>signal["umbral_alta"]) if eligible else np.nan,
            alerta_persistencia=int(baseline_sigma>signal["umbral_alta"]) if eligible else np.nan,
            n_calibracion=signal["n_calibracion"],calibracion_fin=signal["calibracion_fin"],
            imputadas_historia=row.get("imputadas",np.nan),tipo="Evaluación retrospectiva exploratoria"))
    return pd.DataFrame(rows)

def confusion(truth,signal):
    y=np.asarray(truth,dtype=int);a=np.asarray(signal,dtype=int)
    tp=int(((y==1)&(a==1)).sum());fp=int(((y==0)&(a==1)).sum())
    fn=int(((y==1)&(a==0)).sum());tn=int(((y==0)&(a==0)).sum())
    def divide(x,n):return x/n if n else np.nan
    return dict(N=len(y),eventos=int(y.sum()),TP=tp,FP=fp,FN=fn,TN=tn,
        precision=divide(tp,tp+fp),sensibilidad=divide(tp,tp+fn),F1=divide(2*tp,2*tp+fp+fn),
        falsas_alarmas_entre_alertas=divide(fp,tp+fp),tasa_falsos_positivos=divide(fp,fp+tn),
        omisiones=divide(fn,tp+fn))

def compare_common(evaluation,models,stage="prueba"):
    if evaluation.empty or not models:return pd.DataFrame(),pd.DataFrame()
    d=evaluation.loc[evaluation.etapa.eq(stage)&evaluation.modelo.isin(models)].copy()
    keys=["pais","producto","fecha"]
    valid=d.loc[d.evaluable]
    counts=valid.groupby(keys).modelo.nunique()
    common=counts[counts.eq(len(models))].index
    valid=valid.loc[pd.MultiIndex.from_frame(valid[keys]).isin(common)]
    rows=[]
    for model,g in valid.groupby("modelo"):
        rows.append(dict(modelo=model,**confusion(g.evento_real,g.alerta_modelo)))
    if len(valid):
        baseline=valid.drop_duplicates(keys)
        rows.append(dict(modelo="Persistencia de volatilidad",**confusion(baseline.evento_real,baseline.alerta_persistencia)))
    return pd.DataFrame(rows),valid

def contextual_rules(bundle,country,product,origin,rules,comparability=None):
    """R2–R4: contexto, sin alterar el evento mensual ni usar anualidades futuras."""
    a=annual_indicators(bundle.annual)
    d=a.loc[a.pais.eq(country)&a.producto.eq(product)&a.fecha.dt.year.le(pd.Timestamp(origin).year-rules.annual_lag)]
    rows=[]
    raw=raw_market(bundle,country,product).loc[lambda s:s.index<=pd.Timestamp(origin)].tail(12)
    coverage=100*raw.notna().mean() if len(raw) else np.nan
    rows.append(dict(regla="R5 Cobertura original reciente",estado="Revisar calidad" if coverage<rules.local_coverage_warning else "Sin disparo",detalle=f"Últimos {len(raw)} meses: {coverage:.1f} % originales. Control local de calidad, distinto del 20 % global de imputación."))
    if d.empty:return pd.DataFrame(rows+[dict(regla="R2 Contexto productivo",estado="No evaluable",detalle="No hay anualidad compatible con el rezago supuesto.")])
    x=d.iloc[-1];year=int(x.fecha.year)
    change=x.crecimiento_produccion_pct__original
    rows.append(dict(regla="R2 Caída de producción",estado="Vigilancia contextual" if np.isfinite(change) and change<rules.production_drop else "Sin disparo" if np.isfinite(change) else "No evaluable",detalle=f"Año {year}; variación original {change:.2f} %. Umbral operativo {rules.production_drop} %."))
    item=(comparability or {}).get(country+"|"+product,{})
    verified=item.get("validada") is True and isinstance(item.get("evidencia"),str) and bool(item["evidencia"].strip())
    for rule,field,check in [("R3 Exposición importadora","exposicion_importadora_candidata_pct",lambda v:v>100),
                             ("R4 Oferta parcial","oferta_parcial_candidata_t",lambda v:v<=0)]:
        value=x[field]
        status="No habilitada: comparabilidad física pendiente"
        if verified:
            status="Revisión contextual" if np.isfinite(value) and check(value) else "Sin disparo" if np.isfinite(value) else "No evaluable"
            if x[field+"__usa_imputacion"]:status="Condicionada por imputación · "+status
        rows.append(dict(regla=rule,estado=status,detalle=f"Año {year}; candidato {value:.2f}. No clasifica inseguridad alimentaria."))
    return pd.DataFrame(rows)

def synthetic_case(name,rules=None):
    """Entradas artificiales para probar la regla; no miden eficacia en mercados."""
    rules=rules or Rules();rng=np.random.default_rng(42)
    dates=pd.date_range("2020-01-01",periods=61,freq="MS")
    values=100*np.exp(np.r_[0,np.cumsum(rng.normal(.002,.01,60))])
    history=pd.Series(values[:-1],index=dates[:-1]);origin=history.index[-1]
    history.iloc[-3:]=history.iloc[-4]
    candidate=history.iloc[-1]*np.exp(.002)
    if name=="Choque +30 %":candidate=history.iloc[-1]*1.30
    if name=="Corte de tres meses":history.iloc[-3:]=np.nan
    sig=forecast_signal(history,origin,candidate,rules)
    return history,candidate,sig
