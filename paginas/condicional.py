"""Pantalla 5: probabilidad condicional."""

import plotly.graph_objects as go
import streamlit as st

from core.interpretacion import pct, texto_condicional
from core.probabilidad import frecuencia_relativa, matriz_condicional, probabilidad_condicional
from paginas import _comun as c

st.title("Probabilidad condicional")
st.markdown("**Pregunta del guía:** sabiendo que ocurre algo (un mes, una estación, una zona u "
            "otro evento), ¿cambia la probabilidad de lo que me importa?")
st.latex(r"P(A \mid B) = \frac{P(A \cap B)}{P(B)} = \frac{n(A \cap B)}{n(B)}")

df = c.datos_filtrados()
if df is None:
    st.stop()

izq, centro, der = st.columns(3)
evento_a = izq.selectbox("Evento A (lo que me importa)", list(c.EVENTOS),
                         format_func=c.EVENTOS.get, index=4)
tipo = centro.selectbox("Condición B", ["Otro evento", "Mes", "Estación", "Zona"])

if tipo == "Otro evento":
    opciones = [e for e in c.EVENTOS if e != evento_a]
    b_evento = der.selectbox("Evento B", opciones, format_func=c.EVENTOS.get)
    condicion, nombre_b = df[b_evento].fillna(False).astype(bool), c.CONDICION_EVENTO[b_evento]
    # La condición lluvia_ayer pierde los días sin día anterior: se descartan de A también.
    if df[b_evento].isna().any():
        condicion = df[b_evento]
elif tipo == "Mes":
    mes = der.selectbox("Mes", sorted(df["mes"].unique()), format_func=lambda m: c.MESES[m - 1])
    condicion, nombre_b = df["mes"] == mes, f"el mes es {c.MESES[mes - 1]}"
elif tipo == "Estación":
    estacion = der.selectbox("Estación", c.ESTACIONES)
    condicion, nombre_b = df["estacion"] == estacion, f"la estación es {estacion}"
else:
    zona = der.selectbox("Zona", sorted(df["zona"].unique()), format_func=c.NOMBRE_ZONA.get)
    condicion, nombre_b = df["zona"] == zona, f"la zona es {c.NOMBRE_ZONA[zona]}"

nombre_a = c.NOMBRE_EVENTO[evento_a]
cond = probabilidad_condicional(df[evento_a], condicion)
base = frecuencia_relativa(df[evento_a])

col1, col2 = st.columns(2)
with col1:
    c.metrica(f"P(A | B): {c.EVENTOS[evento_a]} dado que {nombre_b}", cond)
with col2:
    c.metrica(f"P(A): {c.EVENTOS[evento_a]} en general", base)
st.info(texto_condicional(nombre_a, nombre_b, cond, base))

st.subheader("Mapa de calor: probabilidad de un día apto por zona y mes")
st.latex(r"P(\text{apto} \mid \text{zona},\ \text{mes}) = "
         r"\frac{n(\text{apto} \cap \text{zona} \cap \text{mes})}{n(\text{zona} \cap \text{mes})}")
m = matriz_condicional(df, "apto", "zona", "mes")
zonas = [z for z in c.NOMBRE_ZONA if z in set(m["fila"])]
z_valores, textos, casos = [], [], []
for zona_slug in zonas:
    fila = m[m["fila"] == zona_slug].set_index("columna")
    z_valores.append([fila["probabilidad"].get(mm) for mm in range(1, 13)])
    textos.append([pct(fila["probabilidad"].get(mm)) if mm in fila.index else "" for mm in range(1, 13)])
    casos.append([c.entero(fila["totales"].get(mm, 0)) for mm in range(1, 13)])
fig = go.Figure(go.Heatmap(
    z=z_valores, x=[mes[:3].capitalize() for mes in c.MESES], y=[c.NOMBRE_ZONA[z] for z in zonas],
    text=textos, texttemplate="%{text}", customdata=casos, zmin=0, zmax=1,
    colorscale=[[0, "#F3E3C3"], [1, c.VERDE]], colorbar={"tickformat": ".0%"},
    hovertemplate="%{y}, %{x}: %{text} (%{customdata} días)<extra></extra>",
))
c.estilo(fig, "Mes", "Zona")
st.plotly_chart(fig, width="stretch")
poco = m[m["totales"] < 30]
if not poco.empty:
    st.warning(f"{len(poco)} celdas zona-mes tienen menos de 30 casos; interpretalas con cuidado.")
