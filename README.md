# Trekrisk: clima y probabilidad para planificar salidas de trekking

Aplicación web en Streamlit que responde una pregunta práctica de un guía de trekking:

> ¿Qué probabilidad hay de que un día sea **apto** para salir, según el clima real de cada punto de trekking de Córdoba y la época del año?

Trabajo integrador final de Estadística y Probabilidad Aplicada (ISAUI / Universidad Provincial de Córdoba, Sede Villa Carlos Paz). La especificación completa está en [`SPEC.md`](SPEC.md).

Se usan **solo datos climáticos reales**: 5 años (2021-01-01 a 2025-12-31) de 5 zonas, 1.826 días por zona (9.130 filas). No se simulan datos; el único "sorteo" es el remuestreo con reposición de días reales.

## Instalación

Requiere Python 3.10 o superior (probado con 3.14).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

```bash
streamlit run app.py             # interfaz web, se abre en http://localhost:8501
pytest                           # pruebas de core/
```

Los datos ya vienen guardados en `data/`, por lo que la app funciona **sin internet**. Son datos de archivo: la interfaz no descarga ni actualiza nada. `core/api.py` queda como registro de cómo se obtuvieron.

### Tablero

La app es un único tablero. Arriba se eligen las **zonas** (se pueden comparar varias) y el rango de fechas; en la barra lateral se editan los umbrales.

| Umbral | Valor por defecto | Significado |
| --- | --- | --- |
| Lluvia | 1,0 mm | precipitación ≥ umbral es un día lluvioso |
| Viento | 30 km/h | viento máximo ≥ umbral es viento fuerte |
| Calor | 32 °C | temperatura máxima ≥ umbral es calor extremo |
| Helada | 0 °C | temperatura mínima ≤ umbral es helada |

Un día es **apto** si no hay lluvia, ni viento fuerte, ni temperatura extrema (calor o helada). El botón "Restablecer umbrales" vuelve a los valores por defecto.

| Fila | Contenido |
| --- | --- |
| 1 | Métricas: día apto, zona y mes con más días aptos, lluvia, viento fuerte y temperatura extrema |
| 2 | Frecuencia de un evento por mes y zona; los 8 resultados posibles |
| 3 | Mapa de calor de P(apto) por zona y mes; mejores y peores combinaciones |
| 4 | Experimento aleatorio (remuestreo de días reales); independencia entre eventos |
| 5 | Datos crudos |

Cada resultado muestra la cantidad de casos que lo respaldan (con una advertencia si son menos de 30) y una línea de interpretación. La teoría de cada tema se desarrolla en la presentación.

## Estructura

```
app.py                  # entrada de Streamlit: barra lateral y tablero
interfaz/               # formato, filtros y tarjetas del tablero
core/                   # lógica pura, sin importar Streamlit
  config.py  api.py  datos.py  eventos.py
  probabilidad.py  simulacion.py  interpretacion.py
data/                   # un CSV por zona (clima_<slug>.csv), versionados en git
tests/                  # pruebas de core/ con pytest
.streamlit/config.toml  # tema visual
```

## Fuente de los datos

[Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) (`https://archive-api.open-meteo.com/v1/archive`), sin API key y para uso no comercial. Los datos provienen del reanálisis ERA5. Variables diarias pedidas: `precipitation_sum`, `wind_speed_10m_max`, `wind_gusts_10m_max`, `temperature_2m_max` y `temperature_2m_min`, en mm, km/h y °C, con zona horaria `America/Argentina/Cordoba`.

Zonas:

| Zona | Latitud | Longitud |
| --- | --- | --- |
| Cerro Champaquí | -31,97 | -64,93 |
| Cerro Uritorco | -30,84 | -64,46 |
| Quebrada del Condorito | -31,65 | -64,64 |
| Pan de Azúcar | -31,24 | -64,46 |
| Los Gigantes | -31,57 | -64,80 |

## Limitaciones

- La grilla del reanálisis es del orden de 10 a 25 km: zonas cercanas pueden dar valores casi idénticos y el **microclima de cumbre no queda capturado**.
- No se informa la altitud de las cumbres a la API. Open-Meteo ajusta la temperatura a la altitud del terreno en las coordenadas pedidas, que queda por debajo de la cumbre: las temperaturas están sesgadas hacia el calor (entre 1 y 2,5 °C en la mayoría de las zonas y hasta unos 6 °C en la Quebrada del Condorito, cuyas coordenadas caen en el valle), lo que afecta sobre todo a las heladas.
- Las probabilidades frecuenciales son estimaciones basadas en 5 años: suponen que el clima futuro se comporta como el registrado. Las combinaciones zona-mes se apoyan en unos 150 días cada una.
- Los umbrales de día apto no fueron validados con guías de trekking; son editables para probar alternativas.
- El análisis es descriptivo: no es un pronóstico del tiempo.

## Qué no se usa y por qué

- **Regresión:** no se predice una variable continua; se estiman probabilidades de eventos.
- **Inferencia (intervalos de confianza y tests de hipótesis):** se analiza el registro completo de 5 años y la pregunta se responde con probabilidades empíricas, sin generalizar desde una muestra.

## Licencia

Ver [`LICENSE`](LICENSE).
