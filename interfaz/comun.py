"""Piezas compartidas por el tablero: filtros, datos filtrados, formato y estilo de gráficos."""

from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.config import FECHA_FIN, FECHA_INICIO, ZONAS, Umbrales
from core.datos import cargar_clima
from core.eventos import marcar_eventos
from core.interpretacion import pct, texto_poca_muestra
from core.probabilidad import Resultado

CARPETA_DATOS = str(Path(__file__).resolve().parent.parent / "data")
FUENTE = "Fuente: [Open-Meteo](https://open-meteo.com/) (reanálisis ERA5), datos de archivo."

NOMBRE_ZONA: dict[str, str] = {z.slug: z.nombre for z in ZONAS}
MESES: list[str] = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                    "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
ESTACIONES: list[str] = ["verano", "otoño", "invierno", "primavera"]

# Evento -> cómo se nombra en los textos ("la probabilidad de ...") y como condición ("cuando ...")
EVENTOS: dict[str, str] = {
    "lluvia": "A: lluvia",
    "viento_fuerte": "B: viento fuerte",
    "temp_extrema": "C: temperatura extrema",
    "lluvia_ayer": "D: lluvia el día anterior",
    "apto": "Día apto",
    "adverso": "Día adverso",
}
NOMBRE_EVENTO: dict[str, str] = {
    "lluvia": "un día de lluvia",
    "viento_fuerte": "un día de viento fuerte",
    "temp_extrema": "un día de temperatura extrema",
    "lluvia_ayer": "lluvia el día anterior",
    "apto": "un día apto",
    "adverso": "un día adverso",
}
CONDICION_EVENTO: dict[str, str] = {
    "lluvia": "hay lluvia",
    "viento_fuerte": "hay viento fuerte",
    "temp_extrema": "hay temperatura extrema",
    "lluvia_ayer": "llovió el día anterior",
    "apto": "el día es apto",
    "adverso": "el día es adverso",
}

VERDE, OCRE, AZUL, ROJO, GRIS = "#2F6B4F", "#B5832B", "#3F6C8F", "#A8452F", "#7A857E"
PALETA = [VERDE, OCRE, AZUL, ROJO, GRIS]
COLOR_ZONA: dict[str, str] = {z.slug: PALETA[i] for i, z in enumerate(ZONAS)}
COLOR_ZONA_NOMBRE: dict[str, str] = {NOMBRE_ZONA[slug]: col for slug, col in COLOR_ZONA.items()}

_CLAVES_UMBRAL = {
    "u_lluvia": "lluvia_mm",
    "u_viento": "viento_kmh",
    "u_calor": "calor_c",
    "u_helada": "helada_c",
}


def entero(x: int) -> str:
    """Entero con punto como separador de miles."""
    return f"{int(x):,}".replace(",", ".")


def numero(x: float, decimales: int = 1) -> str:
    """Número con coma decimal."""
    return f"{x:.{decimales}f}".replace(".", ",")


def _restablecer_umbrales() -> None:
    for clave, campo in _CLAVES_UMBRAL.items():
        st.session_state[clave] = getattr(Umbrales(), campo)


def _inicializar_estado() -> None:
    """Valores por defecto de los filtros, sin pisar los que ya eligió el usuario."""
    st.session_state.setdefault("zonas_sel", [z.slug for z in ZONAS])
    st.session_state.setdefault(
        "rango_fechas", (date.fromisoformat(FECHA_INICIO), date.fromisoformat(FECHA_FIN))
    )
    for clave, campo in _CLAVES_UMBRAL.items():
        st.session_state.setdefault(clave, getattr(Umbrales(), campo))


def barra_lateral() -> None:
    """Dibuja los umbrales en la barra lateral. Los valores quedan en st.session_state."""
    _inicializar_estado()
    with st.sidebar:
        st.header("Umbrales")
        st.number_input("Lluvia (mm) ≥", min_value=0.0, step=0.5, key="u_lluvia",
                        help="Un día con precipitación ≥ este valor es lluvioso.")
        st.number_input("Viento (km/h) ≥", min_value=0.0, step=1.0, key="u_viento",
                        help="Viento máximo ≥ este valor es viento fuerte.")
        st.number_input("Calor (°C) ≥", step=1.0, key="u_calor",
                        help="Temperatura máxima ≥ este valor es calor extremo.")
        st.number_input("Helada (°C) ≤", step=1.0, key="u_helada",
                        help="Temperatura mínima ≤ este valor es helada.")
        st.button("Restablecer umbrales", on_click=_restablecer_umbrales)
        st.caption("Un día es apto si no hay lluvia, ni viento fuerte, ni temperatura extrema "
                   "(calor o helada).")


def filtros_superiores() -> None:
    """Dibuja el selector de zonas y el rango de fechas arriba del tablero."""
    _inicializar_estado()
    col_zonas, col_fechas = st.columns([3, 1])
    with col_zonas:
        st.pills("Zonas a comparar", [z.slug for z in ZONAS], selection_mode="multi",
                 key="zonas_sel", format_func=NOMBRE_ZONA.get)
    with col_fechas:
        st.date_input("Rango de fechas", key="rango_fechas",
                      min_value=date.fromisoformat(FECHA_INICIO),
                      max_value=date.fromisoformat(FECHA_FIN))


def umbrales_actuales() -> Umbrales:
    """Umbrales vigentes según la barra lateral (o los de por defecto)."""
    _inicializar_estado()
    return Umbrales(**{campo: float(st.session_state[clave])
                       for clave, campo in _CLAVES_UMBRAL.items()})


@st.cache_data(show_spinner=False)
def _clima_con_eventos(lluvia: float, viento: float, calor: float, helada: float) -> pd.DataFrame:
    """Carga todo el clima y marca los eventos; se recalcula solo si cambia un umbral."""
    clima = cargar_clima(CARPETA_DATOS)
    return marcar_eventos(clima, Umbrales(lluvia, viento, calor, helada))


def datos_filtrados() -> pd.DataFrame | None:
    """Datos con eventos, ya filtrados por zonas y fechas. None (con aviso) si no hay filas.

    Los eventos se marcan antes de filtrar para que lluvia_ayer use el día real anterior.
    """
    _inicializar_estado()
    u = umbrales_actuales()
    try:
        df = _clima_con_eventos(u.lluvia_mm, u.viento_kmh, u.calor_c, u.helada_c)
    except FileNotFoundError as error:
        st.error(f"{error}")
        return None

    rango = st.session_state["rango_fechas"]
    if not isinstance(rango, (tuple, list)) or len(rango) != 2:
        st.warning("Elegí una fecha de inicio y una de fin.")
        return None
    desde, hasta = pd.Timestamp(rango[0]), pd.Timestamp(rango[1])
    filtrado = df[df["zona"].isin(st.session_state["zonas_sel"])
                  & (df["fecha"] >= desde) & (df["fecha"] <= hasta)]
    if filtrado.empty:
        st.warning("Los filtros dejan cero filas. Elegí al menos una zona y un rango con datos.")
        return None
    return filtrado


def metrica(etiqueta: str, r: Resultado) -> None:
    """st.metric con el valor en porcentaje y la cantidad de casos; avisa si son pocos."""
    st.metric(etiqueta, pct(r.valor), delta=f"{entero(r.favorables)} de {entero(r.totales)} casos",
              delta_color="off", delta_arrow="off")
    if r.poca_muestra:
        st.caption(texto_poca_muestra())


def estilo(fig: go.Figure, titulo_x: str = "", titulo_y: str = "", porcentaje: bool = False) -> go.Figure:
    """Aplica el estilo común: colores del tema, ejes rotulados y coma decimal."""
    fig.update_layout(
        separators=",.", colorway=PALETA, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)", font={"color": "#1F2A24"},
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        xaxis_title=titulo_x, yaxis_title=titulo_y, legend_title_text="",
    )
    fig.update_xaxes(gridcolor="#E3E3DA")
    fig.update_yaxes(gridcolor="#E3E3DA")
    if porcentaje:
        fig.update_yaxes(tickformat=".0%")
    return fig


def tabla(df: pd.DataFrame) -> None:
    """Muestra una tabla sin índice."""
    st.dataframe(df, hide_index=True, width="stretch")


NOMBRE_CORTO: dict[str, str] = {
    "lluvia": "lluvia",
    "viento_fuerte": "viento fuerte",
    "temp_extrema": "temperatura extrema",
    "lluvia_ayer": "lluvia ayer",
    "apto": "día apto",
    "adverso": "día adverso",
}
