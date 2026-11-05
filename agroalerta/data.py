"""Lectura y contrato de las salidas V4. No se rellenan valores silenciosamente."""
from dataclasses import dataclass, field
from pathlib import Path
from io import BytesIO
import hashlib
import json
import os
import numpy as np
import pandas as pd

KEY = ["pais", "producto"]
ANNUAL = ["produccion_t", "area_ha", "rendimiento_t_ha", "importaciones_t",
          "exportaciones_t", "importaciones_usd", "exportaciones_usd"]
MONTH_FILE = "base_mensual_V4.csv"
YEAR_FILE = "base_anual_V4.csv"

class DataError(ValueError):
    """El archivo incumple el contrato; se explica el problema al usuario."""

def sha(data):
    return hashlib.sha256(data).hexdigest()

def boolean(s):
    mapping = {"true": True, "false": False, "1": True, "0": False,
               "si": True, "sí": True, "no": False}
    if s.dtype == bool:
        return s.fillna(False)
    text = s.astype("string").str.lower().str.strip()
    bad = text.notna() & ~text.isin(mapping)
    if bad.any():
        raise DataError(f"Marca de imputación no reconocida: {text[bad].iloc[0]}")
    return text.map(mapping).fillna(False).astype(bool)

def read_csv(raw):
    try:
        return pd.read_csv(BytesIO(raw), encoding="utf-8-sig")
    except Exception as exc:
        raise DataError(f"No se pudo leer el CSV UTF-8: {exc}") from exc

def normalize(raw, frequency):
    d = read_csv(raw)
    variables = ["precio_lcu_t"] if frequency == "mensual" else ANNUAL
    required = KEY + ["fecha"] + variables + [v+"__original" for v in variables]
    if frequency == "mensual":
        required += ["tasa_lcu_usd"]
    missing = sorted(set(required)-set(d.columns))
    if missing:
        raise DataError("Faltan columnas V4: " + ", ".join(missing))
    for key in KEY:
        if d[key].isna().any() or d[key].astype(str).str.strip().eq("").any():
            raise DataError(f"Hay llaves vacías en {key}.")
        d[key] = d[key].astype(str).str.strip()
    d["fecha"] = pd.to_datetime(d.fecha, errors="coerce")
    if d.fecha.isna().any() or getattr(d.fecha.dt, "tz", None) is not None:
        raise DataError("Las fechas deben ser válidas y no tener zona horaria.")
    if not d.fecha.dt.day.eq(1).all() or (frequency == "anual" and not d.fecha.dt.month.eq(1).all()):
        raise DataError("La fecha debe ser inicio de mes (mensual) o de año (anual).")
    if d.duplicated(KEY+["fecha"]).any():
        raise DataError("Hay llaves país + producto + fecha duplicadas; corregirlas en el notebook.")
    nums = variables+[v+"__original" for v in variables]
    if frequency == "mensual":
        nums += ["tasa_lcu_usd"]
    for v in nums:
        parsed = pd.to_numeric(d[v], errors="coerce")
        if (d[v].notna() & parsed.isna()).any() or np.isinf(parsed).any():
            raise DataError(f"Hay números inválidos en {v}.")
        if parsed.dropna().lt(0).any():
            raise DataError(f"Hay magnitudes negativas en {v}; verificar unidades y fuente.")
        d[v] = parsed.astype(float)
    if frequency == "mensual" and d.tasa_lcu_usd.dropna().le(0).any():
        raise DataError("La tasa LCU por USD debe ser positiva.")
    for v in variables:
        observed = d[v+"__original"].notna()
        same = np.isclose(d.loc[observed,v], d.loc[observed,v+"__original"], rtol=1e-9, atol=1e-7)
        if not same.all():
            raise DataError(f"Se modificaron valores originales de {v}.")
        derived_flag = ~observed & d[v].notna()
        flag = v+"__imputado"
        if flag in d and not boolean(d[flag]).equals(derived_flag):
            raise DataError(f"La marca {flag} contradice el valor original.")
        d[flag] = derived_flag
        d[v+"__estado"] = np.select([observed, derived_flag], ["observado", "imputado"], default="faltante")
    # Calendario por mercado. Una fila ausente se vuelve NaN, nunca una observación.
    frames = []
    for (country, product), g in d.groupby(KEY, sort=True):
        g = g.sort_values("fecha").set_index("fecha")
        index = pd.date_range(g.index.min(), g.index.max(), freq="MS" if frequency=="mensual" else "YS")
        old_index = g.index
        g = g.reindex(index).rename_axis("fecha").reset_index()
        g["pais"], g["producto"] = country, product
        g["fila_calendario_generada"] = ~g.fecha.isin(old_index)
        for v in variables:
            g[v+"__imputado"] = g[v+"__imputado"].fillna(False).astype(bool)
            g[v+"__estado"] = g[v+"__estado"].fillna("faltante")
        frames.append(g)
    if not frames:
        raise DataError("El archivo no contiene registros.")
    return pd.concat(frames,ignore_index=True).sort_values(KEY+["fecha"]).reset_index(drop=True)

@dataclass
class Bundle:
    monthly: pd.DataFrame
    annual: pd.DataFrame
    hashes: dict
    label: str = "Piloto incluido"
    predictions: pd.DataFrame = field(default_factory=pd.DataFrame)
    ranking: pd.DataFrame = field(default_factory=pd.DataFrame)
    config: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    artifact_hashes: dict = field(default_factory=dict)

    @property
    def fingerprint(self):
        return sha(json.dumps({"bases":self.hashes,"resultados":self.artifact_hashes},sort_keys=True).encode())

def load_bytes(month, year, extras=None, label="Archivos V4"):
    m, a = normalize(month,"mensual"), normalize(year,"anual")
    # La divisa de un país/mes debe coincidir entre todos sus productos.
    if m.groupby(["pais","fecha"]).tasa_lcu_usd.nunique().gt(1).any():
        raise DataError("Las tasas de cambio difieren entre productos del mismo país y mes.")
    h = {MONTH_FILE:sha(month),YEAR_FILE:sha(year)}
    b = Bundle(m,a,h,label)
    extras = extras or {}
    b.artifact_hashes={name:sha(raw) for name,raw in extras.items()}
    if "configuracion.json" in extras:
        cfg = json.loads(extras["configuracion.json"])
        b.config = cfg
        if cfg.get("fuentes") == h:
            if "predicciones_evaluadas.csv" in extras:
                b.predictions = read_csv(extras["predicciones_evaluadas.csv"])
                for v in ["fecha","origen"]:
                    b.predictions[v] = pd.to_datetime(b.predictions[v])
            if "ranking_escala_completa_casos_comunes.csv" in extras:
                b.ranking = read_csv(extras["ranking_escala_completa_casos_comunes.csv"])
        else:
            b.warnings.append("Las bases cambiaron: se desactivaron los resultados V1 antiguos. Reejecute el notebook predictivo o recalcule el SAT con las bases actuales.")
    else:
        b.warnings.append("No se cargaron resultados predictivos vinculados a estas bases. Los escenarios interactivos sí usan los archivos actuales.")
    return b

def resolve_directory(repo):
    if os.environ.get("AGROALERTA_DATA_DIR"):
        return Path(os.environ["AGROALERTA_DATA_DIR"]).expanduser()
    if os.environ.get("AGROALERTA_PROYECTO"):
        return Path(os.environ["AGROALERTA_PROYECTO"])/"data/processed/Imputacion/resultados_imputacion_V4"
    current = Path(repo)/"data/current"
    return current if (current/MONTH_FILE).exists() else Path(repo)/"data/demo"

def read_directory(directory):
    p = Path(directory)
    try:
        month,year = (p/MONTH_FILE).read_bytes(),(p/YEAR_FILE).read_bytes()
    except OSError as exc:
        raise DataError(f"No se encuentran ambas bases V4 en {p}.") from exc
    # Soporta el paquete preparado y la organización original de Google Drive.
    candidates = [p, p.parents[1]/"Modelado/resultados_piloto_modelos_V1" if len(p.parents)>1 else p]
    extras = {}
    for name in ["configuracion.json","predicciones_evaluadas.csv","ranking_escala_completa_casos_comunes.csv"]:
        for root in candidates:
            paths = [root/name,root/"tablas"/name]
            hit = next((x for x in paths if x.is_file()),None)
            if hit:
                extras[name] = hit.read_bytes(); break
    return month,year,extras

def quality(b):
    m,a=b.monthly,b.annual
    fx=m.groupby(["pais","fecha"]).tasa_lcu_usd.first()
    missing_m=int(m.precio_lcu_t__original.isna().sum())
    missing_a=int(a[[v+"__original" for v in ANNUAL]].isna().sum().sum())
    denominator=len(m)+len(a)*len(ANNUAL)+len(fx)
    missing=missing_m+missing_a+int(fx.isna().sum())
    return dict(mensual=len(m),anual=len(a),precios_originales=int(m.precio_lcu_t__original.notna().sum()),
                precios_imputados=int(m.precio_lcu_t__imputado.sum()),faltantes_mensuales=missing_m,
                faltantes_anuales=missing_a,celdas_base=denominator,faltantes_base=missing,
                porcentaje_global=100*missing/denominator,
                porcentaje_agricola=100*(missing_m+missing_a)/(len(m)+len(a)*7))
