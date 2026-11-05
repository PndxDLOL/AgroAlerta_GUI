# AgroAlerta · Piloto gráfico V2

Aplicación Streamlit de Minería de Datos: precios agrícolas, producción, comercio, calidad y reglas
experimentales de volatilidad. **Interfaz V2; fase predictiva V1.** Las mejoras del modelo se registran
como trabajo futuro, sin presentarlas como una nueva anticipación validada.

## Ejecutar

Recomendado: Python 3.12. Abra una terminal en la carpeta que contiene app.py.

```bash
python -m venv .venv
```

Active con `.venv\Scripts\activate` en Windows o `source .venv/bin/activate` en Linux/macOS.

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abra la URL local que imprime Streamlit, normalmente http://localhost:8501. Inicia con las bases V4
incluidas: Colombia, Ecuador y Perú; arroz y maíz; 2012-2024. No requiere claves API.

## Cambios V2

- Botón claro/oscuro por sesión y parámetro tema en la URL; gráficos y tablas adaptados.
- Comparación del mismo producto en varios países: mismo mes y USD nominales, sin arrastrar datos.
- Mediana regional de volatilidades USD y cambio mensual, con canasta fija y cobertura completa.
- Gráfica y descarga de los pronósticos V1 originales, con métricas en fechas comunes.
- Escenarios futuros con zoom reciente y explicación de proyecciones planas; no se añade ruido.
- Instructivo PDF de ocho páginas, Excel vacío, plantillas CSV y conversor Excel a dos bases validadas.
- Lectura UTF-8 explícita para corregir el error CP1252 de Trazabilidad en Windows.
- Comentarios del equipo priorizados en docs/PLAN_PREDICCION_V2.md, visibles también en Ayuda.

## Pantallas

1. Panorama: diez KPI y frecuencias explícitas.
2. Comparación regional: un producto entre países, precios y volatilidad descriptiva.
3. Calidad e imputación: huecos, originales, preparados y correlación.
4. Modelos y escenarios: resultados V1 exactos o escenarios por corte.
5. SAT y evaluación: reglas, detección, señales experimentales, falsas alarmas y omisiones.
6. Trazabilidad: reglas, hashes y evidencias.
7. Ayuda y mejoras V2: documentación, conversor y plan predictivo.

Naranja y rombos indican estimaciones o dependencia de imputaciones. No evaluable sigue separado de
Sin señal estadística. La mediana regional no es una nueva alerta SAT ni volatilidad de una cartera.
Las cifras USD regionales pueden diferir de las volatilidades locales del SAT.

## Preparar y actualizar datos

Complete assets/Plantilla_AgroAlerta.xlsx conservando mensual y anual. Use Ayuda para convertirla, o:

```bash
python scripts/preparar_csv.py --excel Mi_base.xlsx
python scripts/actualizar_datos.py --entrada data/importacion_csv
```

El conversor no imputa: valida columnas, originales y llaves y exporta las dos bases con contrato V4.
Un pronóstico exportado no se debe convertir en observación original.

Después de volver a ejecutar los notebooks en Colab o Jupyter:

```bash
python scripts/actualizar_datos.py --proyecto /ruta/Proyecto_Precios_Agricolas
```

Busca data/processed/Imputacion/resultados_imputacion_V4 y las salidas hermanas de
Modelado/resultados_piloto_modelos_V1. Valida antes de sustituir data/current. Si cambian las bases y
no coinciden sus SHA-256, desactiva resultados predictivos antiguos. Pulse Actualizar lectura.
Países, productos y períodos se obtienen de los archivos. También admite subir ambos CSV en el lateral,
AGROALERTA_DATA_DIR (carpeta de CSV) y AGROALERTA_PROYECTO (raíz del proyecto).

## Reproducir evidencias y pruebas

```bash
python scripts/generar_evidencias.py
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Las evidencias se generan en data/processed/SAT/resultados_sat_V1, conservando la identificación V1.
Incluyen indicadores regionales por producto. --recalcular ejecuta un nuevo ensayo de tres modelos.
Se aprobaron 36 tests: datos, causalidad, V1, región, UTF-8, Excel, siete pantallas y apariencia por sesión.
Se renderizaron y revisaron las ocho páginas del PDF y las tres hojas del Excel. La interfaz se verifica
con AppTest; el navegador remoto no accede al servidor local de este entorno. No se declara una revisión
visual de la app en ese navegador ni un despliegue externo.

## Documentación

- [Instructivo PDF](docs/Instructivo_AgroAlerta_V2.pdf).
- [Reglas y KPI](docs/REGLAS_Y_KPI.md).
- [Contrato y reproducción](docs/DATOS_Y_REPRODUCCION.md).
- [Plan Predicción V2](docs/PLAN_PREDICCION_V2.md).
- [Pruebas y demostración](docs/PRUEBAS_Y_DEMO.md).
- [Fuentes](docs/FUENTES.md).

Para regenerar el PDF: instale requirements-docs.txt y ejecute scripts/generar_instructivo.py.
El Excel se edita con una aplicación de hojas de cálculo. regional.py calcula el panel, v1.py recupera
resultados del notebook, templates.py convierte archivos y textio.py concentra lectura UTF-8.

## GitHub y servidor

Suba el contenido de esta carpeta, incluidos data/demo, docs y assets. Excluya entornos, secretos y
bases propias no autorizadas. Se incluyen GitHub Actions y Dockerfile, sin ejecución en las cuentas
del equipo. Streamlit Community Cloud puede usar app.py y Python 3.12.

```bash
docker build -t agroalerta .
docker run --rm -p 8501:8501 agroalerta
```

La selección del modelo, nuevos datos, eventos a 3/6 meses, incertidumbre y publicación real de fuentes
son trabajo futuro. Los escenarios desde 2025 parten del corte histórico 2024; no son datos actuales.

Equipo: Cristian Valdes Díaz, Miguel Angel Rendón Barrios y Juan David Rodríguez Leguizamón.
Docente asesor: Jaime Andrés Gutierrez Monsalve.
