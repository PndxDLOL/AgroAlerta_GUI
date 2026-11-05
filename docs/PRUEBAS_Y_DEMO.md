# Verificación y demostración del piloto gráfico V2

Se aprobaron 36 pruebas automatizadas con Python 3.12.14 y las dependencias fijadas. AppTest recorre
las siete pantallas, una proyección mensual y anual, el laboratorio, evidencias, filtros y tema. Dos
sesiones independientes conservan apariencias distintas y el cambio de tema no modifica los KPI.

Las pruebas nuevas verifican UTF-8 ante un fallo CP1252 reproducible, igualdad de valores V1 graficados,
mediana regional calculada independientemente, canasta fija cuando falta un país, diferencias entre
meses consecutivos, exclusión del índice con un solo país, rechazo de Excel vacío y conservación de
originales e imputaciones al convertir Excel. La fixture contiene valores sintéticos solo para tests.

Se revisaron las tres hojas del Excel y las ocho páginas del PDF. Se comprobó la conversión por terminal.
No se realizó usabilidad con participantes ni un despliegue en GitHub, Docker o Streamlit Community Cloud.
El navegador remoto no pudo acceder al servidor local; la interfaz conserva las verificaciones AppTest.

## Recorrido de 12-15 minutos

1. Panorama (2 min): Colombia-Arroz, diez KPI, procedencia y tema. Aclare USD nominales y corte 2024.
2. Calidad (2 min): huecos largos e imputaciones; ausencia global distinta de cobertura local.
3. Regional (2 min): mismo producto, tres países y mismo mes; mediana con cobertura completa, sin alerta regional.
4. V1 y escenarios (3 min): compare pronósticos registrados con originales; después genere un escenario.
   Explique que V1 reajusta un paso por corte y el multipaso ajusta una sola vez. No se inventa ruido.
5. SAT (2-3 min): señal estricta, casos comunes, falsas alarmas y omisiones; corte No evaluable y laboratorio separado.
6. Ayuda/Trazabilidad (1-2 min): PDF, plantilla, conversión y plan de investigación Predicción V2.

Se conserva la evaluación V1: 144 casos comunes de prueba, 17 meses evento; Ingenuo obtiene
TP=10, FP=0, FN=7 y TN=127. Es retrospectiva y exploratoria; los meses evento pueden solaparse.
No se volvieron a seleccionar modelos por prueba. Las cifras están en evidencias/datos.

Ejemplo regional: arroz, diciembre de 2024, Colombia/Ecuador/Perú. Mediana original USD=2,468620 pp;
cambio mensual=-1,581992 pp; cobertura 3/3. Su escala difiere de la volatilidad local del SAT.
