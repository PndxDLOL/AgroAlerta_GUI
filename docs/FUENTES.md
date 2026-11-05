# Fuentes y atribución

## Datos del proyecto

Se incluyen salidas transformadas entregadas por el equipo, no una descarga nueva realizada por la
interfaz. Proceden de FAOSTAT: precios al productor (PP), cultivos y productos pecuarios (QCL), y comercio
de cultivos y productos pecuarios (TCL); la divisa corresponde a la serie histórica de Banco Mundial
usada en el proceso previo. Las imputaciones y derivados son transformaciones del proyecto AgroAlerta.
Los modelos y reglas de este prototipo no están respaldados ni certificados por esos organismos.

Las fechas originales de extracción, la edición de cada dominio y el identificador exacto de la serie
de divisa no se recuperan de los dos CSV V4. Deben completarse desde los registros de adquisición antes
de una publicación definitiva; no se inventan aquí. El manifest aporta el hash exacto de la copia usada.

Referencias de las bases:

- FAO, FAOSTAT, PP: https://www.fao.org/faostat/en/#data/PP
- FAO, FAOSTAT, QCL: https://www.fao.org/faostat/en/#data/QCL
- FAO, FAOSTAT, TCL: https://www.fao.org/faostat/en/#data/TCL
- Banco Mundial, catálogo de datos: https://data.worldbank.org/
- Términos de bases estadísticas FAO: https://www.fao.org/contact-us/terms/db-terms-of-use/es/

La política general de FAO indica CC BY 4.0 salvo excepciones en metadatos, junto con condiciones
adicionales. Se debe conservar esta atribución, identificar las transformaciones y comprobar condiciones
específicas de terceros. La licencia del código no sustituye las licencias de datos.
Fecha de comprobación de enlaces y política general: 28 de octubre de 2026. No equivale a fecha de
descarga de los datos. Para la bibliografía definitiva complete año de actualización y acceso original.

## Artefactos de origen

- `AgroAlerta_Imputacion_V4.ipynb`: originales, marcas y estructura de bases.
- `AgroAlerta_Piloto_Modelos_V1.ipynb`: reconstrucción por corte y candidatos predictivos.
- `AgroAlerta_Piloto_Modelos_V1_Completo.zip`: bases y tablas utilizadas en esta entrega.

Las funciones KNN se adaptaron a un módulo estático y se documentó la restricción temporal. No se
ejecuta automáticamente código de esos notebooks. La equivalencia de indicadores se verifica con
pruebas numéricas. Las fechas y firmas de los archivos efectivos están en `evidencias/datos/manifest.json`.

## Documentación técnica primaria

- Streamlit, instalación y ejecución: https://docs.streamlit.io/get-started/installation
- Streamlit, caché de datos: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data
- Streamlit, AppTest: https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest
- Streamlit, gráficos Plotly: https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart
- Streamlit Community Cloud: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app
- Scikit-learn, KNNImputer: https://scikit-learn.org/stable/modules/generated/sklearn.impute.KNNImputer.html
- Statsmodels, pronósticos: https://www.statsmodels.org/stable/tsa.html

Estas fuentes documentan la implementación. No constituyen validación externa de las reglas operativas
ni reemplazan las referencias científicas del manuscrito del equipo.

## Referencias visuales V2

AE4 fue suministrado como referencia de controles, observado frente a predicho y descarga CSV. Su app
analiza la acción de Ecopetrol; no se incorporaron su modelo ni datos al análisis agrícola.
https://panorama-cd-colombia.vercel.app/ se examinó como referencia de contraste, tarjetas, jerarquía
y alternancia de apariencia; no se emplearon sus cifras académicas en AgroAlerta.

La documentación de st.set_option limita su uso a opciones de cliente:
https://docs.streamlit.io/develop/api-reference/configuration/st.set_option . El piloto aplica estilos
y gráficos por sesión, sin modificar la configuración global de tema del servidor.
