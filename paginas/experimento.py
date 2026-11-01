"""Pantalla 7: experimento aleatorio (remuestreo de días reales)."""

import plotly.graph_objects as go
import streamlit as st

from core.interpretacion import pct, texto_simulacion
from core.probabilidad import Resultado, frecuencia_relativa
from core.simulacion import simular
from paginas import _comun as c

st.title("Experimento aleatorio")
st.markdown("**Pregunta del guía:** si saco días al azar del registro, ¿la frecuencia se acerca a "
            "la probabilidad del registro?")
st.markdown("No se inventan datos: se **remuestrean con reposición días reales** del registro "
            "filtrado. Misma semilla, mismo resultado.")
st.latex(r"fr_n(E) = \frac{\text{sorteos con } E}{n} \;\longrightarrow\; P(E)\ \text{del registro}")

df = c.datos_filtrados()
if df is None:
    st.stop()

izq, der = st.columns(2)
evento = izq.selectbox("Evento", list(c.EVENTOS), format_func=c.EVENTOS.get, index=4)
n = der.slider("Cantidad de sorteos (N)", min_value=100, max_value=100_000, value=1_000, step=100)
semilla = c.semilla_actual()
st.caption(f"Semilla: {semilla} (se cambia en la barra lateral).")

r = simular(df[evento], n, semilla)
registro = frecuencia_relativa(df[evento])
simulada = Resultado(r.frecuencia_final, int(round(r.frecuencia_final * n)), n)

col1, col2 = st.columns(2)
with col1:
    c.metrica("Frecuencia tras N sorteos", simulada)
with col2:
    c.metrica("Probabilidad del registro", registro)

fig = go.Figure(go.Scattergl(x=r.curva["n"], y=r.curva["frecuencia_acumulada"], mode="lines",
                             line={"color": c.VERDE}, name="Frecuencia acumulada"))
fig.add_hline(y=r.probabilidad_registro, line_dash="dash", line_color=c.OCRE,
              annotation_text=f"Registro: {pct(r.probabilidad_registro)}")
c.estilo(fig, "Sorteos acumulados (N)", "Frecuencia relativa acumulada", porcentaje=True)
st.plotly_chart(fig, width="stretch")
st.info(texto_simulacion(r, c.NOMBRE_EVENTO[evento]))
