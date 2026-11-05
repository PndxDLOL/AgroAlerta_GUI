# AgroAlerta SAT V1

Generado: 2026-11-03T11:07:12.856203-05:00. Corte observado: 2024-12-01.

Se evaluó un evento de volatilidad de tres retornos por encima del percentil 90 de calibración.
Umbral de prueba fijo hasta 2022-12-01; horizonte de un mes.
Modelos comparados en la misma intersección de casos observados elegibles. No se eligió un ganador definitivo.

## Resultados de prueba en casos comunes

| modelo | N | eventos | TP | FP | FN | TN | precision | sensibilidad | F1 | falsas_alarmas_entre_alertas | tasa_falsos_positivos | omisiones |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ARIMA | 144.0000 | 17.0000 | 10.0000 | 0.0000 | 7.0000 | 127.0000 | 1.0000 | 0.5882 | 0.7407 | 0.0000 | 0.0000 | 0.4118 |
| Deriva | 144.0000 | 17.0000 | 10.0000 | 0.0000 | 7.0000 | 127.0000 | 1.0000 | 0.5882 | 0.7407 | 0.0000 | 0.0000 | 0.4118 |
| Holt amortiguado | 144.0000 | 17.0000 | 10.0000 | 0.0000 | 7.0000 | 127.0000 | 1.0000 | 0.5882 | 0.7407 | 0.0000 | 0.0000 | 0.4118 |
| Holt-Winters | 144.0000 | 17.0000 | 10.0000 | 0.0000 | 7.0000 | 127.0000 | 1.0000 | 0.5882 | 0.7407 | 0.0000 | 0.0000 | 0.4118 |
| Ingenuo | 144.0000 | 17.0000 | 10.0000 | 0.0000 | 7.0000 | 127.0000 | 1.0000 | 0.5882 | 0.7407 | 0.0000 | 0.0000 | 0.4118 |
| Ingenuo estacional | 144.0000 | 17.0000 | 13.0000 | 40.0000 | 4.0000 | 87.0000 | 0.2453 | 0.7647 | 0.3714 | 0.7547 | 0.3150 | 0.2353 |
| LSTM | 144.0000 | 17.0000 | 13.0000 | 24.0000 | 4.0000 | 103.0000 | 0.3514 | 0.7647 | 0.4815 | 0.6486 | 0.1890 | 0.2353 |
| MLP | 144.0000 | 17.0000 | 13.0000 | 21.0000 | 4.0000 | 106.0000 | 0.3824 | 0.7647 | 0.5098 | 0.6176 | 0.1654 | 0.2353 |
| Random Forest AR | 144.0000 | 17.0000 | 12.0000 | 14.0000 | 5.0000 | 113.0000 | 0.4615 | 0.7059 | 0.5581 | 0.5385 | 0.1102 | 0.2941 |
| Ridge AR | 144.0000 | 17.0000 | 11.0000 | 2.0000 | 6.0000 | 125.0000 | 0.8462 | 0.6471 | 0.7333 | 0.1538 | 0.0157 | 0.3529 |
| SARIMA | 144.0000 | 17.0000 | 10.0000 | 0.0000 | 7.0000 | 127.0000 | 1.0000 | 0.5882 | 0.7407 | 0.0000 | 0.0000 | 0.4118 |
| SES | 144.0000 | 17.0000 | 10.0000 | 0.0000 | 7.0000 | 127.0000 | 1.0000 | 0.5882 | 0.7407 | 0.0000 | 0.0000 | 0.4118 |
| Persistencia de volatilidad | 144.0000 | 17.0000 | 11.0000 | 7.0000 | 6.0000 | 120.0000 | 0.6111 | 0.6471 | 0.6286 | 0.3889 | 0.0551 | 0.3529 |

N, TP, FP, FN y TN son conteos. Las otras medidas son proporciones entre 0 y 1; NaN significa no calculable.
Las etiquetas requieren precios originales positivos. Se conservan los motivos de exclusión.
Los resultados de todos los modelos y exclusiones están en evaluacion_alertas.csv.

## Alcance de la evidencia

La tabla de pruebas funcionales verifica llaves y tres entradas artificiales de la regla. Las pruebas de interfaz
automatizadas se ejecutan aparte con pytest y AppTest. No son una validación de utilidad con usuarios.
Los indicadores comerciales son candidatos: su correspondencia física entre dominios continúa pendiente.
La aplicación muestra resultados anuales en su frecuencia y no los convierte en meses independientes.
No se validaron huecos de 36 meses ni se calibra inseguridad alimentaria.
