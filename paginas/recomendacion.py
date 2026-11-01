"""Pantalla 8: recomendación por zona y mes."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.interpretacion import pct, texto_frecuencia, texto_recomendacion
from core.probabilidad import Resultado, frecuencias_por_grupo, ranking_zona_mes
from paginas import _comun as c

CANTIDAD = 10

st.title("Recomendación")
st.markdown("**Pregunta del guía:** ¿en qué zona y mes conviene salir, y cuándo conviene evitarlo?")
st.latex(r"P(\text{apto} \mid \text{zona},\ \text{mes}) = "
         r"\frac{\text{días aptos de la zona en ese mes}}{\text{días de la zona en ese mes}}")

df = c.datos_filtrados()
if df is None:
    st.stop()

ranking = ranking_zona_mes(df)
st.info(texto_recomendacion(ranking))


def _formatear(t):
    out = t.assign(
        Zona=t["zona"].map(c.NOMBRE_ZONA), Mes=t["mes"].map(lambda m: c.MESES[m - 1].capitalize()),
        **{"P(apto)": t["probabilidad"].map(pct), "Días aptos": t["favorables"].map(c.entero),
           "Días totales": t["totales"].map(c.entero),
           "Aviso": t["totales"].map(lambda n: "Menos de 30 casos" if n < 30 else "")},
    )
    return out[["Zona", "Mes", "P(apto)", "Días aptos", "Días totales", "Aviso"]]


mejores = ranking.head(CANTIDAD)
peores = ranking.tail(CANTIDAD).iloc[::-1]
col1, col2 = st.columns(2)
with col1:
    st.subheader(f"Las {len(mejores)} mejores combinaciones")
    c.tabla(_formatear(mejores))
with col2:
    st.subheader(f"Las {len(peores)} peores combinaciones")
    c.tabla(_formatear(peores))

barras = pd.concat([mejores, peores]).drop_duplicates(["zona", "mes"]).iloc[::-1]
etiquetas = [f"{c.NOMBRE_ZONA[z]}, {c.MESES[m - 1]}" for z, m in zip(barras["zona"], barras["mes"])]
claves_mejores = set(zip(mejores["zona"], mejores["mes"]))
colores = [c.VERDE if clave in claves_mejores else c.OCRE
           for clave in zip(barras["zona"], barras["mes"])]
fig = go.Figure(go.Bar(
    x=barras["probabilidad"], y=etiquetas, orientation="h", marker_color=colores,
    text=[pct(v) for v in barras["probabilidad"]], textposition="outside",
    customdata=barras[["favorables", "totales"]],
    hovertemplate="%{y}: %{text} (%{customdata[0]} de %{customdata[1]} días)<extra></extra>",
))
c.estilo(fig, "Probabilidad de día apto", "Zona y mes")
fig.update_xaxes(tickformat=".0%", range=[0, 1.05])
st.plotly_chart(fig, width="stretch")

st.subheader("Mejor estación")
estaciones = frecuencias_por_grupo(df, "apto", "estacion").sort_values(
    "frecuencia_relativa", ascending=False)
mejor = estaciones.iloc[0]
r_estacion = Resultado(float(mejor["frecuencia_relativa"]), int(mejor["favorables"]),
                       int(mejor["totales"]))
c.metrica(f"Mejor estación: {mejor['estacion']}", r_estacion)
st.info(texto_frecuencia("un día apto", r_estacion, contexto=f" en {mejor['estacion']}"))

with st.expander("Ranking completo"):
    c.tabla(_formatear(ranking))
