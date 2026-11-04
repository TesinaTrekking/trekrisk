# TREKRISK

## Sistema de análisis estadístico de condiciones climáticas para actividades de trekking

**Trabajo Práctico Integrador Final — Estadística y Probabilidad Aplicada**  
ISAUI / Universidad Provincial de Córdoba — Sede Villa Carlos Paz

**Integrantes**

- Britos, Benjamín
- Faginoli, Santiago
- Heredia, Lucas Agustín
- Oyarzún López, Benjamín Elías

**Docente evaluador:** Belagardi, Esteban  
**Fecha de entrega:** 7 de noviembre de 2026

---

## 1. Problemática

La planificación de una salida de trekking requiere considerar las precipitaciones, el viento y las temperaturas extremas. Estas condiciones varían entre zonas y épocas del año, por lo que una descripción general del clima resulta insuficiente para comparar alternativas.

Trekrisk aborda la siguiente pregunta: **¿con qué frecuencia se registraron jornadas climáticamente aptas para realizar trekking en cinco zonas de Córdoba y cómo cambia esa frecuencia según la zona y el mes?**

El término *apto* expresa una clasificación operativa basada en umbrales configurables. No representa una garantía de seguridad: no contempla el estado del sendero, la dificultad del recorrido, la experiencia del grupo ni todas las condiciones meteorológicas relevantes.

## 2. Fundamentación

El proyecto vincula el desarrollo de software con la aplicación de estadística descriptiva y probabilidad sobre registros meteorológicos históricos reales. La programación permite organizar los datos, aplicar criterios uniformes y repetir los cálculos cuando cambian los filtros o los umbrales.

El análisis histórico aporta una referencia para comparar zonas y meses antes de planificar una actividad. Su utilidad consiste en fundamentar esa comparación con cantidades observadas, sin convertir las frecuencias históricas en un pronóstico para una fecha específica.

## 3. Objetivos

### Objetivo general

Desarrollar un sistema que procese registros climáticos históricos y aplique herramientas estadísticas y probabilísticas para comparar las condiciones de aptitud climática de cinco zonas de trekking de Córdoba.

### Objetivos específicos

- Organizar y validar los registros diarios del período 2021–2025.
- Identificar y clasificar las variables originales y derivadas.
- Definir eventos mediante umbrales editables.
- Calcular frecuencias, probabilidades condicionales y relaciones entre eventos.
- Ilustrar la convergencia de frecuencias mediante remuestreo de días reales.
- Presentar resultados con sus cantidades de casos e interpretaciones.
- Identificar las limitaciones que condicionan las conclusiones.

## 4. Descripción y procedencia de los datos

Se utilizan cinco archivos CSV almacenados en `data/`, uno por zona. Cada fila representa una combinación de **zona y fecha**. El período abarca desde el 1 de enero de 2021 hasta el 31 de diciembre de 2025, inclusive: 1.826 registros por zona y **9.130 registros en total**. El año bisiesto 2024 explica el día adicional respecto de cinco años de 365 días.

| Zona | Latitud | Longitud | Registros |
| --- | ---: | ---: | ---: |
| Cerro Champaquí | −31,97 | −64,93 | 1.826 |
| Cerro Uritorco | −30,84 | −64,46 | 1.826 |
| Quebrada del Condorito | −31,65 | −64,64 | 1.826 |
| Pan de Azúcar | −31,24 | −64,46 | 1.826 |
| Los Gigantes | −31,57 | −64,80 | 1.826 |

La fuente registrada en el repositorio es la Historical Weather API de Open-Meteo, mediante el endpoint `https://archive-api.open-meteo.com/v1/archive`. La especificación identifica los datos como provenientes de reanálisis ERA5. Un reanálisis reconstruye condiciones meteorológicas mediante modelos y observaciones; estas filas no deben interpretarse como mediciones de una estación instalada en cada cumbre.

El código de procedencia conserva las variables solicitadas: `precipitation_sum`, `wind_speed_10m_max`, `wind_gusts_10m_max`, `temperature_2m_max` y `temperature_2m_min`, con unidades explícitas y zona horaria `America/Argentina/Cordoba`. La consulta no fija el parámetro de modelo; los CSV no conservan metadatos suficientes para auditar por sí solos la identificación exacta del reanálisis utilizado en la descarga original.

La aplicación carga los CSV existentes y funciona sin conexión una vez instalado el entorno. No descarga ni actualiza información desde la interfaz. La validación del conjunto archivado no informó problemas de columnas requeridas, valores nulos, fechas duplicadas ni cobertura temporal por zona.

## 5. Variables utilizadas

### Variables originales

| Variable | Clasificación | Unidad o descripción |
| --- | --- | --- |
| `zona` | Cualitativa nominal | Identificador de la zona |
| `fecha` | Temporal | Día del registro |
| `precipitacion_mm` | Cuantitativa continua | Precipitación diaria, en mm |
| `viento_kmh` | Cuantitativa continua | Velocidad máxima diaria del viento a 10 m, en km/h |
| `racha_kmh` | Cuantitativa continua | Ráfaga máxima diaria a 10 m, en km/h |
| `tmax_c` | Cuantitativa continua | Temperatura máxima diaria a 2 m, en °C |
| `tmin_c` | Cuantitativa continua | Temperatura mínima diaria a 2 m, en °C |

### Variables derivadas

Se obtienen el año, el mes y la estación del hemisferio sur. El mes se utiliza como categoría ordenada del calendario, de carácter cíclico; la estación se trata como cualitativa nominal. Los eventos son variables cualitativas nominales dicotómicas: ocurren o no ocurren.

| Evento | Símbolo | Definición con umbrales predeterminados |
| --- | --- | --- |
| Lluvia | A | Precipitación ≥ 1,0 mm |
| Viento fuerte | B | Viento máximo ≥ 30 km/h |
| Temperatura extrema | C | Temperatura máxima ≥ 32 °C o mínima ≤ 0 °C |
| Lluvia el día anterior | D | Ocurrencia de A en la fecha inmediatamente anterior de la misma zona |
| Día apto | H | No ocurre A, B ni C |
| Día adverso | Hᶜ | Ocurre al menos uno de A, B o C |

Las igualdades están incluidas en los umbrales. Las ráfagas se conservan para describir los datos, pero no intervienen en la definición actual de aptitud. En la primera fecha de cada zona, D queda sin definir porque no se dispone del día anterior; esos cinco registros se excluyen de los cálculos que requieren D.

## 6. Metodología

1. **Carga y validación:** lectura de los cinco CSV y comprobación de su estructura y cobertura.
2. **Preparación:** conversión de fechas e incorporación de año, mes y estación.
3. **Clasificación:** aplicación de los umbrales y construcción de los eventos. La lluvia del día anterior se calcula dentro de cada zona y exige fechas consecutivas.
4. **Filtrado:** selección de zonas y fechas. La interfaz calcula los eventos sobre el historial antes de aplicar estos filtros.
5. **Análisis:** obtención de medidas descriptivas, frecuencias, probabilidades condicionales, ranking e indicadores de independencia aproximada.
6. **Remuestreo:** selección con reposición de registros reales y cálculo de frecuencias acumuladas.
7. **Presentación:** visualización en un único tablero con cantidades de casos e interpretación.

Los resultados de este informe se calcularon mediante las funciones de `core/`, con las cinco zonas, el período completo y los umbrales predeterminados. Los porcentajes se redondean a una cifra decimal; las diferencias entre probabilidades se expresan en puntos porcentuales.

## 7. Herramientas estadísticas y probabilísticas

### 7.1. Estadística descriptiva

Se calculan media, mediana, desvío estándar, mínimo, máximo y percentiles 25 y 75 para las cinco variables meteorológicas numéricas. El desvío se obtiene con `pandas`, que utiliza divisor n − 1 por defecto. Estas medidas están disponibles en `core/datos.py`; no tienen una tarjeta propia en el tablero actual.

### 7.2. Experimento aleatorio y espacio muestral

El experimento consiste en observar las condiciones de un día en una zona. Para describir su resultado se consideran la ocurrencia o ausencia de A, B y C. Existen **2³ = 8 combinaciones**, que forman una partición del conjunto de registros. Estas combinaciones no son equiprobables. Solo la combinación sin lluvia, viento fuerte ni temperatura extrema resulta apta.

Debe distinguirse este espacio de categorías del universo de registros zona-fecha utilizado en un sorteo: en ese sorteo cada fila tiene igual probabilidad de ser elegida, aunque las ocho categorías climáticas tengan frecuencias distintas.

### 7.3. Frecuencia relativa, probabilidad clásica y frecuencial

La frecuencia relativa de un evento E es:

**fr(E) = n(E) / N**, donde n(E) es la cantidad de casos favorables y N el total de casos válidos.

En un sorteo uniforme de una fila del archivo, la probabilidad clásica se calcula como casos favorables sobre casos posibles. Por ejemplo, seleccionar una fila apta tiene probabilidad exacta **4.772/9.130** dentro de ese experimento finito.

El enfoque frecuencial utiliza esa misma proporción observada como estimación para condiciones semejantes a las históricas. Ambos enfoques pueden producir el mismo número, pero responden preguntas distintas. La interpretación futura requiere suponer que el historial es representativo; no queda garantizada por el cálculo.

Las funciones de probabilidad clásica están implementadas en `core/probabilidad.py`, aunque el tablero no les dedica una visualización propia.

### 7.4. Probabilidad condicional

**P(E | F) = n(E ∩ F) / n(F)**, siempre que n(F) sea mayor que cero.

Se aplica principalmente a **P(H | zona, mes)**: el denominador contiene únicamente los registros de la zona y el mes elegidos. También permite comparar la lluvia de un día según haya llovido en el anterior. Cuando el denominador es cero, el sistema devuelve un resultado no calculable en lugar de dividir por cero.

### 7.5. Independencia aproximada

La independencia teórica exige **P(E ∩ F) = P(E) × P(F)**. El programa compara ambas cantidades con una tolerancia fija:

**|P(E ∩ F) − P(E) × P(F)| < 0,02.**

Se analizan los seis pares posibles entre A, B, C y D. El resultado indica compatibilidad con el criterio numérico elegido; no constituye una prueba de hipótesis ni demuestra independencia meteorológica. Una tolerancia absoluta puede ocultar diferencias relativas importantes en eventos poco frecuentes.

### 7.6. Remuestreo y convergencia

Se seleccionan filas históricas al azar con reposición y se calcula la frecuencia acumulada del evento elegido. La semilla constante del proyecto permite reproducir el experimento. No se generan valores meteorológicos nuevos.

El procedimiento ilustra la aproximación de la frecuencia del sorteo a la proporción del archivo. Al seleccionar filas de manera independiente, no conserva la sucesión temporal de episodios meteorológicos y no permite concluir que los días reales sean independientes.

### 7.7. Herramientas no utilizadas

No se aplica regresión porque el objetivo no es modelar ni predecir una variable continua. Tampoco se implementan intervalos de confianza ni pruebas de hipótesis: el alcance elegido es describir el archivo completo y comparar sus proporciones empíricas.

Disponer del archivo completo permite describir ese período sin muestrearlo, pero no elimina la incertidumbre al extrapolar a otros años. Para una generalización formal sería necesario ampliar la metodología y considerar la dependencia temporal y espacial.

## 8. Resultados e interpretación

### 8.1. Resumen descriptivo

Cada medida de la siguiente tabla utiliza **9.130 observaciones válidas**. Las medidas descriptivas no tienen casos favorables, porque resumen magnitudes y no eventos.

| Variable | Media | Mediana | Desvío | Mínimo | Máximo | P25 | P75 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Precipitación (mm) | 2,9 | 0,0 | 6,8 | 0,0 | 93,4 | 0,0 | 2,5 |
| Viento máximo (km/h) | 14,5 | 13,6 | 5,4 | 1,7 | 46,4 | 10,6 | 17,4 |
| Ráfaga máxima (km/h) | 42,1 | 39,2 | 14,2 | 14,8 | 134,6 | 31,7 | 49,7 |
| Temperatura máxima (°C) | 16,6 | 16,6 | 7,0 | −7,9 | 40,3 | 11,9 | 21,2 |
| Temperatura mínima (°C) | 7,4 | 7,5 | 6,1 | −16,6 | 22,9 | 3,0 | 11,7 |

La mediana de precipitación es cero y su media es positiva, lo que muestra que las jornadas con precipitación elevan el promedio. Las ráfagas presentan valores mayores que el viento máximo considerado para clasificar B; por eso una baja frecuencia de B no permite afirmar que las ráfagas intensas sean igualmente infrecuentes.

### 8.2. Frecuencias generales

| Evento | Favorables / total | Frecuencia |
| --- | ---: | ---: |
| Día apto | 4.772 / 9.130 | 52,3 % |
| Día adverso | 4.358 / 9.130 | 47,7 % |
| Lluvia | 3.226 / 9.130 | 35,3 % |
| Viento fuerte | 113 / 9.130 | 1,2 % |
| Temperatura extrema | 1.269 / 9.130 | 13,9 % |

Algo más de la mitad de los registros cumple simultáneamente los tres criterios de aptitud. La lluvia es el evento adverso más frecuente entre los considerados. Los porcentajes de A, B y C no deben sumarse para obtener la proporción adversa, porque pueden ocurrir juntos.

### 8.3. Espacio muestral observado

Todos los porcentajes de esta tabla tienen como denominador los **9.130 registros**.

| Lluvia A | Viento B | Temperatura C | Casos / total | Frecuencia | Clasificación |
| --- | --- | --- | ---: | ---: | --- |
| Sí | Sí | Sí | 7 / 9.130 | 0,1 % | Adverso |
| Sí | Sí | No | 34 / 9.130 | 0,4 % | Adverso |
| Sí | No | Sí | 197 / 9.130 | 2,2 % | Adverso |
| Sí | No | No | 2.988 / 9.130 | 32,7 % | Adverso |
| No | Sí | Sí | 5 / 9.130 | 0,1 % | Adverso |
| No | Sí | No | 67 / 9.130 | 0,7 % | Adverso |
| No | No | Sí | 1.060 / 9.130 | 11,6 % | Adverso |
| No | No | No | 4.772 / 9.130 | 52,3 % | Apto |

Las cantidades suman 9.130; las diferencias que puedan aparecer al sumar porcentajes se deben al redondeo. Dos combinaciones tienen menos de 30 ocurrencias —7 y 5—, aunque el denominador utilizado para sus frecuencias es el registro completo. Conviene distinguir esta escasez de ocurrencias de la advertencia automática del sistema, que se activa cuando el denominador de un resultado es menor que 30.

### 8.4. Comparación entre zonas

| Zona | Días aptos / total | P(H | zona) |
| --- | ---: | ---: |
| Quebrada del Condorito | 1.182 / 1.826 | 64,7 % |
| Pan de Azúcar | 1.142 / 1.826 | 62,5 % |
| Cerro Uritorco | 930 / 1.826 | 50,9 % |
| Los Gigantes | 810 / 1.826 | 44,4 % |
| Cerro Champaquí | 708 / 1.826 | 38,8 % |

Quebrada del Condorito presenta la mayor proporción de registros aptos con estos criterios. Esta posición describe las condiciones de los datos asociados a las coordenadas consultadas. La ausencia de ajuste explícito a la altitud de las cumbres impide convertir el ranking en una comparación concluyente de seguridad de los recorridos.

### 8.5. Comparación mensual

| Mes | Días aptos / total | P(H | mes) |
| --- | ---: | ---: |
| Enero | 274 / 775 | 35,4 % |
| Febrero | 299 / 705 | 42,4 % |
| Marzo | 339 / 775 | 43,7 % |
| Abril | 448 / 750 | 59,7 % |
| Mayo | 475 / 775 | 61,3 % |
| Junio | 446 / 750 | 59,5 % |
| Julio | 422 / 775 | 54,5 % |
| Agosto | 471 / 775 | 60,8 % |
| Septiembre | 488 / 750 | 65,1 % |
| Octubre | 462 / 775 | 59,6 % |
| Noviembre | 348 / 750 | 46,4 % |
| Diciembre | 300 / 775 | 38,7 % |

Septiembre presenta la mayor proporción agregada de jornadas aptas y enero la menor. Los denominadores cambian por la duración de los meses. Cada total incluye las cinco zonas; por ejemplo, los 750 registros de septiembre corresponden a 30 días × 5 años × 5 zonas, no a 750 fechas distintas.

### 8.6. Combinaciones de zona y mes

| Posición destacada | Zona y mes | Días aptos / total | Probabilidad condicional |
| --- | --- | ---: | ---: |
| Mayor proporción | Quebrada del Condorito, junio | 126 / 150 | 84,0 % |
| Segunda | Pan de Azúcar, junio | 123 / 150 | 82,0 % |
| Tercera | Pan de Azúcar, agosto | 127 / 155 | 81,9 % |
| Menor proporción | Los Gigantes, enero | 39 / 155 | 25,2 % |

El mejor mes agregado no tiene por qué coincidir con el de cada zona. Septiembre encabeza la comparación general, mientras que la mayor proporción de una combinación específica corresponde a Quebrada del Condorito en junio. Esto justifica utilizar la probabilidad condicional y el mapa de calor en lugar de decidir únicamente con el promedio global.

### 8.7. Relación entre lluvia y lluvia del día anterior

Para comparar A y D se utilizan **9.125 pares válidos**: se excluye el primer registro de cada una de las cinco zonas.

- P(A): **3.226 / 9.125 = 35,4 %**, sobre ese universo válido.
- P(D): **3.224 / 9.125 = 35,3 %**.
- P(A ∩ D): **2.008 / 9.125 = 22,0 %**.
- P(A | D): **2.008 / 3.224 = 62,3 %**.

El producto P(A) × P(D) es aproximadamente 12,5 %. Es una cantidad calculada a partir de las dos proporciones marginales, no una frecuencia conjunta observada. La diferencia respecto del 22,0 % conjunto es de **9,5 puntos porcentuales**, superior a la tolerancia de 2 puntos.

Por lo tanto, este par no satisface el criterio de independencia aproximada del programa. En el registro, la lluvia es más frecuente cuando también llovió el día anterior. Esta asociación describe persistencia temporal observada, sin establecer por sí sola una relación causal.

Al evaluar los seis pares, lluvia–viento, viento–temperatura extrema y viento–lluvia anterior cumplen el criterio de proximidad. Lluvia–temperatura extrema, lluvia–lluvia anterior y temperatura extrema–lluvia anterior no lo cumplen. Los universos son de 9.130 casos para pares sin D y 9.125 para pares con D.

### 8.8. Remuestreo de días aptos

Con 10.000 selecciones con reposición y la semilla constante del proyecto, se obtuvieron **5.223 selecciones aptas / 10.000 = 52,2 %**. La referencia del archivo es **4.772 / 9.130 = 52,3 %**.

La diferencia es de aproximadamente 0,04 puntos porcentuales. El resultado ilustra la proximidad entre la frecuencia del sorteo y la proporción histórica. Las 10.000 selecciones no representan nuevas observaciones ni amplían el período meteorológico disponible.

## 9. Implementación y verificación

La aplicación utiliza Python, pandas y NumPy para el procesamiento, Streamlit para la interfaz y Plotly para los gráficos. `requests` se conserva en el módulo de procedencia de los datos; `pytest` se utiliza para las pruebas.

| Componente | Responsabilidad |
| --- | --- |
| `app.py` | Entrada y composición del tablero |
| `interfaz/` | Filtros, formato, estilos y tarjetas |
| `core/config.py` | Zonas, umbrales y constantes |
| `core/datos.py` | Carga, validación y resumen descriptivo |
| `core/eventos.py` | Clasificación y espacio muestral |
| `core/probabilidad.py` | Frecuencias, condicionales, independencia y ranking |
| `core/simulacion.py` | Remuestreo de registros reales |
| `core/interpretacion.py` | Generación de textos interpretativos |
| `core/api.py` | Registro del procedimiento de descarga |
| `data/` y `tests/` | Archivo histórico y pruebas |

La lógica de `core/` no importa Streamlit. El tablero presenta métricas generales, frecuencias mensuales, las ocho combinaciones, un mapa de calor, un ranking, el experimento de remuestreo, comparaciones de independencia y los datos filtrados.

Para ejecutar el proyecto desde su directorio raíz:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

En Windows, la activación del entorno se realiza con `.venv\Scripts\activate`. La instalación requiere acceso a los paquetes; la consulta del archivo histórico no necesita conexión.

La verificación realizada con `.venv/bin/python -m pytest` finalizó con **58 pruebas aprobadas de 58 ejecutadas**. Las pruebas cubren, entre otros casos, igualdad con los umbrales, tratamiento de la lluvia anterior por zona, conteos del espacio muestral, probabilidades conocidas, denominadores nulos, reproducibilidad del remuestreo y validación de los CSV. Las pruebas de descarga reemplazan la respuesta de red.

Estos resultados verifican los casos cubiertos por las pruebas; no constituyen una validación meteorológica de los umbrales ni una evaluación completa de la interfaz.

## 10. Dificultades y decisiones durante el desarrollo

**Del módulo de riesgo al análisis histórico.** Según el documento inicial del equipo, la idea surgió como un módulo asociado a la tesina de trekking. Se optó por una aplicación desacoplada que pudiera trabajar sin consultas en tiempo real. Los archivos precargados contienen datos históricos reales, no datos ficticios de prueba.

**Archivo fijo y reproducibilidad.** Se conservaron los CSV en el repositorio y una semilla constante para repetir el remuestreo. La contrapartida es que el período no se actualiza automáticamente.

**Criterio explícito de aptitud.** Se definieron umbrales editables para hacer visible cómo se clasifica cada jornada. Su elección no fue validada con guías de trekking y condiciona todos los rankings.

**Antecedente temporal.** La lluvia anterior se calcula por zona y solo entre fechas consecutivas, evitando arrastrar el último valor de una zona a la siguiente. La ausencia de antecedente no se interpreta como ausencia de lluvia.

**Interfaz única.** Se eligió un tablero para comparar resultados sin navegación entre pantallas. Las fórmulas y la distinción entre probabilidad clásica y frecuencial se desarrollan en el informe y la defensa.

**Ejecución e interpretación de la consigna.** La consigna solicita como mínimo una versión ejecutable por consola. La implementación se inicia con un comando de consola, pero la interacción ocurre en el navegador y no ofrece una interfaz de análisis por terminal. La especificación del proyecto considera suficiente ese inicio desde consola. Corresponde confirmar con el docente si esa interpretación satisface el requisito de entrega.

## 11. Limitaciones

- La resolución espacial del reanálisis no representa todos los microclimas de montaña; zonas cercanas pueden compartir condiciones muy similares.
- La consulta no informa explícitamente la altitud de las cumbres. Las temperaturas de las coordenadas consultadas pueden no representar las del recorrido y afectar especialmente la clasificación de heladas.
- El período comprende cinco años y no constituye por sí solo una caracterización climática de largo plazo.
- Los registros de fechas consecutivas y zonas próximas pueden estar relacionados; 9.130 filas no equivalen a 9.130 observaciones independientes.
- Los datos diarios no describen la hora ni la duración de los episodios. El evento adverso puede ocurrir fuera del horario de una salida.
- La definición de aptitud no incluye ráfagas, tormentas eléctricas, visibilidad, nieve ni condiciones del terreno.
- El criterio de independencia es una comparación descriptiva con tolerancia, sin contraste inferencial.
- Los resultados cambian al modificar los umbrales, las zonas o las fechas seleccionadas.

## 12. Conclusiones

Trekrisk permitió organizar 9.130 registros históricos y relacionar conceptos de estadística y probabilidad con una pregunta concreta de planificación. Con los umbrales predeterminados, **4.772 de 9.130 jornadas-zona resultaron aptas, equivalentes al 52,3 %**.

La comparación muestra diferencias entre zonas y meses. Quebrada del Condorito presenta **1.182 jornadas aptas de 1.826 (64,7 %)**, mientras que septiembre reúne **488 de 750 registros aptos (65,1 %)** al agregar las cinco zonas. El análisis condicionado identifica como combinación de mayor proporción a Quebrada del Condorito en junio: **126 de 150 (84,0 %)**. Estos resultados permiten priorizar alternativas para su evaluación posterior, dentro de las limitaciones de coordenadas, altitud y criterios utilizados.

El análisis de lluvia evidencia que considerar el antecedente temporal aporta información: en **2.008 de 3.224 registros precedidos por lluvia (62,3 %)** también llovió en el día observado. El remuestreo, por su parte, permite ilustrar la convergencia de frecuencias sin inventar datos meteorológicos.

La principal contribución del sistema es ofrecer una comparación histórica reproducible, con criterios explícitos y cantidades verificables. La elección de una salida concreta requiere complementarla con información meteorológica actual y con la evaluación del recorrido y del grupo.

## 13. Posibles mejoras

- Revisar las coordenadas e informar las altitudes pertinentes al obtener nuevos datos.
- Validar los umbrales con guías y estudiar la sensibilidad de los rankings a sus cambios.
- Ampliar el período y las zonas, manteniendo la trazabilidad de la fuente.
- Conservar metadatos de descarga: fecha de consulta, modelo y elevación utilizados.
- Evaluar si corresponde incorporar las ráfagas a la definición de aptitud.
- Incorporar métodos de incertidumbre que contemplen dependencia temporal y espacial, si se amplía el objetivo hacia la inferencia.
- Explorar una integración posterior con la aplicación de gestión de trekking.

Estas propuestas no forman parte de las funcionalidades verificadas en esta versión.

## 14. Fuentes y material de referencia

- **Consigna de la asignatura:** `CONSIGNA_IEFI_EPA.pdf`, requisitos del informe, sistema y defensa.
- **Documento inicial del equipo:** `Trekrisk documento tecnico formal.pdf`, antecedentes, portada y estructura general.
- **Especificación del proyecto:** [`../SPEC.md`](../SPEC.md).
- **Instalación, alcance y limitaciones:** [`../README.md`](../README.md).
- **Decisión de interfaz:** [`adr/0001-tablero-unico.md`](adr/0001-tablero-unico.md).
- **Evidencia de resultados:** archivos [`../data/`](../data/), procesados mediante [`../core/`](../core/), con el período completo y `Umbrales()` predeterminados.
- **Fuente meteorológica indicada por el proyecto:** [Open-Meteo, Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api). La revisión de este informe se basó en el archivo local y el código de procedencia; no se realizó una nueva descarga.
