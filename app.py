"""Entrada de Streamlit: navegación y barra lateral común."""

import streamlit as st

from paginas import _comun

st.set_page_config(page_title="Clima para trekking en Córdoba", page_icon="🥾", layout="wide")

_comun.barra_lateral()

navegacion = st.navigation(
    [
        st.Page("paginas/datos.py", title="1. Datos", url_path="datos", default=True),
        st.Page("paginas/eventos_espacio.py", title="2. Eventos y espacio muestral",
                url_path="eventos"),
        st.Page("paginas/frecuencias.py", title="3. Frecuencias relativas", url_path="frecuencias"),
        st.Page("paginas/clasica_frecuencial.py", title="4. Probabilidad clásica y frecuencial",
                url_path="clasica-frecuencial"),
        st.Page("paginas/condicional.py", title="5. Probabilidad condicional",
                url_path="condicional"),
        st.Page("paginas/independencia.py", title="6. Independencia", url_path="independencia"),
        st.Page("paginas/experimento.py", title="7. Experimento aleatorio",
                url_path="experimento"),
        st.Page("paginas/recomendacion.py", title="8. Recomendación", url_path="recomendacion"),
    ]
)
navegacion.run()
