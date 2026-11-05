from pathlib import Path
from streamlit.testing.v1 import AppTest
from agroalerta.data import read_csv,MONTH_FILE,YEAR_FILE

ROOT=Path(__file__).resolve().parents[1]

def test_seven_pages_and_forecast(monkeypatch):
    monkeypatch.setenv("AGROALERTA_DATA_DIR",str(ROOT/"data/demo"))
    app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
    assert not app.exception and len(app.metric)==10
    assert app.selectbox(key="country").options==["Colombia","Ecuador","Perú"]
    for page in ["Comparación regional","Calidad e imputación","Modelos y escenarios","SAT y evaluación","Ayuda y mejoras V2","Trazabilidad"]:
        app.radio(key="page").set_value(page).run()
        assert not app.exception, [x.message for x in app.exception]
        if page=="Modelos y escenarios":
            assert len(app.dataframe)>=2
            app.radio(key="forecast_mode").set_value("Escenarios futuros").run()
            app.button(key="run_forecast").click().run()
            assert not app.exception and len(app.dataframe)>=2
            app.selectbox(key="frequency").select("anual").run()
            app.button(key="run_forecast").click().run()
            assert not app.exception
        if page=="SAT y evaluación":
            app.selectbox(key="synthetic").select("Corte de tres meses").run()
            assert not app.exception
    app.button(key="evidence").click().run()
    assert not app.exception

def test_market_filters(monkeypatch):
    monkeypatch.setenv("AGROALERTA_DATA_DIR",str(ROOT/"data/demo"))
    app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
    app.selectbox(key="country").select("Perú").run()
    app.selectbox(key="product").select("Maíz").run()
    assert not app.exception and len(app.metric)==10

def test_new_markets_from_files(monkeypatch,tmp_path,source_bytes):
    for name,raw in zip([MONTH_FILE,YEAR_FILE],source_bytes[:2]):
        d=read_csv(raw);d.loc[d.pais.eq("Colombia"),"pais"]="Chile"
        d.to_csv(tmp_path/name,index=False)
    monkeypatch.setenv("AGROALERTA_DATA_DIR",str(tmp_path))
    app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
    assert not app.exception
    assert app.selectbox(key="country").options==["Chile","Ecuador","Perú"]

def test_theme_button_preserves_data(monkeypatch):
    monkeypatch.setenv("AGROALERTA_DATA_DIR",str(ROOT/"data/demo"))
    app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
    values=[x.value for x in app.metric]
    app.button(key="toggle_theme").click().run()
    assert not app.exception and app.session_state["theme_mode"]=="oscuro"
    assert values==[x.value for x in app.metric]
    app.radio(key="page").set_value("Comparación regional").run()
    assert not app.exception
    app.button(key="toggle_theme").click().run()
    assert not app.exception and app.session_state["theme_mode"]=="claro"

def test_theme_is_per_session(monkeypatch):
    monkeypatch.setenv("AGROALERTA_DATA_DIR",str(ROOT/"data/demo"))
    dark=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
    dark.button(key="toggle_theme").click().run()
    light=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
    assert dark.session_state["theme_mode"]=="oscuro"
    assert light.session_state["theme_mode"]=="claro"
