"""Pruebas de core/probabilidad.py con casos calculados a mano."""

import math

import pandas as pd
import pytest

from core.probabilidad import (
    Resultado,
    convergencia,
    frecuencia_relativa,
    frecuencias_por_grupo,
    independencia,
    matriz_condicional,
    matriz_independencia,
    probabilidad_clasica_fecha,
    probabilidad_clasica_uniforme,
    probabilidad_condicional,
    probabilidad_frecuencial,
    ranking_zona_mes,
)

# 10 filas: llueve en 4 (días 0 a 3); viento en 5 (días 2 a 6)
LLUVIA = pd.Series([True] * 4 + [False] * 6)
VIENTO = pd.Series([False, False, True, True, True, True, True, False, False, False])


def test_frecuencia_relativa_10_filas():
    r = frecuencia_relativa(LLUVIA)
    assert (r.favorables, r.totales) == (4, 10)
    assert r.valor == pytest.approx(0.4)
    assert r.poca_muestra  # 10 < 30


def test_frecuencia_relativa_con_universo():
    r = frecuencia_relativa(LLUVIA, universo=VIENTO)
    assert (r.favorables, r.totales) == (2, 5)
    assert r.valor == pytest.approx(0.4)


def test_frecuencia_relativa_excluye_na():
    ev = pd.Series([pd.NA, True, False, True], dtype="boolean")
    r = frecuencia_relativa(ev)
    assert (r.favorables, r.totales) == (2, 3)


def test_poca_muestra_en_el_limite():
    assert Resultado(0.5, 15, 29).poca_muestra
    assert not Resultado(0.5, 15, 30).poca_muestra


def test_clasica_fecha_y_frecuencial_coinciden_con_la_frecuencia():
    df = pd.DataFrame({"lluvia": LLUVIA})
    assert probabilidad_clasica_fecha(df, "lluvia").valor == pytest.approx(0.4)
    assert probabilidad_frecuencial(LLUVIA) == frecuencia_relativa(LLUVIA)


def test_clasica_uniforme_sorteo_de_mes():
    meses = list(range(1, 13))
    r = probabilidad_clasica_uniforme(meses, {6, 7, 8})
    assert (r.favorables, r.totales) == (3, 12)
    assert r.valor == pytest.approx(0.25)
    assert probabilidad_clasica_uniforme([], {1}).valor is None


def test_frecuencias_por_grupo():
    df = pd.DataFrame({"zona": ["a"] * 4 + ["b"] * 6, "lluvia": LLUVIA})
    t = frecuencias_por_grupo(df, "lluvia", "zona").set_index("zona")
    assert (t.loc["a", "favorables"], t.loc["a", "totales"]) == (4, 4)
    assert t.loc["b", "frecuencia_relativa"] == 0.0
    assert list(t.columns) == ["favorables", "totales", "frecuencia_relativa"]


def test_convergencia_acumulada():
    c = convergencia(pd.Series([True, False, True, True]))
    assert c["n"].tolist() == [1, 2, 3, 4]
    assert c["frecuencia_acumulada"].tolist() == pytest.approx([1.0, 0.5, 2 / 3, 0.75])


def test_condicional_valores_conocidos():
    # A ∩ B = días 2 y 3 (2); n(B) = 5; n(A) = 4
    r = probabilidad_condicional(LLUVIA, VIENTO)
    assert (r.favorables, r.totales) == (2, 5)
    assert r.valor == pytest.approx(0.4)
    r2 = probabilidad_condicional(VIENTO, LLUVIA)  # P(B|A) = 2/4
    assert (r2.favorables, r2.totales) == (2, 4)
    assert r2.valor == pytest.approx(0.5)


def test_condicional_con_nb_cero_devuelve_none():
    r = probabilidad_condicional(LLUVIA, pd.Series([False] * 10))
    assert r.valor is None
    assert (r.favorables, r.totales) == (0, 0)


def test_condicional_ignora_na():
    a = pd.Series([True, True, False, True])
    b = pd.Series([pd.NA, True, True, True], dtype="boolean")
    r = probabilidad_condicional(a, b)
    assert (r.favorables, r.totales) == (2, 3)


def test_matriz_condicional_formato_largo():
    df = pd.DataFrame({
        "zona": ["a", "a", "a", "b"],
        "mes": [1, 1, 2, 1],
        "apto": [True, False, True, True],
    })
    m = matriz_condicional(df, "apto")
    assert list(m.columns) == ["fila", "columna", "favorables", "totales", "probabilidad"]
    fila = m[(m["fila"] == "a") & (m["columna"] == 1)].iloc[0]
    assert (fila["favorables"], fila["totales"], fila["probabilidad"]) == (1, 2, 0.5)


def test_independencia_par_independiente_y_par_dependiente():
    a = pd.Series([True, True, False, False])
    b = pd.Series([True, False, True, False])
    ind = independencia(a, b)
    assert ind.independientes and ind.diferencia == pytest.approx(0.0)
    assert ind.p_a_dado_b == pytest.approx(0.5) and ind.casos == 4

    dep = independencia(a, a)  # P(A∩A) = 0,5 vs 0,25
    assert not dep.independientes
    assert dep.diferencia == pytest.approx(0.25)


def test_independencia_usa_epsilon():
    a = pd.Series([True, True, False, False])
    assert not independencia(a, a, epsilon=0.02).independientes
    assert independencia(a, a, epsilon=0.30).independientes


def test_independencia_con_pb_cero():
    r = independencia(LLUVIA, pd.Series([False] * 10))
    assert r.p_a_dado_b is None and r.p_ab == 0.0


def test_independencia_sin_casos():
    r = independencia(pd.Series([], dtype=bool), pd.Series([], dtype=bool))
    assert r.casos == 0 and not r.independientes and math.isnan(r.p_a)


def test_matriz_independencia_tiene_6_pares_con_4_eventos():
    df = pd.DataFrame({"A": LLUVIA, "B": VIENTO, "C": LLUVIA[::-1].reset_index(drop=True),
                       "D": pd.Series([pd.NA] + [True] * 9, dtype="boolean")})
    m = matriz_independencia(df, ["A", "B", "C", "D"])
    assert len(m) == 6
    assert m[(m["a"] == "A") & (m["b"] == "D")]["casos"].iloc[0] == 9


def test_ranking_zona_mes_ordenado():
    df = pd.DataFrame({
        "zona": ["a", "a", "b", "b", "b"],
        "mes": [1, 1, 1, 2, 2],
        "apto": [True, False, True, True, True],
    })
    r = ranking_zona_mes(df)
    assert list(r.columns) == ["zona", "mes", "favorables", "totales", "probabilidad"]
    assert r["probabilidad"].tolist() == [1.0, 1.0, 0.5]
    assert (r.iloc[0]["zona"], r.iloc[0]["mes"], r.iloc[0]["totales"]) == ("b", 2, 2)
