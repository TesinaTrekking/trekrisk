"""Eventos climáticos (A, B, C, D, apto, adverso) y espacio muestral."""

from itertools import product

import pandas as pd

from core.config import Umbrales

EVENTOS_BASE: list[str] = ["lluvia", "viento_fuerte", "temp_extrema"]


def _lluvia_ayer(df: pd.DataFrame) -> pd.Series:
    """Lluvia del día anterior en la misma zona; <NA> si no hay día anterior consecutivo."""
    orden = df.sort_values(["zona", "fecha"])
    grupos = orden.groupby("zona")
    ayer = grupos["lluvia"].shift(1).astype("boolean")
    es_consecutivo = grupos["fecha"].diff() == pd.Timedelta(days=1)
    return ayer.where(es_consecutivo).reindex(df.index)


def marcar_eventos(df: pd.DataFrame, umbrales: Umbrales) -> pd.DataFrame:
    """Devuelve una copia del DataFrame con las columnas de eventos.

    Agrega lluvia (A), viento_fuerte (B), temp_extrema (C), lluvia_ayer (D),
    apto y adverso. Requiere un índice sin repetidos y `fecha` como fecha.
    """
    salida = df.copy()
    salida["lluvia"] = salida["precipitacion_mm"] >= umbrales.lluvia_mm
    salida["viento_fuerte"] = salida["viento_kmh"] >= umbrales.viento_kmh
    salida["temp_extrema"] = (salida["tmax_c"] >= umbrales.calor_c) | (
        salida["tmin_c"] <= umbrales.helada_c
    )
    salida["lluvia_ayer"] = _lluvia_ayer(salida)
    salida["apto"] = ~salida["lluvia"] & ~salida["viento_fuerte"] & ~salida["temp_extrema"]
    salida["adverso"] = ~salida["apto"]
    return salida


def espacio_muestral(df: pd.DataFrame) -> pd.DataFrame:
    """Tabla de los 8 resultados elementales con sus casos y frecuencia relativa.

    Columnas: lluvia, viento_fuerte, temp_extrema, casos, frecuencia_relativa, resultado.
    Incluye los 8 resultados aunque alguno tenga 0 casos.
    """
    total = len(df)
    filas = []
    for a, b, c in product([True, False], repeat=3):
        casos = int(
            ((df["lluvia"] == a) & (df["viento_fuerte"] == b) & (df["temp_extrema"] == c)).sum()
        )
        filas.append(
            {
                "lluvia": a,
                "viento_fuerte": b,
                "temp_extrema": c,
                "casos": casos,
                "frecuencia_relativa": casos / total if total else float("nan"),
                "resultado": "adverso" if (a or b or c) else "apto",
            }
        )
    return pd.DataFrame(filas)
