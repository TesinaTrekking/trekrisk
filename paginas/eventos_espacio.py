"""Pantalla 2: eventos y espacio muestral."""

import plotly.graph_objects as go
import streamlit as st

from core.eventos import espacio_muestral
from core.interpretacion import pct, texto_frecuencia
from core.probabilidad import frecuencia_relativa
from paginas import _comun as c

st.title("Eventos y espacio muestral")
st.markdown("**Pregunta del guía:** ¿de cuántas maneras puede ser el clima de un día y cuáles "
            "de esas maneras son aptas para salir?")

df = c.datos_filtrados()
if df is None:
    st.stop()
u = c.umbrales_actuales()

st.markdown(
    "El **experimento aleatorio** es observar el clima de un día en una zona. Los eventos, con los "
    "umbrales vigentes:\n\n"
    f"- **A, lluvia:** precipitación ≥ {c.numero(u.lluvia_mm)} mm\n"
    f"- **B, viento fuerte:** viento máximo ≥ {c.numero(u.viento_kmh)} km/h\n"
    f"- **C, temperatura extrema:** máxima ≥ {c.numero(u.calor_c)} °C **o** mínima ≤ "
    f"{c.numero(u.helada_c)} °C\n"
    "- **D, lluvia ayer:** hubo lluvia el día anterior en la misma zona\n"
    "- **Día apto:** no ocurre A, ni B, ni C\n"
    "- **Día adverso:** ocurre al menos uno de A, B o C"
)

st.latex(r"\Omega = \{\text{A, no A}\} \times \{\text{B, no B}\} \times \{\text{C, no C}\}"
         r"\quad\Rightarrow\quad |\Omega| = 2 \times 2 \times 2 = 8")
st.latex(r"\text{apto} = A^c \cap B^c \cap C^c \qquad \text{adverso} = A \cup B \cup C")

col1, col2 = st.columns(2)
apto = frecuencia_relativa(df["apto"])
adverso = frecuencia_relativa(df["adverso"])
with col1:
    c.metrica("Día apto", apto)
with col2:
    c.metrica("Día adverso", adverso)

tabla = espacio_muestral(df)


def _etiqueta(fila) -> str:
    letras = [letra for letra, col in (("A", "lluvia"), ("B", "viento_fuerte"),
                                       ("C", "temp_extrema")) if fila[col]]
    return " + ".join(letras) if letras else "Ninguno"


tabla["resultado_elemental"] = tabla.apply(_etiqueta, axis=1)
orden = tabla.sort_values("frecuencia_relativa")
fig = go.Figure(go.Bar(
    x=orden["frecuencia_relativa"], y=orden["resultado_elemental"], orientation="h",
    marker_color=[c.VERDE if r == "apto" else c.OCRE for r in orden["resultado"]],
    text=[pct(v) for v in orden["frecuencia_relativa"]], textposition="outside",
    customdata=orden["casos"], hovertemplate="%{y}: %{text} (%{customdata} casos)<extra></extra>",
))
c.estilo(fig, "Frecuencia relativa", "Resultado elemental")
fig.update_xaxes(tickformat=".0%")
st.plotly_chart(fig, width="stretch")

mostrar = tabla.assign(
    lluvia=tabla["lluvia"].map({True: "Sí", False: "No"}),
    viento_fuerte=tabla["viento_fuerte"].map({True: "Sí", False: "No"}),
    temp_extrema=tabla["temp_extrema"].map({True: "Sí", False: "No"}),
    casos=tabla["casos"].map(c.entero),
    frecuencia_relativa=tabla["frecuencia_relativa"].map(pct),
    resultado=tabla["resultado"].str.capitalize(),
)[["lluvia", "viento_fuerte", "temp_extrema", "casos", "frecuencia_relativa", "resultado"]]
mostrar.columns = ["A: lluvia", "B: viento fuerte", "C: temp. extrema", "Casos",
                   "Frecuencia relativa", "Resultado"]
c.tabla(mostrar)
st.caption(f"Total: {c.entero(tabla['casos'].sum())} días. Los 8 resultados no son equiprobables.")

st.info(texto_frecuencia("un día apto", apto) + " " + texto_frecuencia("un día adverso", adverso))
