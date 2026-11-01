"""Pantalla 1: datos, estado de la caché, validación y estadística descriptiva."""

import pandas as pd
import streamlit as st

from core.api import ErrorDescarga, descargar_todas
from core.config import DIAS_ESPERADOS, FECHA_FIN, FECHA_INICIO, ZONAS
from core.datos import cargar_clima, resumen_descriptivo, validar
from paginas import _comun as c

st.title("Datos")
st.markdown(
    "**Pregunta del guía:** ¿con qué datos trabajamos y qué tan confiables son?\n\n"
    f"Clima diario real de {len(ZONAS)} zonas entre {FECHA_INICIO} y {FECHA_FIN} "
    f"({c.entero(DIAS_ESPERADOS)} días por zona). {c.FUENTE}"
)

st.subheader("Descarga")
st.write("Los datos ya vienen guardados en la carpeta `data/` y la app funciona sin internet. "
         "La descarga vuelve a pedirlos a Open-Meteo y reemplaza los CSV.")
if st.button("Descargar o actualizar datos"):
    try:
        with st.spinner("Descargando las 5 zonas desde Open-Meteo…"):
            guardadas = descargar_todas(c.CARPETA_DATOS)
        st.cache_data.clear()
        st.success("Descarga completa: " + ", ".join(
            f"{c.NOMBRE_ZONA[slug]}: {c.entero(filas)} filas" for slug, filas in guardadas.items()))
    except ErrorDescarga as error:
        st.error(f"No se pudo completar la descarga (las zonas anteriores a la falla ya se "
                 f"actualizaron). Detalle: {error}")
    except OSError as error:
        st.error(f"No se pudo guardar un archivo: {error}")

st.subheader("Estado de la caché")
estado, presentes = [], []
for zona in ZONAS:
    try:
        d = cargar_clima(c.CARPETA_DATOS, [zona.slug])
    except FileNotFoundError:
        estado.append({"Zona": zona.nombre, "Archivo": f"clima_{zona.slug}.csv",
                       "Estado": "Falta", "Filas": "0", "Desde": "—", "Hasta": "—"})
        continue
    presentes.append(zona.slug)
    completo = len(d) == DIAS_ESPERADOS
    estado.append({"Zona": zona.nombre, "Archivo": f"clima_{zona.slug}.csv",
                   "Estado": "Completo" if completo else "Incompleto",
                   "Filas": c.entero(len(d)), "Desde": f"{d['fecha'].min():%Y-%m-%d}",
                   "Hasta": f"{d['fecha'].max():%Y-%m-%d}"})
c.tabla(pd.DataFrame(estado))

if not presentes:
    st.error("No hay ningún CSV en `data/`. Usá el botón de descarga.")
    st.stop()

st.subheader("Validación")
problemas = validar(cargar_clima(c.CARPETA_DATOS, presentes))
if problemas:
    for problema in problemas:
        st.error(problema)
else:
    st.success(f"Sin problemas: {len(presentes)} zonas, {c.entero(DIAS_ESPERADOS)} filas cada una, "
               "sin nulos ni fechas duplicadas.")

st.subheader("Variables y su tipo")
c.tabla(pd.DataFrame([
    ("zona", "Cualitativa nominal", "Punto de trekking", "—"),
    ("fecha", "Temporal", "Día calendario", "AAAA-MM-DD"),
    ("precipitacion_mm", "Cuantitativa continua", "Precipitación diaria acumulada", "mm"),
    ("viento_kmh", "Cuantitativa continua", "Viento máximo a 10 m", "km/h"),
    ("racha_kmh", "Cuantitativa continua", "Racha máxima a 10 m", "km/h"),
    ("tmax_c", "Cuantitativa continua", "Temperatura máxima a 2 m", "°C"),
    ("tmin_c", "Cuantitativa continua", "Temperatura mínima a 2 m", "°C"),
    ("mes", "Cualitativa ordinal", "Mes del año (1 a 12)", "—"),
    ("estacion", "Cualitativa nominal", "Estación (hemisferio sur)", "—"),
], columns=["Variable", "Tipo", "Descripción", "Unidad"]))

st.subheader("Estadística descriptiva")
df = c.datos_filtrados()
if df is None:
    st.stop()
resumen = resumen_descriptivo(df).map(lambda v: c.numero(v, 1)).reset_index(names="variable")
resumen.columns = ["Variable", "Media", "Mediana", "Desvío", "Mínimo", "Máximo", "P25", "P75"]
c.tabla(resumen)
st.caption(f"Calculado con {c.entero(len(df))} días según los filtros de la barra lateral.")

st.subheader("Limitaciones")
st.write("Los datos provienen de un reanálisis (ERA5) con una grilla de 10 a 25 km: zonas cercanas "
         "pueden dar valores casi idénticos y el microclima de cumbre no queda capturado. "
         "No se ajusta por la altitud de las cumbres.")
