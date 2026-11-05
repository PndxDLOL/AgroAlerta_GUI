# Datos y reproducción

## Contrato mínimo

CSV UTF-8 con coma como separador, punto decimal y nombres de columnas V4. Se aceptan mercados y períodos
distintos de los del piloto. Cada llave es única: `pais + producto + fecha`. La fecha es inicio de mes
en la base mensual y primero de enero en la anual. Los países se muestran por nombre, no por M49.

| Archivo | Columnas necesarias |
| --- | --- |
| base_mensual_V4.csv | pais, producto, fecha, precio_lcu_t, precio_lcu_t__original, tasa_lcu_usd |
| base_anual_V4.csv | pais, producto, fecha y las siete medidas siguientes, cada una con su __original |

Las siete medidas anuales son `produccion_t`, `area_ha`, `rendimiento_t_ha`, `importaciones_t`,
`exportaciones_t`, `importaciones_usd`, `exportaciones_usd`. Las marcas `__imputado` son opcionales;
si existen se comprueban frente al original. Las demás columnas V4 se conservan y los KPI se recalculan.
True/False y 1/0 se interpretan explícitamente. Nunca se convierte la cadena False en un valor verdadero.

Original conocido: valor preparado igual al original. Original NaN y preparado conocido: imputado.
Ambos NaN: faltante sin resolver. La tasa es LCU por USD, estrictamente positiva si está informada.
Una misma divisa país-mes debe coincidir entre productos. No se aceptan duplicados ni cambios de originales.
No se realiza una nueva conversión monetaria ni se consulta una API al iniciar la interfaz.

Un calendario ausente se completa dentro del intervalo de cada mercado, con NaN. No se inventan
observaciones fuera de sus extremos ni se rellenan automáticamente los precios. Una fila nueva o una
serie nueva sin suficiente historia puede permanecer No evaluable: escalar no significa garantizar datos.

## Flujo de archivos

1. Descarga e integración PP, TCL y QCL en notebooks.
2. EDA e imputación V4: exportar las dos bases con originales y marcas.
3. Modelado V1: exportar configuración con SHA-256, predicciones evaluadas y ranking.
4. Importador o variable de entorno: leer salidas compatibles sin editar app.py.
5. Streamlit: recalcular KPI, reconstruir escenarios por corte y evaluar SAT.
6. Exportación: conservar reglas, huellas, exclusiones, predicciones y métricas junto al informe.

No se ejecuta código de notebooks subidos desde la interfaz. El motor utiliza funciones Python estáticas
adaptadas de V1. Los modelos interactivos no reemplazan los ensayos completos del notebook.

Para verificar trazabilidad de métricas se requiere `configuracion.json` con `fuentes`, un diccionario
que asocia los dos nombres de CSV a sus SHA-256 exactos. `predicciones_evaluadas.csv` debe tener
frecuencia, variable, pais, producto, fecha, origen, modelo, pronostico y observado; opcionalmente,
ventana y preparacion. Se usa historia total y preparación KNN por corte. El esquema oficial V1 se
incluye en el piloto. Su formato y sus nombres no se traducen automáticamente desde otros esquemas.

El validador de huellas impide presentar métricas antiguas como si procedieran de bases nuevas. No
demuestra por sí solo que un experimento externo esté bien diseñado: ese diseño debe documentarse.

## Ejecutar después de Colab

Con Drive montado y el repositorio copiado en `/content/agroalerta-streamlit`, por ejemplo:

```python
import subprocess, sys
subprocess.run([
    sys.executable, "/content/agroalerta-streamlit/scripts/actualizar_datos.py",
    "--proyecto", "/content/drive/MyDrive/Proyecto_Precios_Agricolas"
], check=True)
```

Descargue `data/current` y póngala en la misma ruta del equipo que ejecutará Streamlit. Instale allí
`requirements.txt`. Si usa otro nombre de versión de imputación, indique su carpeta con `--entrada`;
mantenga el contrato y los nombres de archivos o renómbrelos explícitamente al exportar. No modifique
etiquetas para aparentar una procedencia V4 que no corresponda: documente la versión en el manifest.

## Reconstrucción temporal

Para cada origen se descartan los valores preparados retrospectivos y se toman los originales. KNN
reconstruye cada hueco con ajuste anterior al inicio de ese hueco y donantes no posteriores al origen.
Usa normalización histórica, calendario, rezagos y contexto regional; no utiliza precios futuros del
mercado que se quiere pronosticar. El contexto anual mensual usa originales de dos años antes.
Las ventanas 12/24/36 o 3/5 restringen el ajuste del pronosticador tras esa reconstrucción; el imputador
conserva su historia causal anterior. Por tanto, no equivalen a entrenar toda la tubería desde cero
exclusivamente dentro de la ventana corta.

Faltantes persistentes, series nuevas sin centro histórico o donantes insuficientes producen modelos
no elegibles, con motivo visible. No hay relleno simple automático para ocultar ese problema.

## Cuidados de interpretación

La base preparada no convierte imputaciones en verdad. Los cortes largos de Colombia siguen siendo
estimaciones con incertidumbre; no quedaron validados por el límite global del 20 %. Ese porcentaje
incluye divisa contada una vez por país-mes y anualidades una vez por año, sin duplicarlas por frecuencia.
Los faltantes estructurales de retorno y volatilidad se informan aparte.

El dato de exportaciones de arroz de Colombia en 2024 (62048,43 t) requiere contrastar fuente, unidad y
rubro antes de explicar su salto como cambio económico. No se corrige silenciosamente ni se selecciona
un modelo anual definitivo por un resultado inestable. No se supone que todos los países tengan la
misma moneda: las series LCU se comparan solo dentro del mercado; la correlación regional usa USD.

## Plantilla y conversión V2

assets/Plantilla_AgroAlerta.xlsx contiene Guia, mensual y anual. Las hojas de entrada están vacías.
Mantenga encabezados y deje el original vacío cuando la medida sea una estimación documentada.
Use Ayuda o scripts/preparar_csv.py --excel Mi_base.xlsx. Genera las dos bases en data/importacion_csv,
que puede importar con --entrada. Valida llaves, originales y magnitudes; no realiza imputación ni
verifica equivalencia física de rubros. El nombre V4 indica compatibilidad del contrato de columnas.

Los textos JSON y Markdown se leen explícitamente como UTF-8 con BOM admitido, sin depender de CP1252.
Los CSV usan UTF-8-sig en lectura y descarga. No incorpore proyecciones como observaciones originales.
