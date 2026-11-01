# Trekrisk: clima y probabilidad para planificar salidas de trekking

Aplicación web en Streamlit que responde una pregunta práctica de un guía de trekking:

> ¿Qué probabilidad hay de que un día sea **apto** para salir, según el clima real de cada punto de trekking de Córdoba y la época del año?

Trabajo integrador final de Estadística y Probabilidad Aplicada (ISAU / Universidad Provincial de Córdoba, Sede Villa Carlos Paz). La especificación completa está en [`SPEC.md`](SPEC.md).

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

Los datos ya vienen guardados en `data/`, por lo que la app funciona **sin internet**. La descarga es una acción explícita: botón "Descargar o actualizar datos" en la pantalla Datos.

### Barra lateral

Los filtros se aplican igual en todas las pantallas: zonas, rango de fechas, umbrales y semilla del sorteo.

| Umbral | Valor por defecto | Significado |
| --- | --- | --- |
| Lluvia | 1,0 mm | precipitación ≥ umbral es un día lluvioso |
| Viento | 30 km/h | viento máximo ≥ umbral es viento fuerte |
| Calor | 32 °C | temperatura máxima ≥ umbral es calor extremo |
| Helada | 0 °C | temperatura mínima ≤ umbral es helada |

Un día es **apto** si no hay lluvia, ni viento fuerte, ni temperatura extrema (calor o helada). El botón "Restablecer umbrales" vuelve a los valores por defecto. La semilla por defecto es 42.

### Pantallas

| N.º | Pantalla | Contenido de la materia |
| --- | --- | --- |
| 1 | Datos | descarga, estado de la caché, validación, tipos de variable, estadística descriptiva |
| 2 | Eventos y espacio muestral | experimento aleatorio, espacio muestral (8 resultados), eventos |
| 3 | Frecuencias relativas | frecuencia relativa por zona, mes o estación |
| 4 | Probabilidad clásica y frecuencial | sorteo equiprobable y estabilización de la frecuencia |
| 5 | Probabilidad condicional | P(A \| B) y mapa de calor zona × mes |
| 6 | Independencia | los 6 pares entre A, B, C y D |
| 7 | Experimento aleatorio | remuestreo de días reales y convergencia |
| 8 | Recomendación | mejores y peores combinaciones zona-mes, mejor estación |

Cada resultado muestra su fórmula, la cantidad de casos que lo respaldan (con una advertencia si son menos de 30) y una interpretación en texto.

## Estructura

```
app.py                  # entrada de Streamlit: navegación y barra lateral
paginas/                # una pantalla por archivo
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
- No se informa la altitud de las cumbres a la API ni se ajusta la temperatura por altitud.
- Las probabilidades frecuenciales son estimaciones basadas en 5 años: suponen que el clima futuro se comporta como el registrado. Las combinaciones zona-mes se apoyan en unos 150 días cada una.
- Los umbrales de día apto no fueron validados con guías de trekking; son editables para probar alternativas.
- El análisis es descriptivo: no es un pronóstico del tiempo.

## Qué no se usa y por qué

- **Regresión:** no se predice una variable continua; se estiman probabilidades de eventos.
- **Inferencia (intervalos de confianza y tests de hipótesis):** se analiza el registro completo de 5 años y la pregunta se responde con probabilidades empíricas, sin generalizar desde una muestra.

## Licencia

Ver [`LICENSE`](LICENSE).
