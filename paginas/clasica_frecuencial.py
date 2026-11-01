"""Pantalla 4: probabilidad clásica y frecuencial."""

import plotly.graph_objects as go
import streamlit as st

from core.interpretacion import pct, texto_clasica, texto_frecuencial
from core.probabilidad import (
    convergencia, probabilidad_clasica_fecha, probabilidad_clasica_uniforme,
    probabilidad_frecuencial,
)
from paginas import _comun as c

st.title("Probabilidad clásica y frecuencial")
st.markdown("**Pregunta del guía:** si sorteo un día, un mes o una zona, ¿qué probabilidad hay "
            "de cada resultado, y qué probabilidad puedo esperar para un día futuro?")

df = c.datos_filtrados()
if df is None:
    st.stop()

with st.expander("¿Cuál es la diferencia entre clásica y frecuencial?", expanded=True):
    st.markdown(
        "- **Clásica:** se sortea una fecha, un mes o una zona del registro y todos los casos son "
        "equiprobables, por lo que el cálculo es exacto dentro del registro.\n"
        "- **Frecuencial:** se usa la frecuencia observada como estimación de la probabilidad de "
        "un día futuro, y se muestra cómo se estabiliza al sumar días."
    )

izq, der = st.columns(2)
evento = izq.selectbox("Evento", list(c.EVENTOS), format_func=c.EVENTOS.get, index=4)
sorteo = der.radio("Sorteo equiprobable de", ["Una fecha", "Un mes", "Una zona"], horizontal=True)

col_clasica, col_frecuencial = st.columns(2)

with col_clasica:
    st.subheader("Clásica")
    st.latex(r"P(E) = \frac{\text{casos favorables}}{\text{casos posibles}}")
    nombre = c.NOMBRE_EVENTO[evento]
    if sorteo == "Una fecha":
        clasica = probabilidad_clasica_fecha(df, evento)
        descripcion, sorteado = f"{nombre}", "un día del registro"
    elif sorteo == "Un mes":
        meses = sorted(df["mes"].unique())
        elegidos = st.multiselect("Meses favorables", meses, default=[m for m in (6, 7, 8) if m in meses],
                                  format_func=lambda m: c.MESES[m - 1])
        clasica = probabilidad_clasica_uniforme(meses, set(elegidos))
        descripcion = "que salga " + (", ".join(c.MESES[m - 1] for m in elegidos) or "ningún mes")
        sorteado = "un mes"
    else:
        zonas = sorted(df["zona"].unique())
        elegidas = st.multiselect("Zonas favorables", zonas, default=zonas[:1],
                                  format_func=c.NOMBRE_ZONA.get)
        clasica = probabilidad_clasica_uniforme(zonas, set(elegidas))
        descripcion = "que salga " + (", ".join(c.NOMBRE_ZONA[z] for z in elegidas) or "ninguna zona")
        sorteado = "una zona"
    c.metrica("P clásica", clasica)
    st.info(texto_clasica(descripcion, clasica, sorteado))

ordenado = df.sort_values("fecha")[evento]
frecuencial = probabilidad_frecuencial(ordenado)
with col_frecuencial:
    st.subheader("Frecuencial")
    st.latex(r"P(E) \approx fr(E) = \frac{\text{casos con } E}{\text{casos totales}}")
    c.metrica(f"P frecuencial de «{c.EVENTOS[evento]}»", frecuencial)
    st.info(texto_frecuencial(c.NOMBRE_EVENTO[evento], frecuencial))

st.subheader("Cómo se estabiliza la frecuencia")
curva = convergencia(ordenado)
fig = go.Figure(go.Scatter(x=curva["n"], y=curva["frecuencia_acumulada"], mode="lines",
                           line={"color": c.VERDE}, name="Frecuencia acumulada"))
if frecuencial.valor is not None:
    fig.add_hline(y=frecuencial.valor, line_dash="dash", line_color=c.OCRE,
                  annotation_text=f"Registro completo: {pct(frecuencial.valor)}")
c.estilo(fig, "Días acumulados (orden cronológico)", "Frecuencia relativa acumulada",
         porcentaje=True)
st.plotly_chart(fig, width="stretch")
st.caption(f"La curva suma los {c.entero(len(curva))} días del filtro, de la fecha más antigua a "
           "la más reciente.")
