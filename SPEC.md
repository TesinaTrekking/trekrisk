# SPEC – Análisis probabilístico del clima para planificar salidas de trekking

**Asignatura:** Estadística y Probabilidad Aplicada (ISAUI / Universidad Provincial de Córdoba, Sede Villa Carlos Paz).
**Estado:** implementada. Este documento es la referencia de diseño y la documentación del sistema tal como quedó; las decisiones están cerradas.

---

## 1. Objetivo

Aplicación web en Streamlit que responde una pregunta práctica de un guía de trekking:

> ¿Qué probabilidad hay de que un día sea **apto** para salir, según el clima real de cada punto de trekking de Córdoba y la época del año?

Se usan **solo datos climáticos reales** de Open-Meteo (5 años, 5 zonas). No hay datos simulados.

El sistema debe aplicar estos contenidos de la materia, cada uno resuelto en `core/` con su resultado, sus casos y una interpretación en texto (la teoría se desarrolla en la presentación). El tablero muestra los que tienen visualización propia; la probabilidad clásica y el sorteo equiprobable quedan en `core/` sin pantalla (ver `docs/adr/0001-tablero-unico.md`):

1. Experimento aleatorio
2. Espacio muestral
3. Eventos
4. Frecuencia relativa
5. Probabilidad clásica
6. Probabilidad frecuencial
7. Probabilidad condicional
8. Independencia de eventos

De apoyo: estadística descriptiva básica y una recomendación final por zona y mes.

## 2. Alcance

**Dentro:** datos de archivo en CSV (la descarga queda como registro de procedencia), los 8 contenidos, estadística descriptiva, umbrales editables, recomendación, interfaz web, pruebas de `core/`.

**Fuera de alcance:** incidentes, pronóstico, regresión, inferencia (intervalos, tests), base de datos, login, despliegue, interfaz de consola/CLI, integración con la app de gestión de trekking, ajuste por altitud de las cumbres.

Se ejecuta desde la consola con `streamlit run app.py`, y eso cumple el mínimo de la consigna. No se hace un modo CLI aparte.

## 3. Datos

**Fuente:** Open-Meteo Historical Weather API, sin API key (uso no comercial). Endpoint: `https://archive-api.open-meteo.com/v1/archive`. Los datos provienen de reanálisis (ERA5). El README y la interfaz deben citar a Open-Meteo como fuente.

**Período fijo:** `2021-01-01` a `2025-12-31` (5 años calendario, **1.826 días** por zona, 9.130 filas en total).

**Zonas (confirmadas):**

| slug | nombre | latitud | longitud |
| --- | --- | --- | --- |
| `champaqui` | Cerro Champaquí | -31.97 | -64.93 |
| `uritorco` | Cerro Uritorco | -30.84 | -64.46 |
| `condorito` | Quebrada del Condorito | -31.65 | -64.64 |
| `pan_de_azucar` | Pan de Azúcar | -31.24 | -64.46 |
| `los_gigantes` | Los Gigantes | -31.57 | -64.80 |

**Variables diarias a pedir** (parámetro `daily`): `precipitation_sum`, `wind_speed_10m_max`, `wind_gusts_10m_max`, `temperature_2m_max`, `temperature_2m_min`. Zona horaria: `America/Argentina/Cordoba`. Unidades: mm, km/h y °C.

**Respuesta esperada:** JSON con un objeto `daily` que tiene la lista `time` y una lista por cada variable pedida.

**Caché:** un CSV por zona en `data/clima_<slug>.csv`, versionado en git. La app funciona sin internet. La interfaz no descarga datos: los CSV son datos de archivo y `core/api.py` queda como registro de su procedencia.

**Esquema del CSV** (una fila por día):

| columna | tipo | origen |
| --- | --- | --- |
| `zona` | texto (slug) | definida por el proyecto |
| `fecha` | fecha `AAAA-MM-DD` | `daily.time` |
| `precipitacion_mm` | decimal | `precipitation_sum` |
| `viento_kmh` | decimal | `wind_speed_10m_max` |
| `racha_kmh` | decimal | `wind_gusts_10m_max` |
| `tmax_c` | decimal | `temperature_2m_max` |
| `tmin_c` | decimal | `temperature_2m_min` |

**Limitación a documentar:** la grilla del reanálisis es del orden de 10 a 25 km, por lo que zonas cercanas pueden dar valores casi idénticos y el microclima de cumbre no queda capturado.

## 4. Variables derivadas

Las agrega `core/datos.py` al cargar:

| columna | tipo | definición |
| --- | --- | --- |
| `anio` | entero | año de `fecha` |
| `mes` | entero 1–12 | mes de `fecha` |
| `estacion` | texto | hemisferio sur: `verano` (dic, ene, feb), `otoño` (mar, abr, may), `invierno` (jun, jul, ago), `primavera` (sep, oct, nov) |

Clasificación estadística (se verifica con `validar` y `resumen_descriptivo`; el tablero no la muestra):

- `zona`: cualitativa nominal. `fecha`: temporal.
- `precipitacion_mm`, `viento_kmh`, `racha_kmh`, `tmax_c`, `tmin_c`: cuantitativas continuas.
- `mes`: cualitativa ordinal. `estacion`: cualitativa nominal.

## 5. Experimento, espacio muestral y eventos

**Experimento aleatorio:** observar el clima de un día en una zona.

**Umbrales por defecto** (`Umbrales`, editables en la barra lateral):

| parámetro | valor | significado |
| --- | --- | --- |
| `lluvia_mm` | 1.0 | un día con precipitación ≥ 1 mm es lluvioso |
| `viento_kmh` | 30.0 | viento máximo ≥ 30 km/h es viento fuerte |
| `calor_c` | 32.0 | `tmax_c` ≥ 32 °C es calor extremo |
| `helada_c` | 0.0 | `tmin_c` ≤ 0 °C es helada |

**Eventos** (columnas booleanas que agrega `core/eventos.py`; todas se recalculan al cambiar un umbral):

| columna | evento | definición |
| --- | --- | --- |
| `lluvia` | A | `precipitacion_mm >= lluvia_mm` |
| `viento_fuerte` | B | `viento_kmh >= viento_kmh` (umbral) |
| `temp_extrema` | C | `tmax_c >= calor_c` **o** `tmin_c <= helada_c` |
| `lluvia_ayer` | D | `lluvia` del día anterior **en la misma zona**. El primer día de cada zona queda como `<NA>` y se excluye de los cálculos que usen D |
| `apto` | — | `~lluvia & ~viento_fuerte & ~temp_extrema` (es Aᶜ ∩ Bᶜ ∩ Cᶜ) |
| `adverso` | — | `~apto` (es A ∪ B ∪ C) |

Los eventos de tiempo y lugar (pertenecer a un mes, una estación o una zona) se filtran con las columnas `mes`, `estacion` y `zona`.

**Espacio muestral:** cada día cae en uno de 2 × 2 × 2 = **8 resultados elementales** según si ocurren o no A, B y C. `espacio_muestral(df)` devuelve una tabla de 8 filas con los casos y la frecuencia relativa de cada una. Los 8 resultados **no son equiprobables**. Se muestra también la columna `apto`/`adverso` correspondiente.

## 6. Herramientas estadísticas y fórmulas

Las fórmulas se desarrollan en la presentación; el tablero no las muestra.

```
Frecuencia relativa:      fr(E) = casos con E / casos totales
Probabilidad clásica:     P(E)  = casos favorables / casos posibles   (sorteo equiprobable)
Probabilidad frecuencial: P(E) ≈ fr(E) observada en el historial      (estimación para un día futuro)
Condicional:              P(A | B) = P(A ∩ B) / P(B)  =  n(A ∩ B) / n(B)
Independencia:            A y B independientes  ⇔  P(A ∩ B) = P(A) · P(B)
```

**Diferencia entre clásica y frecuencial (se explica en la presentación; el tablero no la muestra):**

- *Clásica:* se sortea una fecha, un mes o una zona del registro y todos los casos son equiprobables, por lo que el cálculo es exacto dentro del registro.
- *Frecuencial:* se usa la frecuencia observada como estimación de la probabilidad de un día futuro, y se muestra cómo se estabiliza al sumar días.

**Criterio de independencia:** se consideran independientes dos eventos si `|P(A ∩ B) − P(A)·P(B)| < ε` con **ε = 0,02** (2 puntos porcentuales). Además se muestra `P(A | B)` frente a `P(A)`. Pares a evaluar: todos los pares entre A, B, C y D (6 pares). El par (A, D) ilustra que los días consecutivos no son independientes.

**Mínimo de casos:** si un resultado se apoya en menos de **30 casos** se muestra una advertencia.

**Qué NO se usa y por qué (debe figurar en el README):** regresión, porque no se predice una variable continua; inferencia (intervalos y tests), porque se analiza el registro completo de 5 años y la pregunta se responde con probabilidades empíricas.

## 7. Experimento aleatorio (simulación)

`simular` hace un **remuestreo con reposición de días reales** del registro filtrado: elige `n` filas al azar con `numpy.random.default_rng(semilla)` y calcula la frecuencia relativa acumulada del evento elegido. **No se generan datos nuevos.** Se compara la frecuencia final con la probabilidad del registro y se grafica la convergencia. Misma semilla, mismo resultado.

## 8. Contratos de los módulos (`core/`)

Firmas de los módulos tal como están implementados. El tablero y las pruebas dependen de estos nombres y formas de retorno.

```python
# core/config.py
@dataclass(frozen=True)
class Zona: slug: str; nombre: str; latitud: float; longitud: float
ZONAS: tuple[Zona, ...]            # las 5 zonas de la sección 3
FECHA_INICIO = "2021-01-01"; FECHA_FIN = "2025-12-31"; DIAS_ESPERADOS = 1826
EPSILON_INDEPENDENCIA = 0.02; MIN_CASOS = 30
@dataclass(frozen=True)
class Umbrales: lluvia_mm: float = 1.0; viento_kmh: float = 30.0; calor_c: float = 32.0; helada_c: float = 0.0

# core/api.py
class ErrorDescarga(Exception): ...
def descargar_zona(zona: Zona, inicio: str, fin: str) -> pd.DataFrame        # esquema del CSV
def guardar_csv(df: pd.DataFrame, zona: Zona, carpeta: str = "data") -> Path
def descargar_todas(carpeta: str = "data") -> dict[str, int]                 # slug -> filas guardadas

# core/datos.py
def cargar_clima(carpeta: str = "data", zonas: list[str] | None = None) -> pd.DataFrame  # agrega anio, mes, estacion
def validar(df: pd.DataFrame) -> list[str]        # lista de problemas; vacía si todo está bien
def resumen_descriptivo(df: pd.DataFrame) -> pd.DataFrame  # media, mediana, desvío, mín, máx, p25, p75 por variable

# core/eventos.py
def marcar_eventos(df: pd.DataFrame, umbrales: Umbrales) -> pd.DataFrame   # agrega las columnas de la sección 5
def espacio_muestral(df: pd.DataFrame) -> pd.DataFrame                     # 8 filas: lluvia, viento_fuerte, temp_extrema, casos, frecuencia_relativa

# core/probabilidad.py
@dataclass(frozen=True)
class Resultado:
    valor: float | None        # None si no se puede calcular (por ejemplo P(B) = 0)
    favorables: int
    totales: int
    @property
    def poca_muestra(self) -> bool: ...        # totales < MIN_CASOS

def frecuencia_relativa(evento: pd.Series, universo: pd.Series | None = None) -> Resultado
def frecuencias_por_grupo(df: pd.DataFrame, evento: str, por: str | list[str]) -> pd.DataFrame
    # columnas: grupo(s), favorables, totales, frecuencia_relativa
def grupo_mas_probable(df: pd.DataFrame, evento: str, por: str) -> tuple[object, Resultado] | None
    # grupo con mayor frecuencia del evento; desempata por más casos; None si no hay datos
def probabilidad_clasica_fecha(df: pd.DataFrame, evento: str) -> Resultado     # cada fecha del registro equiprobable
def probabilidad_clasica_uniforme(opciones: Sequence, favorables: Collection) -> Resultado  # sorteo de zona o mes
def probabilidad_frecuencial(evento: pd.Series) -> Resultado
def convergencia(evento: pd.Series) -> pd.DataFrame                            # columnas: n, frecuencia_acumulada (orden cronológico)
def probabilidad_condicional(a: pd.Series, b: pd.Series) -> Resultado          # P(A|B); valor None si n(B)=0
def matriz_condicional(df: pd.DataFrame, evento: str, filas: str = "zona", columnas: str = "mes") -> pd.DataFrame
    # P(evento | fila, columna) con casos; formato largo: fila, columna, favorables, totales, probabilidad
@dataclass(frozen=True)
class ResultadoIndependencia:
    p_a: float; p_b: float; p_ab: float; producto: float; diferencia: float
    p_a_dado_b: float | None; independientes: bool; casos: int
def independencia(a: pd.Series, b: pd.Series, epsilon: float = EPSILON_INDEPENDENCIA) -> ResultadoIndependencia
def matriz_independencia(df: pd.DataFrame, eventos: list[str], epsilon: float = EPSILON_INDEPENDENCIA) -> pd.DataFrame
def ranking_zona_mes(df: pd.DataFrame) -> pd.DataFrame     # P(apto | zona, mes) con casos, ordenado de mayor a menor

# core/simulacion.py
@dataclass(frozen=True)
class ResultadoSimulacion:
    n: int; semilla: int; frecuencia_final: float; probabilidad_registro: float; curva: pd.DataFrame
def simular(evento: pd.Series, n: int, semilla: int) -> ResultadoSimulacion

# core/interpretacion.py   (todas devuelven str, en español, con formato "12,3 %")
def pct(x: float | None) -> str
def texto_frecuencia(...) -> str
def texto_clasica(...) -> str
def texto_frecuencial(...) -> str
def texto_condicional(nombre_a: str, nombre_b: str, cond: Resultado, base: Resultado) -> str
def texto_independencia(nombre_a: str, nombre_b: str, r: ResultadoIndependencia, epsilon: float) -> str
def texto_simulacion(r: ResultadoSimulacion, nombre_evento: str) -> str
def texto_recomendacion(ranking: pd.DataFrame) -> str
def texto_poca_muestra() -> str                       # aviso corto de menos de 30 casos
def texto_leyenda_eventos(letras: dict[str, str], nombres: dict[str, str]) -> str
def texto_espacio_muestral(apto: Resultado) -> str
def texto_mapa_calor(matriz: pd.DataFrame) -> str
def texto_matriz_independencia(matriz: pd.DataFrame, epsilon: float = EPSILON_INDEPENDENCIA) -> str
```

**Reglas de las funciones:**

- Son puras: reciben DataFrames o Series y devuelven valores, sin leer archivos ni estado global (salvo `api.py` y `datos.py`).
- Nunca lanzan excepción por una división por cero: devuelven `valor=None` y el texto interpretativo lo explica.
- Todo resultado incluye `favorables` y `totales`.

**Estilo de los textos interpretativos** (ejemplos del tono esperado):

- Condicional: "Cuando es invierno, la probabilidad de un día apto es 58,2 % (n = 724), frente a 41,5 % en general. Un día apto es más probable en invierno, con 16,7 puntos porcentuales de diferencia."
- Independencia: "P(A ∩ B) = 3,1 % y P(A)·P(B) = 2,9 %. La diferencia es de 0,2 puntos, menor que ε = 2 puntos, por lo que se consideran independientes."
- Si hay pocos casos, agregar: "Atención: se basa en menos de 30 casos."
- Si la diferencia entre la condicional y la base es menor que ε, decir que "casi no cambia".

## 9. Interfaz web (Streamlit)

Decisión registrada en `docs/adr/0001-tablero-unico.md`. La interfaz es un único **tablero** (ver `GLOSSARY.md`); no hay navegación entre pantallas. La explicación teórica (fórmulas, clásica contra frecuencial) se desarrolla fuera de la app, en la presentación.

**Estructura:** `app.py` define `st.set_page_config(layout="wide")`, la barra lateral y el tablero. El código de apoyo vive en `interfaz/` (formato, estilo, filtros). Los filtros viven en `st.session_state`. Usar `st.cache_data` para la carga de datos y el cálculo de eventos, y `@st.fragment` en las tarjetas con selector propio.

**Controles:**

| control | ubicación | valor por defecto |
| --- | --- | --- |
| Zonas (`st.pills`, selección múltiple) | arriba del tablero | las 5 |
| Rango de fechas | arriba del tablero | `2021-01-01` a `2025-12-31` |
| Umbrales de lluvia, viento, calor y helada | barra lateral | 1,0 mm, 30 km/h, 32 °C, 0 °C |
| Botón "Restablecer umbrales" | barra lateral | vuelve a los valores por defecto |

La semilla del sorteo es la constante `SEMILLA = 42` de `core/config.py`; no se muestra ni se edita en la interfaz. Los gráficos usan un color por zona.

Si el filtro deja cero filas (por ejemplo, sin zonas elegidas) o el rango de fechas está incompleto, mostrar un único aviso (`st.warning`) en lugar de las tarjetas y no calcular. Si falta un CSV, mostrar un `st.error`.

**Contenido del tablero:**

| Fila | Contenido | Funciones de `core/` |
| --- | --- | --- |
| 1 | Métricas: P(día apto) general, zona con mayor P(apto), mes con mayor P(apto), P(lluvia), P(viento fuerte), P(temperatura extrema); cada una con favorables y total | `frecuencia_relativa`, `grupo_mas_probable` |
| 2 | Barras de P(evento) por mes con color por zona y selector de evento; barras horizontales de los 8 resultados del espacio muestral (verde el apto, rojo los adversos) | `frecuencias_por_grupo`, `espacio_muestral` |
| 3 | Mapa de calor zona × mes de P(apto); ranking de mejores y peores combinaciones zona-mes | `matriz_condicional`, `ranking_zona_mes` |
| 4 | Curva de convergencia de la simulación (con selector de evento y de N, de 100 a 100.000 sorteos); independencia de los 6 pares: barras de P(A ∩ B) frente a P(A)·P(B) y tabla con la diferencia y el veredicto | `simular`, `matriz_independencia` |
| 5 | Tabla de datos crudos filtrada, con fuente (Open-Meteo, archivo) y rango de fechas | `cargar_clima` |

**Patrón de cada tarjeta** (`st.container(border=True)`): título, gráfico o tabla, y una línea de interpretación (`st.caption`, texto de `core/interpretacion.py`). Cada número incluye sus casos favorables y totales, con aviso si hay menos de 30. No se muestran fórmulas.

**Datos:** la interfaz no descarga ni actualiza datos. Los CSV de `data/` son datos de archivo versionados. `core/api.py` se conserva como registro de procedencia y no se invoca desde la interfaz.

**Tema visual** (`.streamlit/config.toml`), tono natural y sobrio:

```toml
[theme]
base = "light"
primaryColor = "#2F6B4F"
backgroundColor = "#FAFAF7"
secondaryBackgroundColor = "#EFEFE8"
textColor = "#1F2A24"
font = "sans serif"
```

Gráficos con Plotly, colores coherentes con el tema, ejes rotulados y porcentajes con coma decimal.

## 10. Requerimientos no funcionales

| ID | Requerimiento | Criterio |
| --- | --- | --- |
| RNF-01 | Reproducibilidad | Período fijo, semilla constante y CSV versionados dan los mismos resultados |
| RNF-02 | Funciona sin internet | Con los CSV en `data/`, la app anda sin conexión |
| RNF-03 | Instalación simple | `pip install -r requirements.txt` y `streamlit run app.py`, documentados en el README |
| RNF-04 | Rendimiento | El tablero se calcula en menos de 2 segundos con unas 9.000 filas |
| RNF-05 | Claridad del código | Funciones pequeñas y puras, type hints, docstrings en español |
| RNF-06 | Separación de capas | `core/` no importa Streamlit |
| RNF-07 | Pruebas | Las funciones de `core/` tienen pruebas con casos calculados a mano |
| RNF-08 | Usabilidad | Interfaz en español, cada resultado con interpretación (las fórmulas van en la presentación) |
| RNF-09 | Manejo de errores | Mensajes claros si falta un CSV, falla la API o P(B) = 0 |
| RNF-10 | Trazabilidad | Cada resultado muestra cuántos casos lo respaldan |

## 11. Pruebas (`tests/`, pytest)

Usar DataFrames chicos construidos a mano, sin red. La descarga se prueba con una respuesta JSON de ejemplo guardada en `tests/` (reemplazando `requests.get`, por ejemplo con `monkeypatch`).

- **Eventos:** un día exactamente en el umbral cuenta como evento (`>=` y `<=`). `temp_extrema` se activa por calor o por helada. `apto` es el complemento de A ∪ B ∪ C.
- **`lluvia_ayer`:** el primer día de cada zona es `<NA>` y no se arrastra información entre zonas.
- **Espacio muestral:** tiene 8 filas y los casos suman el total.
- **Frecuencia y clásica:** con un conjunto de 10 filas calculado a mano.
- **Condicional:** P(A|B) con valores conocidos. Con n(B) = 0 devuelve `valor=None`.
- **Independencia:** un par construido como independiente y otro como dependiente dan veredictos distintos; el criterio usa ε.
- **Simulación:** misma semilla, misma curva; con N grande la frecuencia final queda cerca de la del registro.
- **Datos:** `validar` detecta nulos, filas faltantes y fechas duplicadas; cada CSV real tiene 1.826 filas sin nulos.
- **Interpretación:** los textos incluyen el valor, los casos y la advertencia de poca muestra cuando corresponde.

## 12. Decisiones cerradas

| Tema | Decisión |
| --- | --- |
| Zonas y coordenadas | Las 5 de la sección 3 |
| Umbrales de día apto | Los de la sección 5 |
| Tolerancia de independencia | ε = 0,02 |
| Altitud de las cumbres en la API | No se informa en esta versión; mejora futura |
| Datos | Solo reales; no se simulan |
| Interfaz | Solo web en Streamlit; sin consola |

## 13. Mejoras futuras

- Informar la altitud de cada cumbre a la API para ajustar la temperatura.
- Intervalo de confianza para la proporción de días aptos.
- Más zonas, o integración con la app de gestión de salidas.
- Validar los umbrales con guías de trekking y comparar resultados con umbrales alternativos.
