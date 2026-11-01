"""Entrada de Streamlit: barra lateral de umbrales y tablero único."""

import streamlit as st

from interfaz import comun as c
from interfaz import tarjetas as t

st.set_page_config(page_title="Clima para trekking en Córdoba", page_icon="🥾", layout="wide")

c.barra_lateral()

st.title("Clima para trekking en Córdoba")
st.markdown("¿Dónde y cuándo conviene salir? Probabilidades calculadas con datos reales "
            "de 5 zonas, entre 2021 y 2025.")
c.filtros_superiores()

df = c.datos_filtrados()
if df is None:
    st.stop()

t.fila_metricas(df)

ancha, angosta = st.columns([2, 1])
with ancha:
    t.tarjeta_frecuencias(df)
with angosta:
    t.tarjeta_espacio_muestral(df)

ancha, angosta = st.columns([2, 1])
with ancha:
    t.tarjeta_mapa_calor(df)
with angosta:
    t.tarjeta_ranking(df)

ancha, angosta = st.columns([2, 1])
with ancha:
    t.tarjeta_convergencia(df)
with angosta:
    t.tarjeta_independencia(df)

t.tarjeta_datos(df)
