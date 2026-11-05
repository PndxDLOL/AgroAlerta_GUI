"""Generar la guía PDF de uso. Requiere requirements-docs.txt además del entorno del app."""
from pathlib import Path
import sys,shutil
from html import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Preformatted,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"docs/Instructivo_AgroAlerta_V2.pdf"
GREEN=colors.HexColor("#173d34");ACCENT=colors.HexColor("#197253");MUTED=colors.HexColor("#5e746a")
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleA",fontName="Helvetica-Bold",fontSize=26,leading=30,textColor=GREEN,spaceAfter=12))
styles.add(ParagraphStyle(name="SubA",fontName="Helvetica-Bold",fontSize=16,leading=20,textColor=GREEN,spaceAfter=12))
styles.add(ParagraphStyle(name="BodyA",fontName="Helvetica",fontSize=10.7,leading=15,spaceAfter=9,textColor=GREEN))
styles.add(ParagraphStyle(name="SmallA",fontName="Helvetica",fontSize=9,leading=12,spaceAfter=7,textColor=MUTED))
styles.add(ParagraphStyle(name="CellA",fontName="Helvetica",fontSize=9.3,leading=12,textColor=GREEN))
styles.add(ParagraphStyle(name="HeadA",fontName="Helvetica-Bold",fontSize=9.3,leading=12,textColor=colors.white))
styles.add(ParagraphStyle(name="CodeA",fontName="Courier",fontSize=8.4,leading=12,backColor=colors.HexColor("#edf3ef"),borderPadding=10,spaceAfter=12,textColor=GREEN))
fontdir=Path("/usr/share/fonts/truetype/dejavu")
if (fontdir/"DejaVuSans.ttf").exists():
    for name,file in [("AgroText","DejaVuSans.ttf"),("AgroBold","DejaVuSans-Bold.ttf"),("AgroMono","DejaVuSansMono.ttf")]:
        pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
    pdfmetrics.registerFontFamily("AgroText",normal="AgroText",bold="AgroBold",italic="AgroText",boldItalic="AgroBold")
    for name in ["BodyA","SmallA","CellA"]:styles[name].fontName="AgroText"
    for name in ["TitleA","SubA","HeadA"]:styles[name].fontName="AgroBold"
    styles["CodeA"].fontName="AgroMono"
story=[]

def p(text,style="BodyA"):story.append(Paragraph(text,styles[style]))
def heading(text):p(text,"SubA")
def code(text):story.append(Preformatted(text,styles["CodeA"]))
def table(rows,widths):
    cells=[[Paragraph(escape(str(v)),styles["HeadA"] if i==0 else styles["CellA"]) for v in row] for i,row in enumerate(rows)]
    t=Table(cells,colWidths=widths,hAlign="LEFT",repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),GREEN),("VALIGN",(0,0),(-1,-1),"TOP"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f2f6f3")]),
        ("BOTTOMPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),8),
        ("LINEBELOW",(0,0),(-1,0),.6,ACCENT)]))
    story.append(t);story.append(Spacer(1,12))
def page(num,title):
    if story:story.append(PageBreak())
    p(f"GUÍA DE USO / {num:02d}","SmallA");heading(title)

page(1,"AgroAlerta")
p("Piloto gráfico V2", "TitleA")
p("Proyecto de aula de Minería de Datos. Edición del 3 de noviembre de 2026.")
p("Esta guía explica cómo ejecutar el aplicativo, distinguir observaciones e imputaciones, comparar países, revisar las predicciones V1 y preparar archivos nuevos. La interfaz V2 incorpora mejoras de uso; Predicción V2 sigue siendo un plan de investigación.")
heading("1. Primera ejecución")
p("Instale Python 3.12. Descomprima el proyecto y abra una terminal dentro de la carpeta que contiene app.py. Cree y active un entorno virtual:")
code("python -m venv .venv\n.venv\\Scripts\\activate\npython -m pip install -r requirements.txt\npython -m streamlit run app.py")
p("En Linux o macOS, active el entorno con <b>source .venv/bin/activate</b>. Abra en el navegador la dirección que imprime Streamlit, normalmente http://localhost:8501.")
p("El piloto inicia con data/demo: Colombia, Ecuador y Perú, arroz y maíz, entre 2012 y 2024. No requiere claves API ni descargar precios nuevos al abrir. Los escenarios posteriores a 2024 parten de un corte histórico.")
heading("2. Tema y ayuda")
p("En el panel lateral pulse <b>Cambiar a modo oscuro</b> o <b>Cambiar a modo claro</b>. La selección afecta la sesión y se conserva en el parámetro tema de la URL; no cambia datos ni la apariencia de otros usuarios.")
p("En <b>Instructivo y plantillas</b> descargue este PDF, la plantilla Excel y los encabezados CSV. También están disponibles en <b>Ayuda y mejoras V2</b>.")
p("Recomendación para presentar: ejecute la aplicación antes de la exposición y conserve los datos de demostración para reproducir el recorrido.","SmallA")

page(2,"Explorar mercados y reconocer estimaciones")
p("Elija la fuente, el país, el producto y el período descriptivo en el panel lateral. Países y productos se obtienen de los archivos; no es necesario editar una lista en el código.")
table([["Pantalla","Para qué usarla"],
 ["Panorama","Consultar diez KPI, precios mensuales y contexto productivo/comercial anual."],
 ["Comparación regional","Comparar un producto entre países y revisar cobertura del indicador conjunto."],
 ["Calidad e imputación","Localizar huecos, contrastar originales y preparados, y examinar descriptivos y correlaciones."],
 ["Modelos y escenarios","Reproducir resultados del notebook V1 o calcular un escenario desde un origen."],
 ["SAT y evaluación","Consultar reglas, episodios observados, señales de un mes, falsas alarmas y omisiones."],
 ["Trazabilidad","Revisar reglas, huellas SHA-256 y descargar datos o evidencias."],
 ["Ayuda y mejoras V2","Preparar CSV y consultar el plan de mejora predictiva."]],[145,350])
heading("Qué significan las marcas")
p("<b>Original:</b> dato reportado por la fuente y conservado sin modificación. <b>Imputado:</b> estimación para una observación que faltaba. Los rombos y las celdas naranjas la resaltan. <b>Usa imputación:</b> un indicador derivado depende de alguna entrada estimada.")
p("Un retorno necesita dos precios positivos consecutivos. La volatilidad de tres retornos necesita cuatro. Por eso una imputación puede afectar varios indicadores siguientes, y los primeros períodos tienen ausencias estructurales.")
p("Un vacío no equivale a cero. La aplicación conserva NaN, genera filas ausentes del calendario con NaN y no crea precios automáticamente. En el piloto hay 936 filas mensuales y 130 precios imputados; las lagunas locales largas siguen siendo una limitación.")
p("Los KPI anuales se muestran una vez por año, sin convertirlos en doce observaciones mensuales. Las exposiciones y la oferta parcial son candidatas hasta comprobar equivalencia física entre producción y comercio.")

page(3,"Comparar un producto en la región")
p("1. Seleccione Arroz o Maíz en el panel lateral y abra <b>Comparación regional</b>. El país del lateral no limita esta pantalla.")
p("2. Elija los países de una canasta fija. Desplace <b>Mes para la comparación entre países</b> para ver el mismo mes en todos ellos, sin arrastrar el último precio conocido de otro período.")
p("3. Compare USD/t original, USD/t preparado, estado del precio, retorno y volatilidad original en USD. Cambie entre Originales y Serie preparada para examinar las curvas. Abra la tabla mensual y descargue el detalle con procedencia.")
heading("Indicador conjunto de volatilidad")
p("Para cada país se calculan retornos logarítmicos del precio en USD nominales y su desviación muestral de tres retornos. La mediana regional resume esas volatilidades, con igual participación descriptiva de los países.")
code("retorno_USD[t] = 100 * ln(precio_USD[t] / precio_USD[t-1])\nvol_pais[t] = desviacion_muestral(ultimos_3_retornos_USD)\nvol_regional[t] = mediana(vol_pais[t] de toda la canasta)\ncambio[t] = vol_regional[t] - vol_regional[t-1]")
p("Se requieren al menos dos países y volatilidad disponible en <b>todos</b> los países elegidos. Si falta alguno, la mediana original queda no calculable; no cambia la composición para aparentar continuidad. El cambio solo se calcula entre meses consecutivos completos.")
table([["Ejemplo real del piloto: Arroz, 2024-12","Resultado"],
 ["Canasta","Colombia, Ecuador y Perú"],
 ["Cobertura original","3 de 3 países"],
 ["Mediana de volatilidades en USD","2,4686 puntos porcentuales"],
 ["Cambio frente a 2024-11","-1,5820 puntos porcentuales"]],[325,170])
p("Es un indicador exploratorio de los mercados presentes, no una medición de toda América Latina. No es volatilidad de una cartera, no implica causalidad entre países y no activa una alerta SAT regional. El SAT individual usa moneda local; por eso sus cifras pueden diferir.","SmallA")

page(4,"Predicciones V1 y escenarios futuros")
heading("Resultados V1 del notebook")
p("En <b>Modelos y escenarios</b> seleccione frecuencia y variable objetivo. Abra <b>Resultados V1 del notebook</b>, elija etapa, ventana y tipo de historia, y compare hasta cuatro modelos. Se grafican exactamente los pronósticos del CSV V1 compatible con las bases actuales.")
p("Cada punto V1 es un pronóstico de un período desde un origen anterior. La tabla incluye fecha, origen, observado original, pronóstico, error e imputaciones del entrenamiento. Las métricas usan las mismas fechas elegibles entre modelos; descargue el CSV para revisarlas.")
p("MAE y RMSE conservan la unidad del objetivo. nMAE normaliza con la escala guardada en V1 y MASE utiliza la escala histórica de su corte. No seleccione de nuevo al ganador por prueba: 2023-2024 ya se había examinado.")
heading("Escenarios futuros")
p("Cambie a <b>Escenarios futuros</b>. Elija origen, modelos, horizonte y ventana de entrenamiento; pulse <b>Calcular escenario</b>. El motor vuelve a los originales y reconstruye la historia dentro del corte. El gráfico muestra los últimos 24 meses o seis años, más el escenario; puede activar toda la historia.")
p("Cambiar el zoom no cambia el entrenamiento. Los valores originales posteriores al origen, si existen, se muestran como retenidos y no entran al ajuste. Las advertencias, los modelos no elegibles y la cantidad de imputaciones permanecen visibles.")
table([["Una curva plana o suave","Cómo interpretarla"],
 ["Ingenuo","Repite el último precio por definición."],
 ["SES o Holt amortiguado","Estiman nivel o tendencia amortiguada; no simulan todos los movimientos futuros."],
 ["ARIMA / escenario multipaso","Puede converger a un nivel o trayectoria suave con sus parámetros."],
 ["Diferencia frente a V1","V1 reajusta en cada corte; el escenario ajusta una vez y proyecta varios pasos."]],[160,335])
p("No se añade ruido para hacer una curva más atractiva. Una media esperada suave puede acompañarse de resultados futuros variables. Los escenarios multipaso no tienen intervalos calibrados ni anticipación SAT demostrada a 3 o 6 meses. LSTM se puede ver en resultados V1 cuando fue elegible; el motor interactivo no lo entrena.","SmallA")

page(5,"Reglas SAT, cortes y evidencias")
p("La regla mensual compara la volatilidad de tres retornos con percentiles de historia original. Exige al menos 24 volatilidades de calibración. Para anticipar un mes combina el retorno del precio previsto con dos retornos ya observados: esto es una señal experimental, no anticipación demostrada de una crisis.")
table([["Regla o estado","Lectura"],
 ["Volatilidad alta","Volatilidad mayor al percentil 90 de calibración."],
 ["Vigilancia","Mayor al percentil 75 y no mayor al 90."],
 ["Sin señal estadística","Valor no superior al percentil 75, con datos suficientes."],
 ["No evaluable","Datos o calibración insuficientes. Nunca significa normal."],
 ["Contexto anual","Caída de producción y candidatos comerciales, con rezago supuesto de dos años."],
 ["Calidad de datos","Cobertura original reciente menor a 80 % genera un aviso de revisión."]],[160,335])
p("Las reglas comerciales permanecen deshabilitadas hasta documentar equivalencia de rubros y unidades. El desfase de publicación anual debe verificarse con fechas reales. La mediana regional USD es descriptiva y se mantiene separada de estas reglas.")
heading("Cómo verificar el funcionamiento")
p("Use un corte con precios originales y después un mes dentro de un hueco de Colombia. El segundo puede resultar No evaluable. En el laboratorio: Estabilidad debe dar Sin señal, Choque +30 % debe dar Volatilidad alta y Corte de tres meses debe dar No evaluable. Son datos artificiales separados de las métricas reales.")
p("En la evaluación, TP son aciertos de alerta, FP falsas alarmas, FN eventos omitidos y TN ausencias correctas. El ejemplo V1 con Ingenuo tiene 10 aciertos de 17 meses evento y siete omisiones; no demuestra anticipación confiable. Los 17 meses no necesariamente son episodios independientes.")
heading("Trazabilidad")
p("Revise las huellas SHA-256 y las reglas. Prepare y descargue el paquete de evidencias: conserva indicadores, señales, métricas, exclusiones y configuración. Un cambio en las bases desactiva métricas V1 antiguas si sus huellas ya no coinciden.")
p("El fallo de Windows por CP1252 se corrigió con lectura explícita UTF-8 (incluido BOM). No cambie el texto ni elimine tildes para resolverlo.","SmallA")

page(6,"Preparar nuevas bases: Excel y campos")
p("Descargue <b>Plantilla_AgroAlerta.xlsx</b>. La hoja Guia explica el contrato; mensual y anual están vacías. Pegue datos ya integrados por país, producto y período. Puede extender filas y países sin cambiar los encabezados.")
table([["Hoja mensual: columna","Contenido"],
 ["pais","Nombre consistente del país."],
 ["producto","Nombre consistente del producto."],
 ["fecha","Primer día del mes: 2024-01-01."],
 ["precio_lcu_t","Precio preparado en moneda local por tonelada."],
 ["precio_lcu_t__original","Precio original; vacío si era faltante."],
 ["tasa_lcu_usd","Unidades de moneda local por USD; positiva."]],[195,300])
p("La hoja anual usa pais, producto y fecha al primero de enero. Agregue las siete medidas siguientes y, para cada una, la columna con sufijo <b>__original</b> (17 columnas en total).")
table([["Medida anual","Unidad"],
 ["produccion_t","Toneladas producidas"],["area_ha","Hectáreas cosechadas"],
 ["rendimiento_t_ha","Toneladas por hectárea, declaradas en la fuente"],
 ["importaciones_t / exportaciones_t","Toneladas del rubro comercial"],
 ["importaciones_usd / exportaciones_usd","Valor comercial en USD"]],[240,255])
p("No es obligatorio repetir en Excel las columnas derivadas de retorno, volatilidad o exposición: el aplicativo las calcula. Tampoco son obligatorias las marcas __imputado; si existen se comprueba que concuerden con el original.")
p("Ejemplo didáctico: si un precio original es 100, escriba 100 en precio_lcu_t y en precio_lcu_t__original. Si una estimación documentada es 110 y la fuente estaba vacía, escriba 110 solo en precio_lcu_t. Si no hay dato ni estimación, deje ambas celdas vacías.","SmallA")

page(7,"Convertir, guardar y actualizar")
heading("Opción A: desde el aplicativo")
p("Abra <b>Ayuda y mejoras V2</b>, cargue el Excel completado y descargue <b>las dos bases CSV validadas</b>. Descomprímalas en una carpeta de entrada. Después cárguelas desde Fuente de datos / Cargar dos CSV, o importe la carpeta al proyecto.")
heading("Opción B: desde la terminal")
code("python scripts/preparar_csv.py --excel Mi_base.xlsx\npython scripts/actualizar_datos.py --entrada data/importacion_csv\npython -m streamlit run app.py")
p("El conversor genera base_mensual_V4.csv y base_anual_V4.csv. La denominación indica compatibilidad con el contrato V4: la conversión no ejecuta la imputación del notebook. Las fechas son ISO, los números usan punto decimal y el CSV usa coma y UTF-8. El conversor evita depender del separador regional de Excel.")
heading("Opción C: desde los notebooks en Colab/Jupyter")
p("Exporte las dos bases finales con originales y marcas. Sustituya los nombres de DataFrame y la carpeta por los que usa su notebook:")
code("base_mensual.to_csv(\n    CARPETA / 'base_mensual_V4.csv', index=False,\n    encoding='utf-8-sig', date_format='%Y-%m-%d')\nbase_anual.to_csv(\n    CARPETA / 'base_anual_V4.csv', index=False,\n    encoding='utf-8-sig', date_format='%Y-%m-%d')")
p("Conserve la carpeta de imputación y vuelva a ejecutar el modelado cuando cambien las bases. Puede actualizar directamente desde la carpeta del proyecto:")
code("python scripts/actualizar_datos.py --proyecto RUTA_DEL_PROYECTO")
p("El importador busca las salidas V4 en data/processed/Imputacion/resultados_imputacion_V4 y las predictivas en Modelado/resultados_piloto_modelos_V1. También acepta --entrada con otra carpeta compatible. Valida antes de sustituir data/current y conserva los CSV.")
p("Si la aplicación ya estaba abierta, pulse <b>Actualizar lectura</b>. Cambiar las bases invalida la caché y las métricas vinculadas a la versión anterior. El formato y las llaves se comprueban; la comparabilidad económica entre rubros sigue requiriendo revisión del equipo.","SmallA")

page(8,"Descargas, problemas frecuentes y trabajo futuro")
table([["Descarga","Uso correcto"],
 ["Bases mensuales y anuales filtradas","EDA y seguimiento con columnas originales y marcas."],
 ["Detalle e indicador regional","Comparación descriptiva entre países del mismo producto."],
 ["Resultados V1 seleccionados","Revisar observado, pronóstico, corte y error del notebook."],
 ["Escenario predictivo","Analizar futuros hipotéticos; no convertirlo en observación original."],
 ["Paquete de evidencias","Conservar datos, reglas, métricas, exclusiones y versión para el informe."]],[175,320])
heading("Si algo no carga")
p("<b>Faltan columnas:</b> conserve los encabezados de la plantilla. <b>Duplicados:</b> una sola fila por país, producto y fecha; resuelva la duplicación en la integración. <b>Originales modificados:</b> restablezca el valor reportado por la fuente.")
p("<b>Excel vacío:</b> la plantilla no es una base de demostración; debe completarse. <b>Números inválidos:</b> escriba cantidades numéricas, sin unidades ni separadores de miles como texto. <b>Resultados V1 no disponibles:</b> las nuevas bases requieren sus predicciones y configuración de huellas correspondientes.")
p("<b>Modelo no elegible:</b> revise muestra, huecos, positividad y frecuencia; no se aplica un relleno oculto. Las redes necesitan más respuestas originales y no se supone estacionalidad de doce años en datos anuales.")
heading("Qué queda para Predicción V2")
p("En docs/PLAN_PREDICCION_V2.md se registraron los comentarios del equipo: auditoría del comercio, disponibilidad real de datos, actualización a períodos publicados no vistos, precios reales, variables externas, modelos probabilísticos de eventos, horizontes de 3/6 meses, incertidumbre, calibración y sensibilidad a imputaciones.")
p("Estas tareas no se reportan como logros terminados. El aplicativo presentado conserva resultados V1, monitoreo y reglas experimentales. Su valor predictivo futuro se evaluará frente a Ingenuo, persistencia y referencias probabilísticas, con una prueba que permanezca sin examinar.")
p("Fuentes técnicas: docs.streamlit.io; documentación de pandas, scikit-learn y statsmodels. Fuentes de datos del proyecto: FAOSTAT PP/QCL/TCL y divisa utilizada en el notebook. La interfaz visual toma referencias del ejemplo AE4 suministrado y de panorama-cd-colombia.vercel.app; no copia sus datos ni sus modelos.","SmallA")

def footer(canvas,doc):
    canvas.setStrokeColor(colors.HexColor("#d7e2dc"));canvas.line(48,39,A4[0]-48,39)
    canvas.setFont("Helvetica",8);canvas.setFillColor(MUTED)
    canvas.drawString(48,26,"AgroAlerta | Interfaz V2 | Predicción V1 | Guía de uso")
    canvas.drawRightString(A4[0]-48,26,str(doc.page))

OUT.parent.mkdir(parents=True,exist_ok=True)
doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=50,leftMargin=50,topMargin=45,bottomMargin=55,title="AgroAlerta - Instructivo del piloto V2",author="Equipo AgroAlerta")
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
