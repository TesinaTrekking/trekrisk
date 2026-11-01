"""Tarjetas del tablero: cada una arma un gráfico o una tabla y una línea de interpretación."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.config import EPSILON_INDEPENDENCIA, MIN_CASOS, SEMILLA
from core.datos import COLUMNAS_BASE
from core.eventos import espacio_muestral
from core.interpretacion import (
    pct, texto_espacio_muestral, texto_frecuencia, texto_leyenda_eventos, texto_mapa_calor,
    texto_matriz_independencia, texto_poca_muestra, texto_recomendacion, texto_simulacion,
)
from core.probabilidad import (
    Resultado, frecuencia_relativa, frecuencias_por_grupo, grupo_mas_probable,
    matriz_condicional, matriz_independencia, ranking_zona_mes,
)
from core.simulacion import simular
from interfaz import comun as c

EVENTOS_INDEPENDENCIA = ["lluvia", "viento_fuerte", "temp_extrema", "lluvia_ayer"]
LETRA = dict(zip(EVENTOS_INDEPENDENCIA, "ABCD"))
COLOR_RESULTADO = {"Ninguno (apto)": c.VERDE, "A": c.AZUL, "B": c.GRIS, "C": c.OCRE,
                   "A + B": "#6E8FAE", "A + C": "#8C6F5A", "B + C": "#B7B08F",
                   "A + B + C": c.ROJO}
CANTIDAD_RANKING = 5


def _metrica_grupo(etiqueta: str, nombre: str, r: Resultado) -> None:
    """Métrica cuyo valor es el nombre de un grupo y cuyo detalle es su probabilidad y casos."""
    st.metric(etiqueta, nombre,
              delta=f"{pct(r.valor)} ({c.entero(r.favorables)} de {c.entero(r.totales)} días)",
              delta_color="off", delta_arrow="off")
    if r.poca_muestra:
        st.caption(texto_poca_muestra())


def fila_metricas(df: pd.DataFrame) -> None:
    """Fila de seis métricas del encabezado."""
    columnas = st.columns(6)
    with columnas[0]:
        c.metrica("Día apto", frecuencia_relativa(df["apto"]))
    with columnas[1]:
        zona = grupo_mas_probable(df, "apto", "zona")
        if zona:
            _metrica_grupo("Zona con más días aptos", c.NOMBRE_ZONA[zona[0]], zona[1])
    with columnas[2]:
        mes = grupo_mas_probable(df, "apto", "mes")
        if mes:
            _metrica_grupo("Mes con más días aptos", c.MESES[int(mes[0]) - 1].capitalize(), mes[1])
    with columnas[3]:
        c.metrica("Lluvia", frecuencia_relativa(df["lluvia"]))
    with columnas[4]:
        c.metrica("Viento fuerte", frecuencia_relativa(df["viento_fuerte"]))
    with columnas[5]:
        c.metrica("Temperatura extrema", frecuencia_relativa(df["temp_extrema"]))


@st.fragment
def tarjeta_frecuencias(df: pd.DataFrame) -> None:
    """Barras de la frecuencia relativa de un evento por mes, con un color por zona."""
    with st.container(border=True):
        st.subheader("Frecuencia por mes")
        evento = st.selectbox("Evento", list(c.EVENTOS), format_func=c.EVENTOS.get, index=4,
                              key="evento_frecuencias")
        t = frecuencias_por_grupo(df, evento, ["mes", "zona"])
        t["Mes"] = t["mes"].map(lambda m: c.MESES[m - 1].capitalize())
        t["Zona"] = t["zona"].map(c.NOMBRE_ZONA)
        fig = px.bar(t, x="Mes", y="frecuencia_relativa", color="Zona", barmode="group",
                     color_discrete_map=c.COLOR_ZONA_NOMBRE,
                     category_orders={"Mes": [m.capitalize() for m in c.MESES]},
                     custom_data=["favorables", "totales"])
        fig.update_traces(hovertemplate="%{x}, %{fullData.name}: %{y:.1%} "
                          "(%{customdata[0]} de %{customdata[1]} días)<extra></extra>")
        c.estilo(fig, "Mes", "Frecuencia relativa", porcentaje=True)
        st.plotly_chart(fig, width="stretch")
        st.caption(texto_frecuencia(c.NOMBRE_EVENTO[evento], frecuencia_relativa(df[evento])))


def _etiqueta_resultado(fila: pd.Series) -> str:
    letras = [letra for letra, col in (("A", "lluvia"), ("B", "viento_fuerte"),
                                       ("C", "temp_extrema")) if fila[col]]
    return " + ".join(letras) if letras else "Ninguno (apto)"


def tarjeta_espacio_muestral(df: pd.DataFrame) -> None:
    """Torta de los 8 resultados elementales del clima de un día."""
    with st.container(border=True):
        st.subheader("Los 8 resultados posibles")
        t = espacio_muestral(df)
        t["Resultado"] = t.apply(_etiqueta_resultado, axis=1)
        t = t[t["casos"] > 0]
        fig = px.pie(t, names="Resultado", values="casos", hole=0.4,
                     color="Resultado", color_discrete_map=COLOR_RESULTADO)
        fig.update_traces(textinfo="percent", hovertemplate="%{label}: %{value} días "
                          "(%{percent})<extra></extra>", sort=False)
        c.estilo(fig)
        fig.update_layout(legend={"orientation": "h"})
        st.plotly_chart(fig, width="stretch")
        st.caption(texto_espacio_muestral(frecuencia_relativa(df["apto"])))


def tarjeta_mapa_calor(df: pd.DataFrame) -> None:
    """Mapa de calor de P(apto) por zona y mes."""
    with st.container(border=True):
        st.subheader("Probabilidad de un día apto por zona y mes")
        m = matriz_condicional(df, "apto", "zona", "mes")
        zonas = [z for z in c.NOMBRE_ZONA if z in set(m["fila"])]
        z_valores, textos, casos = [], [], []
        for zona in zonas:
            fila = m[m["fila"] == zona].set_index("columna")
            meses = range(1, 13)
            z_valores.append([fila["probabilidad"].get(mm) for mm in meses])
            textos.append([pct(fila["probabilidad"].get(mm)) if mm in fila.index else ""
                           for mm in meses])
            casos.append([f"{c.entero(fila['favorables'].get(mm, 0))} de "
                          f"{c.entero(fila['totales'].get(mm, 0))}" for mm in meses])
        fig = go.Figure(go.Heatmap(
            z=z_valores, x=[mes[:3].capitalize() for mes in c.MESES],
            y=[c.NOMBRE_ZONA[z] for z in zonas], text=textos, texttemplate="%{text}",
            customdata=casos, zmin=0, zmax=1, colorscale=[[0, "#F3E3C3"], [1, c.VERDE]],
            colorbar={"tickformat": ".0%"},
            hovertemplate="%{y}, %{x}: %{text} (%{customdata} días)<extra></extra>",
        ))
        c.estilo(fig, "Mes", "Zona")
        st.plotly_chart(fig, width="stretch")
        st.caption(texto_mapa_calor(m))


def tarjeta_ranking(df: pd.DataFrame) -> None:
    """Las mejores y las peores combinaciones zona-mes."""
    with st.container(border=True):
        st.subheader("Mejores y peores combinaciones")
        ranking = ranking_zona_mes(df)
        mejores = ranking.head(CANTIDAD_RANKING).assign(Puesto="Mejor")
        # Con pocas combinaciones las dos listas no se pisan: lo que sobra es "Peor".
        peores = ranking.iloc[max(len(ranking) - CANTIDAD_RANKING, CANTIDAD_RANKING):]
        peores = peores.iloc[::-1].assign(Puesto="Peor")
        t = pd.concat([mejores, peores])
        mostrar = pd.DataFrame({
            "Puesto": t["Puesto"],
            "Zona": t["zona"].map(c.NOMBRE_ZONA),
            "Mes": t["mes"].map(lambda m: c.MESES[m - 1].capitalize()),
            "P(apto)": t["probabilidad"].map(pct),
            "Días aptos": t["favorables"].map(c.entero),
            "Días totales": t["totales"].map(c.entero),
            "Aviso": t["totales"].map(lambda n: f"Menos de {MIN_CASOS} casos"
                                      if n < MIN_CASOS else ""),
        })
        c.tabla(mostrar)
        st.caption(texto_recomendacion(ranking))


@st.fragment
def tarjeta_convergencia(df: pd.DataFrame) -> None:
    """Curva de convergencia del remuestreo de días reales."""
    with st.container(border=True):
        st.subheader("Experimento aleatorio: convergencia")
        izq, der = st.columns(2)
        evento = izq.selectbox("Evento", list(c.EVENTOS), format_func=c.EVENTOS.get, index=4,
                               key="evento_convergencia")
        n = der.slider("Cantidad de sorteos (N)", min_value=100, max_value=100_000, value=1_000,
                       step=100, key="n_sorteos")
        r = simular(df[evento], n, SEMILLA)
        fig = go.Figure(go.Scattergl(x=r.curva["n"], y=r.curva["frecuencia_acumulada"],
                                     mode="lines", line={"color": c.VERDE},
                                     name="Frecuencia acumulada"))
        fig.add_hline(y=r.probabilidad_registro, line_dash="dash", line_color=c.OCRE,
                      annotation_text=f"Registro: {pct(r.probabilidad_registro)}")
        c.estilo(fig, "Sorteos acumulados (N)", "Frecuencia relativa acumulada", porcentaje=True)
        st.plotly_chart(fig, width="stretch")
        st.caption(texto_simulacion(r, c.NOMBRE_EVENTO[evento]))


def tarjeta_independencia(df: pd.DataFrame) -> None:
    """P(A ∩ B) frente a P(A)·P(B) para los 6 pares de eventos."""
    with st.container(border=True):
        st.subheader("Independencia entre eventos")
        m = matriz_independencia(df, EVENTOS_INDEPENDENCIA)
        m["par"] = [f"{LETRA[a]}–{LETRA[b]}" for a, b in zip(m["a"], m["b"])]
        fig = go.Figure([
            go.Bar(name="P(A ∩ B)", x=m["par"], y=m["p_ab"], marker_color=c.VERDE),
            go.Bar(name="P(A)·P(B)", x=m["par"], y=m["producto"], marker_color=c.OCRE),
        ])
        fig.update_layout(barmode="group")
        c.estilo(fig, "Par de eventos", "Probabilidad", porcentaje=True)
        st.plotly_chart(fig, width="stretch")
        mostrar = pd.DataFrame({
            "Par": m["par"],
            "P(A ∩ B)": m["p_ab"].map(pct),
            "P(A)·P(B)": m["producto"].map(pct),
            "Diferencia": m["diferencia"].map(lambda d: f"{c.numero(d * 100)} puntos"),
            "Casos": m["casos"].map(c.entero),
            "Veredicto": m["independientes"].map({True: "Independientes",
                                                  False: "No independientes"}),
        })
        c.tabla(mostrar)
        leyenda = texto_leyenda_eventos(LETRA, c.NOMBRE_CORTO)
        st.caption(f"{leyenda}. " + texto_matriz_independencia(m, EPSILON_INDEPENDENCIA))


def tarjeta_datos(df: pd.DataFrame) -> None:
    """Tabla de datos crudos filtrados, con su fuente y rango."""
    with st.container(border=True):
        st.subheader("Datos crudos")
        crudo = df[COLUMNAS_BASE].copy()
        crudo["zona"] = crudo["zona"].map(c.NOMBRE_ZONA)
        crudo["fecha"] = crudo["fecha"].dt.strftime("%d/%m/%Y")
        c.tabla(crudo)
        desde, hasta = df["fecha"].min(), df["fecha"].max()
        st.caption(f"{c.entero(len(df))} días entre el {desde:%d/%m/%Y} y el {hasta:%d/%m/%Y}. "
                   + c.FUENTE)
