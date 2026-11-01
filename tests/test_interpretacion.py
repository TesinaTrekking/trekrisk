"""Pruebas de core/interpretacion.py: valor, casos y advertencia de poca muestra."""

import pandas as pd

from core.interpretacion import (
    pct, texto_clasica, texto_condicional, texto_frecuencia, texto_frecuencial,
    texto_independencia, texto_espacio_muestral, texto_leyenda_eventos, texto_mapa_calor,
    texto_matriz_independencia, texto_poca_muestra, texto_recomendacion,
    texto_simulacion,
)
from core.probabilidad import Resultado, ResultadoIndependencia
from core.simulacion import simular

ADVERTENCIA = "menos de 30 casos"


def test_pct_formato_argentino():
    assert pct(0.123) == "12,3 %"
    assert pct(0.0) == "0,0 %"
    assert pct(None) == "sin datos"
    assert pct(float("nan")) == "sin datos"


def test_frecuencia_incluye_valor_casos_y_advertencia():
    t = texto_frecuencia("la lluvia", Resultado(0.4, 4, 10))
    assert "40,0 %" in t and "4 de 10" in t and ADVERTENCIA in t
    grande = texto_frecuencia("la lluvia", Resultado(0.5, 1500, 3000))
    assert "1.500 de 3.000" in grande and ADVERTENCIA not in grande
    assert "No hay días" in texto_frecuencia("la lluvia", Resultado(None, 0, 0))


def test_clasica_y_frecuencial():
    c = texto_clasica("un día apto", Resultado(0.25, 3, 12), "un mes")
    assert "25,0 %" in c and "3 de 12" in c and ADVERTENCIA in c
    f = texto_frecuencial("un día apto", Resultado(0.52, 4772, 9130))
    assert "52,0 %" in f and "4.772 de 9.130" in f and ADVERTENCIA not in f


def test_condicional_mayor_y_menor():
    t = texto_condicional("un día apto", "es invierno", Resultado(0.582, 421, 724),
                          Resultado(0.415, 3800, 9130))
    assert "58,2 %" in t and "n = 724" in t and "41,5 %" in t
    assert "más probable" in t and "16,7 puntos porcentuales" in t and ADVERTENCIA not in t
    menos = texto_condicional("un día apto", "es verano", Resultado(0.3, 100, 400),
                              Resultado(0.5, 10, 20))
    assert "menos probable" in menos


def test_condicional_casi_no_cambia_poca_muestra_y_sin_datos():
    t = texto_condicional("lluvia", "hay viento", Resultado(0.41, 8, 20), Resultado(0.40, 40, 100))
    assert "casi no cambia" in t and ADVERTENCIA in t
    sin = texto_condicional("lluvia", "hay viento", Resultado(None, 0, 0), Resultado(0.4, 4, 10))
    assert "No se puede calcular" in sin


def _indep(p_ab, producto, independientes, casos=9130):
    return ResultadoIndependencia(0.5, 0.06, p_ab, producto, abs(p_ab - producto), 0.5,
                                  independientes, casos)


def test_independencia_veredictos():
    ind = texto_independencia("A", "B", _indep(0.031, 0.029, True), 0.02)
    assert "3,1 %" in ind and "2,9 %" in ind and "0,2 puntos" in ind
    assert "menor que ε = 2,0 puntos" in ind and "se consideran independientes" in ind
    dep = texto_independencia("A", "D", _indep(0.25, 0.12, False), 0.02)
    assert "no se consideran independientes" in dep and "mayor o igual" in dep
    assert ADVERTENCIA in texto_independencia("A", "B", _indep(0.1, 0.1, True, casos=10), 0.02)


def test_simulacion_incluye_n_y_comparacion_sin_semilla():
    r = simular(pd.Series([True] * 40 + [False] * 60), 1000, 42)
    t = texto_simulacion(r, "la lluvia")
    assert "1.000" in t and "semilla" not in t and "40,0 %" in t and ADVERTENCIA not in t
    assert ADVERTENCIA in texto_simulacion(simular(pd.Series([True, False]), 10, 1), "la lluvia")


def test_recomendacion_mejor_y_peor():
    ranking = pd.DataFrame({
        "zona": ["condorito", "uritorco"], "mes": [6, 1],
        "favorables": [126, 20], "totales": [150, 155], "probabilidad": [0.84, 20 / 155],
    })
    t = texto_recomendacion(ranking)
    assert "Quebrada del Condorito en junio (84,0 %, 126 de 150 días)" in t
    assert "Cerro Uritorco en enero" in t and ADVERTENCIA not in t
    chico = ranking.assign(totales=[10, 155])
    assert ADVERTENCIA in texto_recomendacion(chico)
    assert "No hay datos" in texto_recomendacion(ranking.iloc[0:0])


def test_matriz_independencia_cuenta_pares():
    m = pd.DataFrame({"independientes": [True, True, False, True, False, True],
                      "casos": [1000] * 6})
    t = texto_matriz_independencia(m, 0.02)
    assert "4 de 6" in t and "2,0 puntos" in t and ADVERTENCIA not in t
    chico = m.assign(casos=[10, 1000, 1000, 1000, 1000, 1000])
    assert ADVERTENCIA in texto_matriz_independencia(chico, 0.02)


def test_mapa_calor_avisa_celdas_con_pocos_casos():
    m = pd.DataFrame({"totales": [100, 20, 5, 300]})
    t = texto_mapa_calor(m)
    assert "2 de 4 celdas" in t
    assert "menos de 30 casos" in t
    assert "menos de 30" not in texto_mapa_calor(pd.DataFrame({"totales": [100, 300]}))
    assert "No hay datos" in texto_mapa_calor(pd.DataFrame({"totales": []}))


def test_textos_auxiliares_del_tablero():
    assert "30" in texto_poca_muestra()
    assert texto_leyenda_eventos({"lluvia": "A", "viento_fuerte": "B"},
                                 {"lluvia": "lluvia", "viento_fuerte": "viento"}) \
        == "A = lluvia · B = viento"
    t = texto_espacio_muestral(Resultado(0.5, 1500, 3000))
    assert "A: lluvia" in t and "1.500 de 3.000" in t
