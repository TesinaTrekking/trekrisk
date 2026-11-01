"""Pantalla 6: independencia de eventos."""

import plotly.graph_objects as go
import streamlit as st

from core.config import EPSILON_INDEPENDENCIA
from core.interpretacion import pct, texto_independencia
from core.probabilidad import independencia, matriz_independencia
from paginas import _comun as c

EVENTOS = ["lluvia", "viento_fuerte", "temp_extrema", "lluvia_ayer"]
LETRA = dict(zip(EVENTOS, "ABCD"))

st.title("Independencia de eventos")
st.markdown("**Pregunta del guía:** ¿saber que hay viento o que llovió ayer me dice algo sobre la "
            "lluvia de hoy, o los eventos no se influyen entre sí?")
st.latex(r"A \text{ y } B \text{ independientes} \iff P(A \cap B) = P(A)\cdot P(B)")
st.latex(rf"\text{{Criterio: }} |P(A \cap B) - P(A)\,P(B)| < \varepsilon = "
         rf"{str(EPSILON_INDEPENDENCIA).replace('.', ',')}")

df = c.datos_filtrados()
if df is None:
    st.stop()

m = matriz_independencia(df, EVENTOS)
m["par"] = [f"{LETRA[a]}–{LETRA[b]}" for a, b in zip(m["a"], m["b"])]

fig = go.Figure([
    go.Bar(name="P(A ∩ B)", x=m["par"], y=m["p_ab"], marker_color=c.VERDE),
    go.Bar(name="P(A)·P(B)", x=m["par"], y=m["producto"], marker_color=c.OCRE),
])
fig.update_layout(barmode="group")
c.estilo(fig, "Par de eventos", "Probabilidad", porcentaje=True)
st.plotly_chart(fig, width="stretch")

mostrar = m.assign(
    Par=m["par"],
    **{"P(A ∩ B)": m["p_ab"].map(pct), "P(A)·P(B)": m["producto"].map(pct),
       "Diferencia": m["diferencia"].map(lambda d: f"{c.numero(d * 100)} puntos"),
       "P(A | B)": m["p_a_dado_b"].map(pct), "P(A)": m["p_a"].map(pct),
       "Casos": m["casos"].map(c.entero),
       "Veredicto": m["independientes"].map({True: "Independientes", False: "No independientes"})},
)[["Par", "P(A ∩ B)", "P(A)·P(B)", "Diferencia", "P(A | B)", "P(A)", "Casos", "Veredicto"]]
c.tabla(mostrar)
st.caption(" · ".join(f"{LETRA[e]} = {c.NOMBRE_CORTO[e]}" for e in EVENTOS)
           + ". El par A–D ilustra que los días consecutivos no son independientes.")

st.subheader("Detalle de un par")
elegido = st.selectbox("Par", list(m.index), format_func=lambda i: m.loc[i, "par"])
a, b = m.loc[elegido, "a"], m.loc[elegido, "b"]
r = independencia(df[a], df[b])
col1, col2, col3 = st.columns(3)
col1.metric("P(A ∩ B)", pct(r.p_ab), delta=f"n = {c.entero(r.casos)} casos",
            delta_color="off", delta_arrow="off")
col2.metric("P(A)·P(B)", pct(r.producto), delta=f"n = {c.entero(r.casos)} casos",
            delta_color="off", delta_arrow="off")
col3.metric("P(A | B)", pct(r.p_a_dado_b), delta=f"frente a P(A) = {pct(r.p_a)}",
            delta_color="off", delta_arrow="off")
st.info(texto_independencia(c.NOMBRE_CORTO[a], c.NOMBRE_CORTO[b], r, EPSILON_INDEPENDENCIA))
