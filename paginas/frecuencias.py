"""Pantalla 3: frecuencias relativas por zona, mes o estación."""

import plotly.express as px
import streamlit as st

from core.interpretacion import pct, texto_frecuencia
from core.probabilidad import frecuencia_relativa, frecuencias_por_grupo
from paginas import _comun as c

AGRUPACIONES = {"zona": "Zona", "mes": "Mes", "estacion": "Estación"}

st.title("Frecuencias relativas")
st.markdown("**Pregunta del guía:** ¿con qué frecuencia ocurre cada evento y cómo cambia según la "
            "zona, el mes o la estación?")
st.latex(r"fr(E) = \frac{\text{casos con } E}{\text{casos totales}}")

df = c.datos_filtrados()
if df is None:
    st.stop()

izq, der = st.columns(2)
evento = izq.selectbox("Evento", list(c.EVENTOS), format_func=c.EVENTOS.get, index=4)
agrupacion = der.selectbox("Agrupar por", list(AGRUPACIONES), format_func=AGRUPACIONES.get)

general = frecuencia_relativa(df[evento])
c.metrica(f"Frecuencia general de «{c.EVENTOS[evento]}»", general)

por = [agrupacion]
if agrupacion != "zona" and df["zona"].nunique() > 1:
    por.append("zona")
t = frecuencias_por_grupo(df, evento, por)
t["zona_nombre"] = t["zona"].map(c.NOMBRE_ZONA) if "zona" in t else None
if agrupacion == "mes":
    t["grupo"] = t["mes"].map(lambda m: c.MESES[m - 1].capitalize())
    orden = [m.capitalize() for m in c.MESES]
elif agrupacion == "estacion":
    t["grupo"] = t["estacion"].str.capitalize()
    orden = [e.capitalize() for e in c.ESTACIONES]
else:
    t["grupo"] = t["zona_nombre"]
    orden = [c.NOMBRE_ZONA[z] for z in c.NOMBRE_ZONA]

fig = px.bar(t, x="grupo", y="frecuencia_relativa", barmode="group",
             color="zona_nombre" if "zona" in por else None,
             color_discrete_sequence=c.PALETA, category_orders={"grupo": orden},
             custom_data=["favorables", "totales"])
fig.update_traces(hovertemplate="%{x}: %{y:.1%} (%{customdata[0]} de %{customdata[1]} casos)"
                  "<extra></extra>")
c.estilo(fig, AGRUPACIONES[agrupacion], "Frecuencia relativa", porcentaje=True)
st.plotly_chart(fig, width="stretch")

con_zona = agrupacion != "zona" and "zona" in por
mostrar = t[["grupo", *(["zona_nombre"] if con_zona else []), "favorables", "totales",
             "frecuencia_relativa"]].copy()
mostrar["frecuencia_relativa"] = mostrar["frecuencia_relativa"].map(pct)
mostrar["favorables"] = mostrar["favorables"].map(c.entero)
mostrar["totales"] = mostrar["totales"].map(c.entero)
mostrar.columns = [AGRUPACIONES[agrupacion], *(["Zona"] if con_zona else []),
                   "Casos favorables", "Casos totales", "Frecuencia relativa"]
c.tabla(mostrar)

if (t["totales"] < 30).any():
    st.warning("Algunos grupos tienen menos de 30 casos; sus frecuencias son poco confiables.")
st.info(texto_frecuencia(c.NOMBRE_EVENTO[evento], general))
