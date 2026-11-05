## Registro de comentarios y alcance

Los comentarios del equipo se incorporan como hipótesis y tareas de investigación. La interfaz del piloto
es V2; los resultados predictivos que reproduce siguen siendo V1. Todavía no se entrenó ni validó un
nuevo sistema probabilístico de anticipación. La presentación debe describir un prototipo de monitoreo
de volatilidad con escenarios y reglas experimentales.

| Tema recibido | Acción para Predicción V2 | Estado y evidencia necesaria |
| --- | --- | --- |
| Ingenuo lideró validación agregada | Conservar Ingenuo y persistencia como referencias; comparar errores en los mismos casos y por mercado | Pendiente. El promedio agregado no demuestra que ningún modelo gane en un mercado particular |
| Anticipar el evento directamente | Evaluar un clasificador probabilístico de volatilidad alta, además del pronóstico de precio | Investigación futura; calibración y evaluación cronológica separadas |
| Horizonte útil de 3 y 6 meses | Definir de antemano evento y horizonte; evaluar ambos sin elegir con la prueba | Futuro. El escenario multipaso de la interfaz no equivale a esa validación |
| Variables externas | Priorizar tipo de cambio rezagado y precios internacionales del mismo producto; después fertilizantes, petróleo, ENSO/lluvias e inflación | Futuro. Confirmar cobertura, unidad, licencia y fecha efectiva de disponibilidad |
| Precios reales | Comparar precio nominal con precio local deflactado por IPC y base documentada | Futuro. USD nominales no equivalen a dólares constantes |
| Más países y productos | Evaluar modelos de panel con identidad de mercado y escalamiento ajustado en entrenamiento | Futuro. Aumentar filas no garantiza más eventos independientes |
| Comercio anual de Colombia | Auditar fuente, código de rubro, unidad y posibles cambios de cobertura antes de corregir el valor de 2024 | Pendiente prioritario. No borrar ni winsorizar automáticamente el salto |
| Huecos largos e imputación | Analizar sensibilidad en historia original, imputada y mixta; estudiar incertidumbre de reconstrucción | Pendiente. No asignar un peso arbitrario ni tratar imputaciones como etiquetas reales |
| Prueba ciega | Reservar nuevos períodos publicados y no utilizados por el equipo; registrar fecha de extracción y congelar decisiones | Futuro. 2025-2026 solo serían elegibles si existen y no se han consultado; no se asume 2026 completo |
| Umbrales e incertidumbre | Estimar intervalos, probabilidades calibradas y costos de FP/FN con datos de desarrollo | Futuro. Percentiles 75/90 siguen siendo reglas iniciales |
| Disponibilidad real de fuentes | Registrar fecha de publicación/vintage y simular qué estaba disponible en cada origen | Pendiente. El rezago anual de dos años es un supuesto, no una fecha comprobada |

### Qué se implementó en el piloto gráfico V2

- Selector de apariencia claro/oscuro por sesión.
- Comparación del mismo producto entre países en USD nominales, con procedencia y cobertura.
- Mediana regional de volatilidades nacionales y su cambio mensual, como descripción exploratoria.
- Gráfica y descarga de predicciones V1 reales, separadas de escenarios futuros con zoom reciente.
- Lectura UTF-8 explícita para corregir el fallo de Trazabilidad en Windows.
- Instructivo PDF, plantilla Excel, plantillas CSV y conversor con validación del contrato.

Estas mejoras de uso no cambian la eficacia predictiva V1 ni demuestran anticipación de crisis.

### Diseño propuesto para el próximo experimento

1. Auditar el comercio y los huecos; congelar una versión de datos y un registro de cambios.
2. Mantener `fecha` como período analítico. Añadir metadatos de publicación y extracción, sin crear dos
   calendarios analíticos. En cada corte, usar solo lo efectivamente publicado.
3. Definir el evento antes de entrenar. Una opción a estudiar es "al menos un mes de volatilidad alta
   en los próximos h meses", h=3 o 6, con umbral fijado usando entrenamiento. Contrastar también el
   pronóstico a un mes. Las etiquetas de evaluación requieren precios originales suficientes.
4. Usar validación de origen móvil y separación temporal. Por el solapamiento de etiquetas futuras,
   aplicar separación de al menos h meses entre entrenamiento y validación cuando corresponda.
   Calibrar probabilidades dentro de desarrollo, nunca con la prueba final.
5. Empezar por modelos sencillos interpretables (por ejemplo, regresión logística regularizada) y un
   candidato no lineal. Entrenar un panel solo si hay datos y eventos suficientes. Redes profundas no
   se habilitan únicamente por aumentar datos imputados.
6. Comparar con frecuencia histórica del evento, persistencia de volatilidad e Ingenuo bajo la misma
   definición de alerta. Medir sensibilidad, precisión, falsas alarmas, omisiones, Brier y calibración.
   Para precios, mantener MAE, RMSE, nMAE y MASE con la misma referencia por corte.
7. Reportar resultados por mercado y agregados, cobertura y costo de errores. Cuantificar incertidumbre
   respetando dependencia temporal y agrupación de episodios; los 17 meses evento V1 no son 17
   episodios independientes. MASE > 1 usa una escala histórica: no reemplaza una comparación directa
   con Ingenuo en las mismas fechas de prueba.
8. Ejecutar una sola evaluación final en períodos nuevos que realmente permanezcan sin examinar.
   Si no se supera a las referencias o no hay muestra suficiente, conservar esa conclusión.

### Criterio de cierre

No declarar anticipación demostrada por una curva más variable, un único promedio favorable o una
diferencia pequeña sin estudiar su estabilidad. La evidencia futura debe mostrar ventaja consistente
frente a las referencias, en varios mercados y con probabilidades calibradas. La descripción y el
monitoreo siguen siendo resultados útiles si esa ventaja no se obtiene.
