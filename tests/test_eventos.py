"""Pruebas de core/eventos.py con DataFrames armados a mano."""

import pandas as pd

from core.config import Umbrales
from core.eventos import espacio_muestral, marcar_eventos


def _df(filas: list[tuple]) -> pd.DataFrame:
    """Filas: (zona, fecha, lluvia_mm, viento, tmax, tmin)."""
    return pd.DataFrame(
        [
            {
                "zona": z, "fecha": pd.Timestamp(f), "precipitacion_mm": p,
                "viento_kmh": v, "racha_kmh": v + 10, "tmax_c": tx, "tmin_c": tn,
            }
            for z, f, p, v, tx, tn in filas
        ]
    )


def test_dia_en_el_umbral_cuenta_como_evento():
    df = _df([("a", "2021-01-01", 1.0, 30.0, 32.0, 5.0), ("a", "2021-01-02", 0.9, 29.9, 31.9, 0.1)])
    r = marcar_eventos(df, Umbrales())
    assert r.loc[0, ["lluvia", "viento_fuerte", "temp_extrema"]].tolist() == [True, True, True]
    assert r.loc[1, ["lluvia", "viento_fuerte", "temp_extrema"]].tolist() == [False, False, False]


def test_temp_extrema_por_calor_o_por_helada():
    df = _df([
        ("a", "2021-01-01", 0, 0, 33.0, 10.0),  # calor
        ("a", "2021-01-02", 0, 0, 20.0, 0.0),   # helada en el umbral
        ("a", "2021-01-03", 0, 0, 20.0, 1.0),   # ninguna
    ])
    assert marcar_eventos(df, Umbrales())["temp_extrema"].tolist() == [True, True, False]


def test_apto_es_el_complemento_de_la_union():
    df = _df([
        ("a", "2021-01-01", 0, 0, 20, 10),   # apto
        ("a", "2021-01-02", 5, 0, 20, 10),   # lluvia
        ("a", "2021-01-03", 0, 40, 20, 10),  # viento
        ("a", "2021-01-04", 0, 0, 20, -3),   # helada
    ])
    r = marcar_eventos(df, Umbrales())
    assert r["apto"].tolist() == [True, False, False, False]
    union = r["lluvia"] | r["viento_fuerte"] | r["temp_extrema"]
    assert (r["adverso"] == union).all()
    assert (r["apto"] == ~r["adverso"]).all()


def test_umbrales_personalizados_recalculan():
    df = _df([("a", "2021-01-01", 2.0, 0, 20, 10)])
    assert marcar_eventos(df, Umbrales(lluvia_mm=3.0))["lluvia"].iloc[0] == False  # noqa: E712
    assert marcar_eventos(df, Umbrales(lluvia_mm=2.0))["lluvia"].iloc[0] == True  # noqa: E712


def test_lluvia_ayer_primer_dia_de_cada_zona_es_na_y_no_cruza_zonas():
    df = _df([
        ("a", "2021-01-01", 5, 0, 20, 10),
        ("a", "2021-01-02", 0, 0, 20, 10),
        ("b", "2021-01-01", 0, 0, 20, 10),
        ("b", "2021-01-02", 5, 0, 20, 10),
    ])
    d = marcar_eventos(df, Umbrales())["lluvia_ayer"]
    assert d.isna().tolist() == [True, False, True, False]
    assert d.iloc[1] == True   # ayer llovió en a  # noqa: E712
    assert d.iloc[3] == False  # ayer no llovió en b; no hereda de a  # noqa: E712


def test_lluvia_ayer_respeta_el_orden_original_y_los_huecos():
    df = _df([
        ("a", "2021-01-03", 0, 0, 20, 10),
        ("a", "2021-01-01", 5, 0, 20, 10),
        ("a", "2021-01-02", 5, 0, 20, 10),
        ("a", "2021-01-10", 0, 0, 20, 10),  # hueco: sin día anterior
    ])
    d = marcar_eventos(df, Umbrales())["lluvia_ayer"]
    assert d.isna().tolist() == [False, True, False, True]
    assert d.iloc[0] == True  # noqa: E712


def test_espacio_muestral_tiene_8_filas_y_suma_el_total():
    df = _df([
        ("a", "2021-01-01", 0, 0, 20, 10),
        ("a", "2021-01-02", 5, 0, 20, 10),
        ("a", "2021-01-03", 5, 40, 20, 10),
        ("a", "2021-01-04", 0, 0, 20, 10),
    ])
    tabla = espacio_muestral(marcar_eventos(df, Umbrales()))
    assert len(tabla) == 8
    assert tabla["casos"].sum() == 4
    assert abs(tabla["frecuencia_relativa"].sum() - 1.0) < 1e-12
    apto = tabla[(~tabla["lluvia"]) & (~tabla["viento_fuerte"]) & (~tabla["temp_extrema"])]
    assert apto["casos"].iloc[0] == 2 and apto["resultado"].iloc[0] == "apto"
    assert (tabla[tabla["resultado"] == "adverso"].shape[0]) == 7
    assert (tabla["casos"] == 0).sum() == 5  # los no observados aparecen con 0
