## Qué representan los diez KPI

P es el precio al productor en moneda local por tonelada; TC es la tasa LCU por USD; Q es producción,
A es área cosechada, M es importación y X es exportación. Las cantidades comerciales deben estar en toneladas.

| KPI | Cálculo | Frecuencia y lectura |
| --- | --- | --- |
| Precio al productor | P | Mensual; conserva moneda local para el modelo |
| Precio en dólares | P / TC | Mensual; USD nominales, sin ajuste por inflación |
| Retorno logarítmico | 100 × ln(Pt / Pt−1) | Mensual; dos precios positivos consecutivos |
| Volatilidad | Desviación muestral de los últimos tres retornos (ddof=1) | Mensual; cuatro precios positivos consecutivos |
| Producción | Q | Anual, toneladas |
| Área cosechada | A | Anual, hectáreas |
| Productividad calculada | Q / A | Anual, t/ha; A debe ser positivo |
| Exposición importadora candidata | 100 × M / Q | Anual; Q positivo; no es proporción del consumo |
| Exposición exportadora candidata | 100 × X / Q | Anual; Q positivo |
| Oferta parcial candidata | Q + M − X | Anual; no es un balance alimentario |

Las cantidades compuestas de comercio se muestran como **candidatas** hasta documentar equivalencia física
entre PP, QCL y TCL. Arroz en cáscara, arroz elaborado y otros rubros no se pueden sumar sin armonización.
La productividad calculada se distingue del rendimiento declarado en la fuente, que también se conserva.

Los datos anuales se representan como años; no se multiplican por doce para crear observaciones mensuales.
La comparación regional utiliza precios USD **originales**, coincidencias por par y al menos doce meses.
La correlación describe asociación; no prueba causalidad ni determina por sí sola la imputación.

## Procedencia y datos ausentes

Cada medida conserva `__original`, la serie preparada y `__imputado`. La aplicación comprueba que ningún
original haya cambiado. Si falta una fila del calendario, la genera con NaN, sin interpolar el precio.
`__usa_imputacion` señala que un indicador depende de una o más entradas estimadas: dos precios para un
retorno y cuatro para una volatilidad. Los puntos y celdas naranjas indican esas estimaciones, también con
rombos y leyendas. Los NaN que todavía persistan se mantienen.

La curva descriptiva usa la base V4 preparada. Para pronosticar, el motor vuelve a los originales y aplica
KNN dentro de cada corte temporal. Ajusta la escala y los vecinos antes de cada hueco, conserva los
originales y no consulta períodos posteriores al origen. Las respuestas imputadas no entrenan como
etiquetas en los modelos supervisados de rezagos. Los donantes regionales pueden corresponder a fechas
simultáneas ya observadas antes del corte; su disponibilidad real de publicación no está verificada.

## Reglas SAT V1

Los valores de `config/reglas.json` son decisiones operativas iniciales. No se optimizaron para mostrar una
mejor puntuación en 2023–2024. No son umbrales de crisis ni evidencia de utilidad de decisiones públicas.

| Regla | Condición | Salida y función |
| --- | --- | --- |
| R1 Volatilidad mensual | Sigma > percentil 90 de volatilidades originales anteriores | Volatilidad alta |
| R1 Vigilancia | Percentil 75 < sigma ≤ percentil 90 | Vigilancia |
| R1 Sin disparo | Sigma ≤ percentil 75 | Sin señal estadística |
| R1 Elegibilidad | Menos de 24 volatilidades de calibración, precio no positivo o entradas originales recientes insuficientes | No evaluable; nunca equivale a normal |
| R2 Producción | Cambio anual original de Q < −10 % | Vigilancia contextual, separada de R1 |
| R3 Exposición importadora | M/Q > 1 | Revisión contextual; deshabilitada hasta validar comparabilidad |
| R4 Oferta parcial | Q+M−X ≤ 0 | Revisión contextual; deshabilitada hasta validar comparabilidad |
| R5 Calidad | Menos de 80 % de precios originales en los últimos doce meses disponibles | Revisar calidad; no es una alerta de mercado |

R2–R4 consultan años hasta **año del origen menos dos**, supuesto de disponibilidad pendiente de contrastar
con las publicaciones. El parámetro `annual_lag` controla ese contexto. El 80 % local de R5 es un control
del prototipo; no reemplaza el límite global de faltantes del proyecto.

R3 y R4 solo se activan si se registra, por mercado, una evidencia revisada:

```json
"comparabilidad": {
  "Colombia|Arroz": {"validada": true, "evidencia": "Ruta al acta que comprueba unidad y equivalencia del rubro"}
}
```

El archivo entregado deja `comparabilidad` vacío porque esa verificación no se ha acreditado.
Las reglas se muestran por separado; no se suman en un índice arbitrario de inseguridad alimentaria.

## Horizonte y evaluación de R1

La detección histórica calcula sigma del mes ya observado y la contrasta con percentiles calculados hasta
el mes anterior. Detectar un episodio histórico no significa haberlo anticipado.

La anticipación usa un pronóstico de **un mes**: se combina su retorno implícito con los dos retornos
anteriores originales. Por eso exige los tres precios originales consecutivos más recientes. Si faltan,
puede existir un escenario de precios imputados, pero la señal SAT estricta queda No evaluable.

Para evaluar, la verdad se calcula únicamente con precios originales. Comparar también con persistencia
de volatilidad requiere cinco precios originales consecutivos. Esta restricción define casos comunes
entre modelos y referencia; se exportan exclusiones y motivos, sin convertirlos en aciertos.

La prueba usa los últimos 24 meses: en la muestra incluida es enero 2023–diciembre 2024, con umbral fijo
calculado hasta diciembre 2022. La validación anterior usa umbrales móviles hasta cada origen. El archivo
V1 aporta predicciones de un paso y entrenamiento por corte. Los resultados son **retrospectivos y
exploratorios** porque 2023–2024 ya se había examinado durante el proyecto. No constituyen una nueva
prueba ciega. Elegir otro conjunto de modelos puede reducir la intersección y cambiar N.

TP: alerta y evento; FP: alerta sin evento; FN: evento omitido; TN: ausencia de ambos.
Precisión = TP/(TP+FP); sensibilidad = TP/(TP+FN); F1 = 2TP/(2TP+FP+FN).
Fracción de falsas alarmas = FP/(TP+FP); tasa de falsos positivos = FP/(FP+TN).
Omisión = FN/(TP+FN). Los denominadores cero se representan como no calculables.

El laboratorio ofrece estabilidad, choque hipotético de +30 % y corte de tres meses. Son entradas
artificiales para verificar reglas; se excluyen de todas las métricas de mercados.

## Alcance predictivo

Los escenarios permiten modelos ingenuos, deriva, suavizamientos, ARIMA, SARIMA, Ridge, bosque aleatorio
y MLP. El ranking importado conserva LSTM cuando el notebook pudo evaluarlo; el motor interactivo no
entrena LSTM. Los parámetros se mantienen simples y se registran fallos de convergencia y elegibilidad.
No se supone estacionalidad de doce años en datos anuales. No se crean etiquetas artificiales para
habilitar redes con muestras anuales pequeñas.

Los escenarios multipaso son puntuales, sin intervalos calibrados; su eficiencia no fue validada con la
prueba de un paso. Con datos hasta 2024, las curvas desde 2025 son escenarios desde un corte histórico,
no predicciones actualizadas al calendario de 2026. El modelo definitivo continúa en evaluación.

## Comparación regional incorporada en interfaz V2

Se comparan precios originales y preparados del mismo producto en USD nominales. Cada país aporta la
volatilidad muestral de tres retornos USD. El indicador conjunto es su mediana, con mínimo dos países
y cobertura completa de una canasta fija. Si falta uno, la mediana original no se calcula. La variación
requiere dos meses consecutivos completos y se expresa en pp. La curva preparada resalta imputaciones.
No activa alertas regionales ni mide la volatilidad de una cartera o de toda América Latina.

Resultados V1 del notebook muestra el CSV predictivo asociado por huellas a estas bases. Pronósticos
de un paso con orígenes actualizados difieren de un escenario multipaso con un solo ajuste. Las medias
suaves no se modifican con ruido. Interfaz V2 no significa una nueva validación de Predicción V2.
